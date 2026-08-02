# Entry point for SIS2VD application
# This is the only supported way to launch the app: python run.py from project root
# This file uses absolute imports and must be at the project root (not inside src/)
# to ensure proper package context for PyInstaller and local development.

from src.main import main

if __name__ == "__main__":
    main()
