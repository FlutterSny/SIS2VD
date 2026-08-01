from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QGroupBox
from PySide6.QtCore import Qt
from app_settings import AppSettings


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Settings"))
        self.setModal(True)
        self.setFixedSize(350, 200)
        
        # Create layout
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Language selection group
        lang_group = QGroupBox(self.tr("Language"))
        lang_layout = QVBoxLayout()
        
        self.language_combo = QComboBox()
        self.language_combo.addItems([self.tr("English"), self.tr("Français")])
        
        # Set current language from settings
        settings = AppSettings()
        current_lang = settings.get_language()
        if current_lang == "fr":
            self.language_combo.setCurrentText(self.tr("Français"))
        else:
            self.language_combo.setCurrentText(self.tr("English"))
        
        lang_layout.addWidget(self.language_combo)
        lang_group.setLayout(lang_layout)
        layout.addWidget(lang_group)
        
        # Buttons
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
    
    def save_settings(self):
        # Save the selected language
        settings = AppSettings()
        lang_code = "en" if self.language_combo.currentText() == self.tr("English") else "fr"
        current_lang = settings.get_language()
        
        settings.set_language(lang_code)
        
        # Show restart message if language changed
        if lang_code != current_lang:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(
                self,
                self.tr("Restart Required"),
                self.tr("Please restart the application for the language change to take effect.")
            )
        
        self.accept()
