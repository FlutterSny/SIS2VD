import sys
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QGroupBox, QFrame
from PySide6.QtCore import Qt
from app_settings import AppSettings

class OnboardingDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Welcome to SIS2VD")
        self.setModal(True)
        self.setFixedSize(400, 300)
        
        # Create layout
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Welcome message
        welcome_label = QLabel(self.tr("Welcome to SIS2VD - Sny's Image Sequence to Video Converter"))
        welcome_label.setAlignment(Qt.AlignCenter)
        welcome_label.setWordWrap(True)
        layout.addWidget(welcome_label)
        
        # Language selection group
        lang_group = QGroupBox(self.tr("Select Language"))
        lang_layout = QVBoxLayout()
        
        self.language_combo = QComboBox()
        self.language_combo.addItems([self.tr("English"), self.tr("Français")])
        self.language_combo.setCurrentText(self.tr("English"))
        
        lang_layout.addWidget(self.language_combo)
        lang_group.setLayout(lang_layout)
        layout.addWidget(lang_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        continue_button = QPushButton(self.tr("Continue"))
        continue_button.setDefault(True)
        continue_button.clicked.connect(self.accept)
        
        button_layout.addStretch()
        button_layout.addWidget(continue_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def accept(self):
        # Save the selected language
        settings = AppSettings()
        lang_code = "en" if self.language_combo.currentText() == "English" else "fr"
        settings.set_language(lang_code)
        
        super().accept()
