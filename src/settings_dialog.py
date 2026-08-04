from typing import Optional
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QGroupBox,
    QLineEdit,
    QFileDialog,
    QMessageBox,
    QProgressBar,
)
from PySide6.QtCore import Qt
from .app_settings import AppSettings
from .ffmpeg_locator import get_ffmpeg_path, clear_stored_ffmpeg_path
from .ffmpeg_downloader import (
    FFmpegDownloadWorker,
    is_download_supported,
    verify_ffmpeg_binary,
)
from pathlib import Path


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Settings"))
        self.setModal(True)
        self.setMinimumSize(420, 450)
        self.resize(480, 520)

        # Current FFmpeg path (resolved at dialog open)
        self._current_ffmpeg_path = get_ffmpeg_path()
        print(f"Current FFmpeg path: {self._current_ffmpeg_path}")

        # Download worker reference
        self._download_worker = None

        # Create layout
        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(30, 20, 30, 20)

        # ── Language selection group ────────────────────────────────
        lang_group = QGroupBox(self.tr("Language"))
        lang_layout = QVBoxLayout()

        self.language_combo = QComboBox()
        self.language_combo.addItem(self.tr("English"), userData="en")
        self.language_combo.addItem(self.tr("Français"), userData="fr")

        # Set current language from settings
        settings = AppSettings()
        current_lang = settings.get_language()
        self.language_combo.setCurrentIndex(1 if current_lang == "fr" else 0)

        lang_layout.addWidget(self.language_combo)
        lang_group.setLayout(lang_layout)
        layout.addWidget(lang_group)

        # ── FFmpeg group ────────────────────────────────────────────
        ffmpeg_group = QGroupBox(self.tr("FFmpeg"))
        ffmpeg_layout = QVBoxLayout()

        # Current detected path label
        self.ffmpeg_status_label = QLabel()
        self._update_ffmpeg_status()
        self.ffmpeg_status_label.setWordWrap(True)
        self.ffmpeg_status_label.setTextFormat(Qt.RichText)
        ffmpeg_layout.addWidget(self.ffmpeg_status_label)

        # Manual override: line edit + browse button
        path_row = QHBoxLayout()
        self.ffmpeg_path_input = QLineEdit()
        self.ffmpeg_path_input.setPlaceholderText(
            self.tr("Leave empty to use auto-detected path")
        )
        if self._current_ffmpeg_path:
            self.ffmpeg_path_input.setText(self._current_ffmpeg_path)
        browse_btn = QPushButton(self.tr("Browse..."))
        browse_btn.clicked.connect(self._browse_ffmpeg)
        path_row.addWidget(self.ffmpeg_path_input, stretch=1)
        path_row.addWidget(browse_btn)
        ffmpeg_layout.addLayout(path_row)

        # Action buttons row
        action_row = QHBoxLayout()

        # Re-run auto-setup (download portable FFmpeg)
        self.ffmpeg_setup_btn = QPushButton(
            self.tr("Download portable FFmpeg") if is_download_supported() else self.tr("Auto-download not available")
        )
        self.ffmpeg_setup_btn.setEnabled(is_download_supported())
        self.ffmpeg_setup_btn.clicked.connect(self._run_ffmpeg_setup)
        action_row.addWidget(self.ffmpeg_setup_btn)

        # Reset stored path
        self.ffmpeg_reset_btn = QPushButton(self.tr("Reset and re-detect"))
        self.ffmpeg_reset_btn.clicked.connect(self._reset_ffmpeg)
        action_row.addWidget(self.ffmpeg_reset_btn)

        ffmpeg_layout.addLayout(action_row)

        # Progress bar (hidden by default)
        self.ffmpeg_progress = QProgressBar()
        self.ffmpeg_progress.setVisible(False)
        self.ffmpeg_progress.setRange(0, 100)
        ffmpeg_layout.addWidget(self.ffmpeg_progress)

        # Log label (hidden by default)
        self.ffmpeg_log_label = QLabel()
        self.ffmpeg_log_label.setVisible(False)
        self.ffmpeg_log_label.setWordWrap(True)
        self.ffmpeg_log_label.setStyleSheet("color: gray; font-size: 11px;")
        ffmpeg_layout.addWidget(self.ffmpeg_log_label)

        # ── Licensing / attribution note ───────────────────────────
        license_label = QLabel(
            self.tr(
                "FFmpeg is free and open-source software. "
                "The build provided is under the GPL license. "
                "Visit <a href='https://ffmpeg.org'>ffmpeg.org</a>"
            )
        )
        license_label.setWordWrap(True)
        license_label.setAlignment(Qt.AlignCenter)
        license_label.setTextFormat(Qt.RichText)
        license_label.setOpenExternalLinks(True)
        license_label.setStyleSheet("color: gray; font-size: 10px;")
        ffmpeg_layout.addWidget(license_label)

        ffmpeg_group.setLayout(ffmpeg_layout)
        layout.addWidget(ffmpeg_group)

        layout.addStretch()

        # ── Save / Cancel buttons ───────────────────────────────────
        button_layout = QHBoxLayout()

        save_button = QPushButton(self.tr("Save"))
        save_button.setDefault(True)
        save_button.clicked.connect(self.save_settings)

        cancel_button = QPushButton(self.tr("Cancel"))
        cancel_button.clicked.connect(self.reject)

        button_layout.addStretch()
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)
    
    # ── FFmpeg status ───────────────────────────────────────────────

    def _update_ffmpeg_status(self, path: Optional[str] = None) -> None:
        """Update the status label with current FFmpeg info."""
        if path is None:
            path = get_ffmpeg_path()
        if path:
            styled_path = '<span style="background-color: #333333; color: #cccccc; font-style: italic;">{path}</span>'.format(path=path)
            self.ffmpeg_status_label.setText(
                self.tr("FFmpeg found at:<br/>") + styled_path
            )
        else:
            self.ffmpeg_status_label.setText(
                self.tr("FFmpeg not found.\nUse the button below to install it.")
            )

    def _sync_ffmpeg_ui(self) -> None:
        """Re-detect FFmpeg path and sync all related UI elements."""
        self._current_ffmpeg_path = get_ffmpeg_path()
        self._update_ffmpeg_status(self._current_ffmpeg_path)
        if self._current_ffmpeg_path:
            self.ffmpeg_path_input.setText(self._current_ffmpeg_path)
        else:
            self.ffmpeg_path_input.clear()

    # ── FFmpeg actions ──────────────────────────────────────────────

    def _browse_ffmpeg(self) -> None:
        """Open a file dialog to let the user pick an FFmpeg binary."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            self.tr("Select FFmpeg executable"),
            "",
            self.tr("Executables") + " (*.exe);;All Files (*)",
        )
        if path:
            self.ffmpeg_path_input.setText(path)

    def _reset_ffmpeg(self) -> None:
        """Clear stored path and force re-detection."""
        clear_stored_ffmpeg_path()
        self._sync_ffmpeg_ui()

    def _run_ffmpeg_setup(self) -> None:
        """Start the portable FFmpeg download in a background thread."""
        # Disable controls during download
        self.ffmpeg_setup_btn.setEnabled(False)
        self.ffmpeg_reset_btn.setEnabled(False)
        self.ffmpeg_progress.setVisible(True)
        self.ffmpeg_log_label.setVisible(True)
        self.ffmpeg_progress.setValue(0)

        self._download_worker = FFmpegDownloadWorker()
        self._download_worker.progress.connect(self.ffmpeg_progress.setValue)
        self._download_worker.log.connect(self._on_download_log)
        self._download_worker.finished.connect(self._on_download_finished)
        self._download_worker.start()

    def _on_download_log(self, message: str) -> None:
        self.ffmpeg_log_label.setText(message)

    def _on_download_finished(self, success: bool, message: str) -> None:
        # Re-enable controls
        self.ffmpeg_setup_btn.setEnabled(True)
        self.ffmpeg_reset_btn.setEnabled(True)
        self.ffmpeg_progress.setVisible(False)
        self.ffmpeg_log_label.setVisible(False)

        if success:
            QMessageBox.information(self, self.tr("Success"), message)
            self._sync_ffmpeg_ui()
        else:
            QMessageBox.warning(self, self.tr("Failed"), message)

    # ── Save ────────────────────────────────────────────────────────

    def save_settings(self) -> None:
        settings = AppSettings()

        # Save language (userData stores the language code directly)
        lang_code = self.language_combo.currentData()  # type: ignore[union-attr]
        current_lang = settings.get_language()
        settings.set_language(lang_code)

        # Save manual FFmpeg override if provided and different
        manual_path = self.ffmpeg_path_input.text().strip()
        if manual_path:
            binary = Path(manual_path)
            if binary.is_file():
                settings.set_ffmpeg_path(manual_path)
            else:
                QMessageBox.warning(
                    self,
                    self.tr("Invalid path"),
                    self.tr("The specified FFmpeg path does not exist."),
                )
                return

        # Show restart message if language changed
        if lang_code != current_lang:
            QMessageBox.information(
                self,
                self.tr("Restart Required"),
                self.tr("Please restart the application for the language change to take effect."),
            )

        self.accept()

    # ── Lifecycle ───────────────────────────────────────────────────

    def closeEvent(self, event: QCloseEvent) -> None:
        """Ensure background worker is cleaned up if dialog closes during download."""
        if self._download_worker and self._download_worker.isRunning():
            self._download_worker.terminate()
            self._download_worker.wait()
        super().closeEvent(event)
