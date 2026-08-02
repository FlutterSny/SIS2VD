# Entry point for SIS2VD. Launch the app with `python run.py` from the
# project root. This is the single supported entry point for both local
# dev runs and the PyInstaller build.
from src.main import main

if __name__ == "__main__":
    main()
