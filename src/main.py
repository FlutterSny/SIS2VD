import sys
import os

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from .ui import MainWindow
from PySide6.QtCore import QTranslator, QLocale
"""Sny's Image Sequence to Video Converter. 2026"""

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("SIS2VD")
    app.setApplicationDisplayName("SIS2VD - Sny's Image Sequence to Video Converter")
    
    # Set application icon
    icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "Icon.icon")
    app.setWindowIcon(QIcon(icon_path))
    
    # Load settings first to get language preference
    from .app_settings import AppSettings
    settings = AppSettings()
    
    # Load translations based on saved language
    translator = QTranslator()
    lang_code = settings.get_language()
    # Load the specific .qm file directly
    if translator.load(f"locales/sis2vd_{lang_code}.qm"):
        app.installTranslator(translator)
    
    if not settings.has_completed_onboarding():
        # Show onboarding dialog
        from .onboarding_dialog import OnboardingDialog
        dialog = OnboardingDialog()
        if dialog.exec() == 0:  # Cancelled
            sys.exit(0)
        
        # Save onboarding completion
        settings.set_onboarding_completed()
        
        # Reload translation with the language selected in onboarding
        lang_code = settings.get_language()
        translator = QTranslator()
        if translator.load(f"locales/sis2vd_{lang_code}.qm"):
            app.installTranslator(translator)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
