"""
FFmpeg Downloader - Downloads, extracts, and verifies a portable FFmpeg binary.

Responsibilities:
  - Detect OS and architecture (Windows x64, Linux x64/amd64, Linux arm64)
  - Download the appropriate static FFmpeg build from verified URLs
  - Run download in a QThread (non-blocking UI) with progress signals
  - Extract archive keeping only the ffmpeg executable
  - Set executable bit on Unix
  - Verify the extracted binary via subprocess `ffmpeg -version`
  - Emit clear success/failure signals for UI integration

macOS is intentionally skipped for auto-download since portable builds are
not straightforward. On macOS, the system (Homebrew) FFmpeg is preferred.
"""
import os
import platform
import shutil
import socket
import subprocess
import tarfile
import zipfile
import urllib.request
import urllib.error
from pathlib import Path
from PySide6.QtCore import QStandardPaths, QThread, Signal, QCoreApplication


# ── Platform detection ───────────────────────────────────────────────────

_SYSTEM = platform.system()
_ARCH = platform.machine().lower()


def _is_windows_x64() -> bool:
    return _SYSTEM == "Windows" and ("amd64" in _ARCH or "x86_64" in _ARCH)


def _is_linux_amd64() -> bool:
    return _SYSTEM == "Linux" and ("amd64" in _ARCH or "x86_64" in _ARCH)


def _is_linux_arm64() -> bool:
    return _SYSTEM == "Linux" and ("aarch64" in _ARCH or "arm" in _ARCH)


# ── Download URLs (verified working) ─────────────────────────────────────

_FFMPEG_DIR_NAME = "ffmpeg"

# Binary name per platform
if _SYSTEM == "Windows":
    FFMPEG_BINARY_NAME = "ffmpeg.exe"
else:
    FFMPEG_BINARY_NAME = "ffmpeg"


def get_download_url() -> str | None:
    """
    Return the download URL for the current OS/arch, or None if unsupported.

    Supported:
      - Windows x64  -> BtbN/FFmpeg-Builds (latest stable zip)
      - Linux amd64  -> johnvansickle.com static tar.xz
      - Linux arm64  -> johnvansickle.com static tar.xz

    macOS is not supported for auto-download.
    """
    if _is_windows_x64():
        return (
            "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/"
            "ffmpeg-master-latest-win64-gpl.zip"
        )

    if _is_linux_amd64():
        return (
            "https://johnvansickle.com/ffmpeg/releases/"
            "ffmpeg-release-amd64-static.tar.xz"
        )

    if _is_linux_arm64():
        return (
            "https://johnvansickle.com/ffmpeg/releases/"
            "ffmpeg-release-arm64-static.tar.xz"
        )

    # macOS or unsupported architecture
    return None


def is_download_supported() -> bool:
    """Return True if auto-download is supported on the current platform."""
    return get_download_url() is not None


# ── Path helpers ─────────────────────────────────────────────────────────

def app_data_path() -> Path:
    """Return the application data directory (same as AppSettings)."""
    return Path(QStandardPaths.writableLocation(QStandardPaths.AppDataLocation))


def ffmpeg_data_dir() -> Path:
    """
    Return the full path where the portable FFmpeg binary is stored.

    Structure:  <AppData>/<app>/ffmpeg/
    """
    return app_data_path() / _FFMPEG_DIR_NAME


# ── Binary verification ────────────────────────────────────────────────

def verify_ffmpeg_binary(binary_path: Path) -> bool:
    """
    Verify that a binary is a valid FFmpeg executable by running `ffmpeg -version`.

    Returns True if the command succeeds and output contains 'ffmpeg'.
    """
    try:
        result = subprocess.run(
            [str(binary_path), "-version"],
            capture_output=True,
            timeout=15,
        )
        if result.returncode != 0:
            return False
        return b"ffmpeg" in result.stdout.lower()
    except (subprocess.TimeoutExpired, OSError, FileNotFoundError):
        return False


# ── Extraction helpers ──────────────────────────────────────────────────

def _extract_windows_zip(archive_path: Path, dest_dir: Path) -> Path | None:
    """
    Extract a Windows FFmpeg zip archive, keeping only ffmpeg.exe.

    Returns the path to the extracted binary, or None on failure.
    """
    binary_path = dest_dir / FFMPEG_BINARY_NAME

    try:
        with zipfile.ZipFile(archive_path) as zf:
            # Find ffmpeg.exe inside the archive (structure varies by build)
            names = [
                n for n in zf.namelist()
                if n.endswith(f"/{FFMPEG_BINARY_NAME}") or n == FFMPEG_BINARY_NAME
            ]
            if not names:
                raise FileNotFoundError(
                    f"'{FFMPEG_BINARY_NAME}' not found inside archive."
                )

            # Extract only the binary member(s)
            target = dest_dir / FFMPEG_BINARY_NAME
            zf.extract(names[0], dest_dir)

        # The extracted file may be nested; find and flatten it
        extracted = next(dest_dir.rglob(FFMPEG_BINARY_NAME), None)
        if extracted and extracted != target:
            shutil.move(str(extracted), str(target))
            # Clean up any empty nested directories created by extract
            for subdir in dest_dir.iterdir():
                if subdir.is_dir() and subdir != Path(dest_dir):
                    shutil.rmtree(subdir, ignore_errors=True)

        return target
    except (zipfile.BadZipFile, KeyError, RuntimeError) as exc:
        raise FileNotFoundError(f"Failed to extract archive: {exc}") from exc


def _extract_linux_tarxz(archive_path: Path, dest_dir: Path) -> Path | None:
    """
    Extract a Linux FFmpeg tar.xz archive, keeping only the ffmpeg binary.

    Returns the path to the extracted binary, or None on failure.
    """
    binary_path = dest_dir / FFMPEG_BINARY_NAME

    try:
        with tarfile.open(archive_path) as tf:
            # Find the ffmpeg binary member
            members = [
                m for m in tf.getmembers()
                if m.name.endswith(f"/{FFMPEG_BINARY_NAME}") and m.isfile()
            ]
            if not members:
                raise FileNotFoundError(
                    f"'{FFMPEG_BINARY_NAME}' not found inside archive."
                )

            # Extract just the binary, flattening the path
            member = members[0]
            member.name = FFMPEG_BINARY_NAME
            tf.extract(member, dest_dir)

        return binary_path
    except (tarfile.TarError, KeyError) as exc:
        raise FileNotFoundError(f"Failed to extract archive: {exc}") from exc


# ── Download helper ─────────────────────────────────────────────────────

def _check_disk_space(path: Path, required_bytes: int) -> bool:
    """
    Check if there is enough disk space for the download.

    Returns True if sufficient space is available.
    """
    try:
        usage = shutil.disk_usage(str(path.parent))
        return usage.free >= required_bytes
    except (OSError, AttributeError):
        # disk_usage not available on some platforms; skip check
        return True


def _tr_ffmpeg(text: str) -> str:
    """Helper to translate strings from outside a QWidget/QThread context."""
    return QCoreApplication.translate("FFmpegDownloadWorker", text)


def _download_with_progress(
    url: str,
    dest: Path,
    progress_signal,
    log_signal,
    cancelled_flag,
    chunk_size: int = 64 * 1024,
) -> None:
    """
    Stream-download *url* to *dest*, emitting progress and log signals.

    Args:
        url: Download URL.
        dest: Destination file path.
        progress_signal: Signal(int) for 0-100 percentage.
        log_signal: Signal(str) for informational messages.
        cancelled_flag: Dict with key 'cancelled' (mutable reference).
        chunk_size: Read buffer size in bytes.

    Raises:
        NoConnectionError: When no internet connection is available.
        DiskSpaceError: When insufficient disk space for download.
        DownloadError: For other download-related failures.
    """
    log_signal.emit(_tr_ffmpeg("Connecting to download source..."))

    # Handle URL exceptions with specific messages
    try:
        response = urllib.request.urlopen(url, timeout=60)
    except urllib.error.URLError as exc:
        # Reason is an underlying exception (e.g., socket.gaierror, ConnectionRefusedError)
        reason = exc.reason
        if isinstance(reason, (socket.gaierror, ConnectionRefusedError, ConnectionResetError)):
            raise _NoConnectionError(
                _tr_ffmpeg("Cannot connect to download server. Please check your internet connection.")
            ) from exc
        # Generic URLError fallback
        raise _DownloadError(_tr_ffmpeg("Failed to connect to download server: {}").format(reason)) from exc
    except socket.timeout:
        raise _NoConnectionError(
            _tr_ffmpeg("Connection timed out. Please check your internet connection and try again.")
        )
    except urllib.error.HTTPError as exc:
        raise _DownloadError(
            _tr_ffmpeg("Server returned HTTP {}. The download URL may be unavailable.").format(exc.code)
        ) from exc

    total = int(response.headers.get("Content-Length", 0))

    # Check disk space if content-length is known and substantial (>50MB typical ffmpeg)
    if total > 1024 * 1024:
        if not _check_disk_space(dest, total + (10 * 1024 * 1024)):  # +10MB buffer for extraction
            raise _DiskSpaceError(
                _tr_ffmpeg("Insufficient disk space. Need ~{} MB, but less free space is available on the drive.").format(total / (1024*1024))
            )

    downloaded = 0

    try:
        with open(dest, "wb") as f:
            while True:
                if cancelled_flag.get("cancelled", False):
                    f.close()
                    dest.unlink(missing_ok=True)
                    log_signal.emit(_tr_ffmpeg("Download cancelled."))
                    return

                chunk = response.read(chunk_size)
                if not chunk:
                    break

                try:
                    f.write(chunk)
                except OSError as exc:
                    if exc.errno == 28:  # ENOSPC
                        raise _DiskSpaceError(
                            _tr_ffmpeg("Disk full during download. Please free up space and try again.")
                        ) from exc
                    raise

                downloaded += len(chunk)

                if total > 0:
                    pct = int((downloaded / total) * 100)
                    progress_signal.emit(pct)
    except (_DiskSpaceError, _NoConnectionError, _DownloadError):
        # Clean up partial download on known errors
        dest.unlink(missing_ok=True)
        raise
    except OSError as exc:
        dest.unlink(missing_ok=True)
        raise _DownloadError(_tr_ffmpeg("Failed to write download file: {}").format(exc)) from exc

    log_signal.emit(_tr_ffmpeg("Download complete ({} MB).").format(downloaded / (1024 * 1024)))


# ── Custom error types for UI handling ──────────────────────────────────

class NoConnectionError(Exception):
    """Raised when no internet connection is available."""
    pass


class DiskSpaceError(Exception):
    """Raised when disk space is insufficient."""
    pass


class DownloadError(Exception):
    """Raised for other download-related failures."""
    pass


# Backward-compatible aliases (used in pipeline)
_NoConnectionError = NoConnectionError
_DiskSpaceError = DiskSpaceError
_DownloadError = DownloadError


# ── Main download worker (QThread) ─────────────────────────────────────

class FFmpegDownloadWorker(QThread):
    """
    Background thread to download, extract, and verify a portable FFmpeg binary.

    Signals:
        progress(int)   : 0-100 download percentage
        log(str)        : informational / error messages
        finished(bool, str) : (success, message) — emitted when done
    """

    progress = Signal(int)
    log = Signal(str)
    finished = Signal(bool, str)

    def __init__(self) -> None:
        super().__init__()
        self._cancelled = {"cancelled": False}

    # ── public API ────────────────────────────────────────────────────

    def cancel(self) -> None:
        """Request the download to stop."""
        self._cancelled["cancelled"] = True

    # ── translation helper ───────────────────────────────────────────

    def _tr(self, text: str) -> str:
        """Translate a string using QCoreApplication.translate (for use in QThread)."""
        return QCoreApplication.translate("FFmpegDownloadWorker", text)

    def run(self) -> None:
        """Execute the full download -> extract -> verify pipeline."""
        dest_dir = ffmpeg_data_dir()
        binary_path = dest_dir / FFMPEG_BINARY_NAME

        # Check if already installed
        if binary_path.is_file() and verify_ffmpeg_binary(binary_path):
            self.finished.emit(True, self._tr("Portable FFmpeg already present and verified."))
            return

        # Verify download is supported on this platform
        url = get_download_url()
        if url is None:
            self.finished.emit(
                False,
                self._tr(
                    "Auto-download not supported on this platform. "
                    "Please specify FFmpeg path manually."
                ),
            )
            return

        dest_dir.mkdir(parents=True, exist_ok=True)

        try:
            self._execute_pipeline(dest_dir, url)
        except NoConnectionError as exc:
            self._cleanup_partial(binary_path, dest_dir)
            self.finished.emit(
                False,
                self._tr("No internet connection: {}. Please check your connection or specify FFmpeg path manually.").format(str(exc)),
            )
        except DiskSpaceError as exc:
            self._cleanup_partial(binary_path, dest_dir)
            self.finished.emit(False, str(exc))
        except PermissionError as exc:
            self._cleanup_partial(binary_path, dest_dir)
            self.finished.emit(
                False,
                self._tr("Permission denied (antivirus/firewall may be blocking): {}. Please add an exception or specify FFmpeg path manually.").format(str(exc)),
            )
        except subprocess.SubprocessError as exc:
            self._cleanup_partial(binary_path, dest_dir)
            self.finished.emit(
                False,
                self._tr("FFmpeg process error (antivirus/firewall may be blocking execution): {}. Please check your security software or specify path manually.").format(str(exc)),
            )
        except DownloadError as exc:
            self._cleanup_partial(binary_path, dest_dir)
            self.finished.emit(False, str(exc))
        except Exception as exc:
            self._cleanup_partial(binary_path, dest_dir)
            self.finished.emit(False, self._tr("Setup failed: {}").format(str(exc)))
            return

    def _cleanup_partial(self, binary_path: Path, dest_dir: Path) -> None:
        """Clean up partial download/extraction to avoid corrupt files."""
        # Remove partial binary
        if binary_path.exists():
            try:
                binary_path.unlink()
            except OSError:
                pass  # Best effort cleanup

        # Remove any archive files
        for archive_ext in ("*.zip", "*.tar.xz", "*.tar"):
            for archive in dest_dir.glob(archive_ext):
                try:
                    archive.unlink()
                except OSError:
                    pass

        # Clean up any extracted temp directories (empty ones from failed zip extract)
        for item in dest_dir.iterdir():
            if item.is_dir():
                try:
                    shutil.rmtree(item, ignore_errors=True)
                except OSError:
                    pass

    # ── pipeline steps ────────────────────────────────────────────────

    def _execute_pipeline(self, dest_dir: Path, url: str) -> None:
        """Orchestrates download -> extract -> chmod -> verify."""
        binary_path = dest_dir / FFMPEG_BINARY_NAME

        # Determine archive filename and type based on platform
        if _is_windows_x64():
            archive_filename = "ffmpeg.zip"
        else:
            archive_filename = "ffmpeg.tar.xz"

        archive_path = dest_dir / archive_filename

        # Step 1: Download
        platform_label = self._tr("Windows") if _SYSTEM == "Windows" else self._tr("Linux")
        self.log.emit(self._tr("Downloading portable FFmpeg for {} ...").format(platform_label))
        self.progress.emit(0)

        _download_with_progress(
            url, archive_path,
            progress_signal=self.progress,
            log_signal=self.log,
            cancelled_flag=self._cancelled,
        )

        if self._cancelled["cancelled"]:
            return

        # Step 2: Extract (only the binary)
        self.log.emit(self._tr("Extracting FFmpeg binary ..."))
        self.progress.emit(90)

        if _is_windows_x64():
            _extract_windows_zip(archive_path, dest_dir)
        else:
            _extract_linux_tarxz(archive_path, dest_dir)

        # Clean up archive
        archive_path.unlink(missing_ok=True)

        if self._cancelled["cancelled"]:
            return

        # Step 3: Set executable bit on Unix
        if _SYSTEM != "Windows" and binary_path.is_file():
            os.chmod(binary_path, 0o755)

        # Step 4: Verify binary runs correctly
        self.progress.emit(95)
        self.log.emit(self._tr("Verifying FFmpeg binary ..."))

        if not binary_path.is_file():
            self.finished.emit(False, self._tr("Binary not found after extraction."))
            return

        if verify_ffmpeg_binary(binary_path):
            self.progress.emit(100)
            self.finished.emit(
                True, self._tr("Portable FFmpeg installed and verified successfully.")
            )
        else:
            self.finished.emit(
                False,
                self._tr(
                    "FFmpeg binary extracted but verification failed. "
                    "The file may be corrupt. Please retry or specify path manually."
                ),
            )
