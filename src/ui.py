import sys
import os
import shutil
from pathlib import Path
from typing import Optional, Dict, Any
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QPushButton, QLineEdit, QFileDialog,
                               QSpinBox, QSlider, QComboBox, QLabel,
                               QProgressBar, QTextEdit, QMessageBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette, QColor, QDragEnterEvent, QDropEvent, QPixmap
from .sequence_utils import extract_pattern, scan_sequence
from .ffmpeg_worker import FFmpegWorker
from .settings_dialog import SettingsDialog


class MainWindow(QMainWindow):
    """Main application window for SIS2VD."""
    
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(self.tr("SIS2VD - Sny's Image Sequence to Video Converter"))
        self.setMinimumSize(800, 600)
        
        # Worker thread
        self.worker: Optional[FFmpegWorker] = None
        self.current_sequence_info: Optional[Dict[str, Any]] = None
        
        # Drag and drop overlay
        self._setup_drop_overlay()
        
        # Create central widget with vertical layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Add image selection UI
        self._add_image_selection_ui()
        
        # Add settings UI
        self._add_settings_ui()
        
        # Add action buttons and progress UI
        self._add_action_buttons_ui()
        
        # Enable drag and drop
        self.setAcceptDrops(True)
        
        # Check FFmpeg availability
        self._check_ffmpeg_availability()
        
        # Apply dark theme if system prefers it
        self._apply_theme()
    
    def _setup_drop_overlay(self):
        """Setup the drag and drop overlay widget."""
        from PySide6.QtWidgets import QLabel
        from PySide6.QtGui import QPainter, QColor, QImage
        
        # Create overlay widget
        self.drop_overlay = QLabel(self)
        self.drop_overlay.setStyleSheet("""
            background-color: rgba(0, 0, 0, 150);
        """)
        self.drop_overlay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Load and scale the drop icon
        icon_path = Path(__file__).parent.parent / "assets" / "File_drop.png"
        if icon_path.exists():
            pixmap = QPixmap(str(icon_path))
            # Invert the image colors
            image = pixmap.toImage()
            image.invertPixels()
            pixmap = QPixmap.fromImage(image)
            
            # Scale to 50% of window size (using minimum size as reference)
            window_size = self.minimumSize()
            scaled_size = window_size * 0.5
            pixmap = pixmap.scaled(
                scaled_size.width(),
                scaled_size.height(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.drop_overlay.setPixmap(pixmap)
        else:
            self.drop_overlay.setText("Drop image file here")
            self.drop_overlay.setStyleSheet("""
                background-color: rgba(0, 0, 0, 150);
                color: white;
                font-size: 24px;
            """)
        
        # Initially hidden
        self.drop_overlay.hide()
    
    def _show_drop_overlay(self):
        """Show the drop overlay covering the entire window."""
        self.drop_overlay.setGeometry(0, 0, self.width(), self.height())
        self.drop_overlay.raise_()
        self.drop_overlay.show()
    
    def _hide_drop_overlay(self):
        """Hide the drop overlay."""
        self.drop_overlay.hide()
    
    def _apply_theme(self) -> None:
        """Apply dark theme based on system preferences."""
        # On Linux, PySide6 typically respects system theme automatically
        # On Windows, we may need to use Fusion style for better dark theme support
        if sys.platform == "win32":
            # Use Fusion style which works well with custom palettes
            from PySide6.QtWidgets import QApplication
            QApplication.setStyle("Fusion")
            
            # Check if system prefers dark mode (Windows 10/11)
            # This is a simplified check - for production, use Windows API
            import os
            if os.getenv("FORCE_DARK_THEME") == "1":
                self._set_dark_palette()
    
    def _set_dark_palette(self) -> None:
        """Set dark color palette for the application."""
        from PySide6.QtWidgets import QApplication
        palette = QPalette()
        
        # Define dark theme colors
        palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
        
        QApplication.instance().setPalette(palette)
    
    def _check_ffmpeg_availability(self) -> None:
        """Check if FFmpeg is available in the system PATH."""
        ffmpeg_path = shutil.which('ffmpeg')
        
        if not ffmpeg_path:
            # FFmpeg not found - show error and disable generate button
            QMessageBox.critical(
                self,
                "FFmpeg not found",
                "FFmpeg is not installed or is not in the PATH.\n\n"
                "Please install FFmpeg and add it to your system PATH.\n"
                "Without FFmpeg, this application cannot function."
            )
            self.generate_button.setEnabled(False)
            self.generate_button.setToolTip("FFmpeg not available")
            self.log_text_edit.append("ERROR: FFmpeg not found in the system.")
        else:
            # FFmpeg found - log the version
            self.log_text_edit.append(f"FFmpeg detected: {ffmpeg_path}")
    
    def _add_image_selection_ui(self) -> None:
        """Add image selection UI components."""
        # Create horizontal layout for image selection
        image_layout = QHBoxLayout()
        
        # Label
        from PySide6.QtWidgets import QLabel
        image_label = QLabel(self.tr("Image sequence:"))
        image_layout.addWidget(image_label)
        
        # QLineEdit to display selected image path
        self.image_path_edit = QLineEdit()
        self.image_path_edit.setPlaceholderText(self.tr("Select an image from the sequence..."))
        self.image_path_edit.setReadOnly(True)
        image_layout.addWidget(self.image_path_edit)
        
        # "Parcourir" button
        browse_button = QPushButton(self.tr("Browse"))
        browse_button.clicked.connect(self._browse_image_file)
        image_layout.addWidget(browse_button)
        
        # Add the horizontal layout to the main vertical layout
        self.layout.addLayout(image_layout)
    
    def _browse_image_file(self) -> None:
        """Open file dialog to select an image file."""
        # Define file filter for image files
        file_filter = "Image Files (*.png *.jpg *.jpeg *.tiff *.exr);;All Files (*)"
        
        # Open file dialog
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select an image from the sequence",
            "",
            file_filter
        )
        
        # Update QLineEdit if a file was selected
        if file_path:
            self.image_path_edit.setText(file_path)
            self._detect_sequence(file_path)
    
    def _detect_sequence(self, file_path: str) -> None:
        """Detect sequence pattern and update UI with sequence info."""
        # Extract pattern from filename
        pattern_info = extract_pattern(file_path)
        
        if not pattern_info:
            self.sequence_info_label.setText(self.tr("Pattern not detected"))
            self.sequence_info_label.setStyleSheet("color: red; font-style: italic;")
            self.current_sequence_info = None
            return
        
        # Scan directory for sequence files
        directory = Path(file_path).parent
        sequence_info = scan_sequence(directory, pattern_info)
        
        if not sequence_info:
            self.sequence_info_label.setText(self.tr("No sequence files found"))
            self.sequence_info_label.setStyleSheet("color: red; font-style: italic;")
            self.current_sequence_info = None
            return
        
        # Store sequence info for encoding
        self.current_sequence_info = {
            'pattern_info': pattern_info,
            'sequence_info': sequence_info,
            'directory': directory
        }
        
        # Update sequence info label
        total_count = sequence_info['total_count']
        start_num = sequence_info['start_number']
        end_num = sequence_info['end_number']
        gaps = sequence_info['gaps']
        
        if gaps:
            gap_info = f", {len(gaps)} trou(s)"
            self.sequence_info_label.setStyleSheet("color: orange; font-style: italic;")
        else:
            gap_info = ""
            self.sequence_info_label.setStyleSheet("color: green; font-style: normal;")
        
        info_text = f"Séquence: {total_count} images ({start_num}-{end_num}){gap_info}"
        self.sequence_info_label.setText(info_text)
        
        # Set default output path based on sequence location
        self._set_default_output_path(directory, pattern_info['prefix'])
    
    def _set_default_output_path(self, directory: Path, prefix: str) -> None:
        """Set default output path based on sequence location."""
        # Create output filename from prefix
        output_name = f"{prefix}video.mp4"
        output_path = directory / output_name
        self.output_path_edit.setText(str(output_path))
    
    def _add_settings_ui(self) -> None:
        """Add settings UI components."""
        # Framerate setting
        framerate_layout = QHBoxLayout()
        framerate_label = QLabel(self.tr("Framerate (fps):"))
        framerate_layout.addWidget(framerate_label)
        
        self.framerate_spinbox = QSpinBox()
        self.framerate_spinbox.setRange(1, 120)
        self.framerate_spinbox.setValue(30)
        framerate_layout.addWidget(self.framerate_spinbox)
        framerate_layout.addStretch()
        
        self.layout.addLayout(framerate_layout)
        
        # CRF (Constant Rate Factor) setting
        crf_layout = QHBoxLayout()
        crf_label = QLabel(self.tr("CRF (Quality):"))
        crf_label.setToolTip(
            self.tr("CRF (Constant Rate Factor): x264 quality scale\n"
            "0 = lossless, 18 = high quality (default), 23 = ffmpeg default,\n"
            "28 = good quality, 51 = worst quality. Lower values = better quality.")
        )
        crf_layout.addWidget(crf_label)
        
        self.crf_slider = QSlider(Qt.Orientation.Horizontal)
        self.crf_slider.setRange(0, 51)
        self.crf_slider.setValue(18)
        self.crf_label_value = QLabel("18")
        self.crf_slider.valueChanged.connect(
            lambda v: self.crf_label_value.setText(str(v))
        )
        crf_layout.addWidget(self.crf_slider)
        crf_layout.addWidget(self.crf_label_value)
        crf_layout.addStretch()
        
        self.layout.addLayout(crf_layout)
        
        # x264 Preset setting
        preset_layout = QHBoxLayout()
        preset_label = QLabel(self.tr("x264 Preset:"))
        preset_layout.addWidget(preset_label)
        
        self.preset_combobox = QComboBox()
        presets = [
            "ultrafast", "superfast", "veryfast", "faster", "fast",
            "medium", "slow", "slower", "veryslow"
        ]
        self.preset_combobox.addItems(presets)
        self.preset_combobox.setCurrentText("medium")
        preset_layout.addWidget(self.preset_combobox)
        preset_layout.addStretch()
        
        self.layout.addLayout(preset_layout)
        
        # Output path setting
        output_layout = QHBoxLayout()
        output_label = QLabel(self.tr("Output file:"))
        output_layout.addWidget(output_label)
        
        self.output_path_edit = QLineEdit()
        self.output_path_edit.setPlaceholderText(self.tr("Select output file..."))
        output_layout.addWidget(self.output_path_edit)
        
        output_browse_button = QPushButton(self.tr("Browse"))
        output_browse_button.clicked.connect(self._browse_outputFile)
        output_layout.addWidget(output_browse_button)
        
        self.layout.addLayout(output_layout)
    
    def _browse_outputFile(self) -> None:
        """Open file dialog to select output file."""
        file_filter = "MP4 Files (*.mp4);;All Files (*)"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Select output file",
            "",
            file_filter
        )
        
        if file_path:
            # Ensure .mp4 extension
            if not file_path.lower().endswith('.mp4'):
                file_path += '.mp4'
            self.output_path_edit.setText(file_path)
    
    def _add_action_buttons_ui(self) -> None:
        """Add action buttons and progress UI components."""
        # Sequence info label
        self.sequence_info_label = QLabel(self.tr("Sequence not detected"))
        self.sequence_info_label.setStyleSheet("color: gray; font-style: italic;")
        self.layout.addWidget(self.sequence_info_label)
        
        # Progress bar (initially hidden)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.layout.addWidget(self.progress_bar)
        
        # Action buttons layout
        buttons_layout = QHBoxLayout()
        
        # "Générer la vidéo" button
        self.generate_button = QPushButton(self.tr("Generate video"))
        self.generate_button.clicked.connect(self._start_encoding)
        buttons_layout.addWidget(self.generate_button)
        
        # "Annuler" button (initially disabled)
        self.cancel_button = QPushButton(self.tr("Cancel"))
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self._cancel_encoding)
        buttons_layout.addWidget(self.cancel_button)
        
        # Settings button with gear emoji
        settings_button = QPushButton(self.tr("⚙️"))
        settings_button.setToolTip(self.tr("Settings"))
        settings_button.clicked.connect(self._open_settings)
        buttons_layout.addWidget(settings_button)
        
        buttons_layout.addStretch()
        
        self.layout.addLayout(buttons_layout)
        
        # FFmpeg logs text edit (read-only, scrollable)
        self.log_text_edit = QTextEdit()
        self.log_text_edit.setReadOnly(True)
        self.log_text_edit.setMaximumHeight(150)
        self.log_text_edit.setPlaceholderText(self.tr("FFmpeg logs will appear here..."))
        self.layout.addWidget(self.log_text_edit)
    
    def _start_encoding(self) -> None:
        """Start the FFmpeg encoding process."""
        # Validate inputs
        if not self.current_sequence_info:
            QMessageBox.warning(self, "No sequence", "Please select a sequence image first.")
            return
        
        output_path = self.output_path_edit.text()
        if not output_path:
            QMessageBox.warning(self, "No output", "Please specify an output file.")
            return
        
        # Validate output path directory is writable
        output_file = Path(output_path)
        try:
            output_dir = output_file.parent
            if not output_dir.exists():
                QMessageBox.warning(self, "Directory does not exist", f"Output directory does not exist: {output_dir}")
                return
            if not os.access(output_dir, os.W_OK):
                QMessageBox.warning(self, "Permission denied", f"No write access for: {output_dir}")
                return
        except Exception as e:
            QMessageBox.warning(self, "Validation error", f"Error validating path: {str(e)}")
            return
        
        # Get parameters
        pattern_info = self.current_sequence_info['pattern_info']
        sequence_info = self.current_sequence_info['sequence_info']
        
        start_number = pattern_info['start_number']
        input_pattern = pattern_info['pattern']
        total_frames = sequence_info['total_count']
        framerate = self.framerate_spinbox.value()
        crf = self.crf_slider.value()
        preset = self.preset_combobox.currentText()
        
        # Validate parameter ranges
        if framerate < 1 or framerate > 120:
            QMessageBox.warning(self, "Invalid parameter", "Framerate must be between 1 and 120.")
            return
        if crf < 0 or crf > 51:
            QMessageBox.warning(self, "Invalid parameter", "CRF must be between 0 and 51.")
            return
        
        # Create and configure worker
        self.worker = FFmpegWorker()
        self.worker.set_parameters(
            start_number=start_number,
            framerate=framerate,
            input_pattern=input_pattern,
            input_directory=self.current_sequence_info['directory'],
            crf=crf,
            preset=preset,
            output_path=Path(output_path),
            total_frames=total_frames
        )
        
        # Connect signals
        self.worker.progress_updated.connect(self._on_progress_updated)
        self.worker.log_output.connect(self._on_log_output)
        self.worker.finished.connect(self._on_encoding_finished)
        
        # Disable controls during encoding
        self._set_encoding_state(True)
        
        # Show progress bar
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Start worker
        self.worker.start()
    
    def _cancel_encoding(self) -> None:
        """Cancel the ongoing encoding process."""
        if self.worker:
            self.worker.cancel()
    
    def _on_progress_updated(self, percentage: int) -> None:
        """Handle progress updates from worker."""
        self.progress_bar.setValue(percentage)
    
    def _on_log_output(self, log_line: str) -> None:
        """Handle log output from worker."""
        self.log_text_edit.append(log_line)
        # Auto-scroll to bottom
        scrollbar = self.log_text_edit.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def _on_encoding_finished(self, success: bool, message: str) -> None:
        """Handle encoding completion."""
        # Re-enable controls
        self._set_encoding_state(False)
        
        # Show completion message
        if success:
            QMessageBox.information(self, "Success", message)
        else:
            QMessageBox.warning(self, "Error", message)
        
        # Hide progress bar after a delay
        self.progress_bar.setVisible(False)
        
        # Clear worker reference
        self.worker = None
    
    def _set_encoding_state(self, encoding: bool) -> None:
        """Enable/disable controls based on encoding state."""
        self.generate_button.setEnabled(not encoding)
        self.cancel_button.setEnabled(encoding)
        self.framerate_spinbox.setEnabled(not encoding)
        self.crf_slider.setEnabled(not encoding)
        self.preset_combobox.setEnabled(not encoding)
        self.output_path_edit.setEnabled(not encoding)
    
    def _open_settings(self) -> None:
        """Open the settings dialog."""
        dialog = SettingsDialog(self)
        dialog.exec()
    
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """Handle drag enter event for file drops."""
        if event.mimeData().hasUrls():
            event.accept()
            self._show_drop_overlay()
        else:
            event.ignore()
    
    def dragLeaveEvent(self, event) -> None:
        """Handle drag leave event to hide overlay."""
        self._hide_drop_overlay()
        event.accept()
    
    def dropEvent(self, event: QDropEvent) -> None:
        """Handle drop event for file drops."""
        self._hide_drop_overlay()
        
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                # Get the first file path
                file_path = urls[0].toLocalFile()
                if file_path:
                    # Update the image path edit
                    self.image_path_edit.setText(file_path)
                    # Trigger sequence detection
                    self._detect_sequence(file_path)
            event.accept()
        else:
            event.ignore()
