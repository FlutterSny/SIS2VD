import sys
from PySide6.QtWidgets import QApplication
from ui import MainWindow
"""Sny's Image Sequence to Video Converter. 2026"""

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
