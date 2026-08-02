import sys
from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QGroupBox, QFrame, QStackedWidget, QProgressBar, QFileDialog
)
from PySide6.QtCore import Qt
from .app_settings import AppSettings
from .ffmpeg_locator import get_ffmpeg_path
from .ffmpeg_downloader import FFmpegDownloadWorker, is_download_supported


class OnboardingDialog(QDialog):
    """Multi-step onboarding: language selection, then optional FFmpeg setup."""

    # Step indices
    STEP_LANGUAGE = 0
    STEP_FFMPEG = 1

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Welcome to SIS2VD"))
        self.setModal(True)
        self.setFixedSize(500, 400)

        # Determine whether FFmpeg is already available
        self._ffmpeg_available = get_ffmpeg_path() is not None

        # ── Stacked widget for steps ───────────────────────────────
        self.stacked = QStackedWidget()
        self.stacked.addWidget(self._build_language_page())
        # FFmpeg page is added only when FFmpeg is genuinely missing
        if not self._ffmpeg_available:
            self.stacked.addWidget(self._build_ffmpeg_page())

        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(30, 20, 30, 20)
        main_layout.addWidget(self.stacked)
        self.setLayout(main_layout)

    # ── Page builders ──────────────────────────────────────────────

    def _build_language_page(self) -> QFrame:
        """Step 1 — Language selection."""
        page = QFrame()
        layout = QVBoxLayout()
        layout.setSpacing(15)

        welcome_label = QLabel(
            self.tr("Welcome to SIS2VD – Sny's Image Sequence to Video Converter")
        )
        welcome_label.setAlignment(Qt.AlignCenter)
        welcome_label.setWordWrap(True)
        layout.addWidget(welcome_label)

        lang_group = QGroupBox(self.tr("Select Language"))
        lang_layout = QVBoxLayout()
        self.language_combo = QComboBox()
        self.language_combo.addItems([self.tr("English"), self.tr("Français")])
        self.language_combo.setCurrentText(self.tr("English"))
        lang_layout.addWidget(self.language_combo)
        lang_group.setLayout(lang_layout)
        layout.addWidget(lang_group)

        layout.addStretch()

        # Buttons
        button_layout = QHBoxLayout()
        self._lang_continue_btn = QPushButton(self.tr("Continue"))
        self._lang_continue_btn.setDefault(True)
        self._lang_continue_btn.clicked.connect(self._on_language_continue)
        button_layout.addStretch()
        button_layout.addWidget(self._lang_continue_btn)
        layout.addLayout(button_layout)

        page.setLayout(layout)
        return page

    def _build_ffmpeg_page(self) -> QFrame:
        """Step 2 — FFmpeg not found; offer download or manual path."""
        page = QFrame()
        layout = QVBoxLayout()
        layout.setSpacing(15)

        title = QLabel(self.tr("FFmpeg is required"))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)

        info_text = QLabel(
            self.tr(
                "SIS2VD needs FFmpeg to encode videos.\n"
                "You can download it automatically, or point us to an "
                "existing installation."
            )
        )
        info_text.setWordWrap(True)
        info_text.setAlignment(Qt.AlignCenter)
        layout.addWidget(info_text)

        # Primary action — auto download
        self._download_btn = QPushButton(
            self.tr("Download FFmpeg automatically")
        )
        self._download_btn.setDefault(True)
        self._download_btn.clicked.connect(self._on_download_ffmpeg)
        layout.addWidget(self._download_btn)

        # Progress (hidden until download starts)
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._progress_bar.setVisible(False)
        layout.addWidget(self._progress_bar)

        self._status_label = QLabel()
        self._status_label.setWordWrap(True)
        self._status_label.setAlignment(Qt.AlignCenter)
        self._status_label.setVisible(False)
        layout.addWidget(self._status_label)

        layout.addSpacing(10)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFrameShadow(QFrame.Sunken)
        layout.addWidget(sep)

        # Secondary action — manual browse
        manual_layout = QHBoxLayout()
        self._manual_btn = QPushButton(
            self.tr("I already have FFmpeg, specify path manually")
        )
        self._manual_btn.clicked.connect(self._on_manual_ffmpeg)
        manual_layout.addWidget(self._manual_btn)
        layout.addLayout(manual_layout)

        page.setLayout(layout)
        return page

    # ── Slot: language continue ────────────────────────────────────

    def _on_language_continue(self):
        """Save language and advance to next step (or finish)."""
        settings = AppSettings()
        lang_code = "en" if self.language_combo.currentText() == "English" else "fr"
        settings.set_language(lang_code)

        if self._ffmpeg_available:
            # FFmpeg already in PATH — skip setup, finish onboarding
            settings.set_onboarding_completed(True)
            self.accept()
        else:
            # Show the FFmpeg setup page
            self.stacked.setCurrentIndex(self.STEP_FFMPEG)

    # ── Slot: auto-download FFmpeg ────────────────────────────────

    def _on_download_ffmpeg(self):
        """Start background download of portable FFmpeg."""
        self._download_btn.setEnabled(False)
        self._manual_btn.setEnabled(False)
        self._progress_bar.setVisible(True)
        self._status_label.setVisible(True)
        self._status_label.setText(self.tr("Downloading FFmpeg … please wait."))

        self._downloader = FFmpegDownloadWorker()
        self._downloader.progress.connect(self._progress_bar.setValue)
        self._downloader.log.connect(self._status_label.setText)
        self._downloader.finished.connect(self._on_download_finished)
        self._downloader.start()

    def _on_download_finished(self, success: bool, message: str):
        """Handle completion of FFmpeg download."""
        self._progress_bar.setVisible(False)
        self._status_label.setText(message)

        if success and get_ffmpeg_path() is not None:
            # Successfully installed — mark onboarding done and close
            settings = AppSettings()
            settings.set_onboarding_completed(True)
            self.accept()
        else:
            # Download failed — re-enable buttons so user can retry
            self._download_btn.setEnabled(True)
            self._manual_btn.setEnabled(True)

    # ── Slot: manual FFmpeg path ──────────────────────────────────

    def _on_manual_ffmpeg(self):
        """Let the user browse for an existing FFmpeg executable."""
        binary_filter = "Executables (*.exe)" if sys.platform == "win32" else "All Files (*)"
        path_str, _ = QFileDialog.getOpenFileName(
            self,
            self.tr("Locate FFmpeg executable"),
            "",
            binary_filter,
        )

        if not path_str:
            return  # User cancelled

        candidate = Path(path_str)
        if not candidate.is_file():
            self._status_label.setVisible(True)
            self._status_label.setText(
                self.tr("Selected file does not exist or is not a valid executable.")
            )
            return

        # Basic smoke-test: try running --version
        import subprocess
        try:
            result = subprocess.run(
                [str(candidate), "--version"],
                capture_output=True, timeout=10
            )
            if result.returncode == 0 and b"ffmpeg" in result.stdout.lower():
                # It's a valid FFmpeg binary — place it where the locator expects
                from .ffmpeg_locator import _ffmpeg_data_dir, _FFMPEG_BINARY_NAME
                target = _ffmpeg_data_dir()
                target.mkdir(parents=True, exist_ok=True)
                import shutil
                dest_binary = target / _FFMPEG_BINARY_NAME
                shutil.copy2(str(candidate), str(dest_binary))
                if sys.platform != "win32":
                    dest_binary.chmod(0o755)

                settings = AppSettings()
                settings.set_onboarding_completed(True)
                self._status_label.setText(
                    self.tr("FFmpeg located and registered successfully.")
                )
                self.accept()
            else:
                self._status_label.setVisible(True)
                self._status_label.setText(
                    self.tr("The selected file does not appear to be FFmpeg.")
                )
        except (subprocess.TimeoutExpired, OSError):
            self._status_label.setVisible(True)
            self._status_label.setText(
                self.tr("Could not verify the selected file as FFmpeg.")
            )