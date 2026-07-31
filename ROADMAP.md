# SIS2VD Roadmap
# Sny's Image Sequence 2 Video

## Overview
Python utility with PySide6 GUI to convert image sequences to MP4 video via ffmpeg.

---

## Phase 1: Project Setup and Structure

### Step 1.1: Create Project Structure
- [x] Create `src/` directory
- [x] Create `src/main.py` (entry point)
- [x] Create `src/ui.py` (MainWindow class)
- [x] Create `src/ffmpeg_worker.py` (QThread for ffmpeg)
- [x] Create `src/sequence_utils.py` (pattern detection)
- [x] Create `requirements.txt` with PySide6 dependency

**Validation:** All files exist with basic structure, requirements.txt contains PySide6

---

### Step 1.2: Basic Entry Point
- [x] Implement `src/main.py` with QApplication initialization
- [x] Create basic MainWindow instance
- [x] Add sys.exit handling
- [x] Test application launches without errors

**Validation:** Running `python src/main.py` opens an empty window

---

## Phase 2: UI Foundation

### Step 2.1: MainWindow Layout
- [x] Implement MainWindow class in `src/ui.py` with QMainWindow
- [x] Create vertical layout
- [x] Add dark theme support (respect system theme)
- [x] Set window title and minimum size

**Validation:** Window opens with proper layout and dark theme on supported systems

---

### Step 2.2: Image Selection UI
- [x] Add "Parcourir" button (QPushButton)
- [x] Add QLineEdit to display selected image path
- [x] Implement QFileDialog for file selection
- [x] Filter for image files (*.png, *.jpg, *.jpeg, *.tiff, *.exr)

**Validation:** Button opens file dialog, selected path displays in text field

---

### Step 2.3: Settings UI Components
- [x] Add Framerate QSpinBox (default 30, range 1-120)
- [x] Add CRF QSlider (0-51, default 18)
- [x] Add QLabel for CRF with tooltip explaining quality scale
- [x] Add x264 Preset QComboBox (ultrafast to veryslow, default medium)
- [x] Add output path QLineEdit
- [x] Add "Parcourir" button for output file selection (QFileDialog save)

**Validation:** All controls visible, CRF tooltip displays, preset list complete

---

### Step 2.4: Action Buttons and Progress
- [x] Add "Générer la vidéo" button
- [x] Add "Annuler" button (initially disabled)
- [x] Add QProgressBar (initially hidden/reset)
- [x] Add QTextEdit for ffmpeg logs (collapsible/scrollable, read-only)
- [x] Add QLabel for detected sequence info (count, pattern)

**Validation:** All buttons and progress elements present in layout

---

## Phase 3: Sequence Detection

### Step 3.1: Pattern Extraction
- [x] Implement `extract_pattern()` in `src/sequence_utils.py`
- [x] Parse filename to extract prefix, padding digits, start_number
- [x] Handle various formats: Shot_1_0100.png, seq.0001.exr, frame_00123.jpg
- [x] Return pattern data structure

**Validation:** Function correctly extracts pattern from test filenames

---

### Step 3.2: Sequence Scanning
- [x] Implement `scan_sequence()` in `src/sequence_utils.py`
- [x] Scan directory for files matching pattern
- [x] Count consecutive files
- [x] Detect gaps in sequence
- [x] Return total count and gap information

**Validation:** Correctly counts sequential files, detects gaps

---

### Step 3.3: UI Integration
- [x] Connect image selection to pattern detection
- [x] Update sequence info label on file selection
- [x] Show warning if gaps detected
- [x] Set default output path based on sequence location

**Validation:** Selecting image updates info label with count and pattern

---

## Phase 4: FFmpeg Worker

### Step 4.1: Worker Thread Setup
- [x] Create FFmpegWorker class inheriting QThread in `src/ffmpeg_worker.py`
- [x] Implement run() method
- [x] Add signal for progress updates (int percentage)
- [x] Add signal for log output (str)
- [x] Add signal for completion (bool success, str message)
- [x] Add cancellation flag and method

**Validation:** Worker class compiles, signals defined

---

### Step 4.2: FFmpeg Command Building
- [x] Implement command builder with parameters:
  - start_number from pattern
  - framerate from settings
  - input pattern (ffmpeg-style)
  - codec: libx264
  - crf value
  - preset
  - pix_fmt: yuv420p
  - output path
- [x] Use pathlib for cross-platform paths

**Validation:** Generated command is valid ffmpeg syntax

---

### Step 4.3: Process Execution
- [x] Implement subprocess.Popen for ffmpeg
- [x] Capture stderr in real-time
- [x] Parse stderr for "frame=" progress indicator
- [x] Calculate percentage based on total frame count
- [x] Emit progress signals
- [x] Emit log lines

**Validation:** Worker can execute ffmpeg and parse output

---

### Step 4.4: Cancellation Handling
- [x] Implement graceful process termination
- [x] Kill ffmpeg subprocess on cancel
- [x] Clean up temporary files if needed
- [x] Emit cancellation signal

**Validation:** Cancel button terminates ffmpeg cleanly

---

## Phase 5: Main Window Integration

### Step 5.1: FFmpeg Check
- [x] Add ffmpeg availability check at startup
- [x] Use `shutil.which()` to detect ffmpeg
- [x] Show QMessageBox if ffmpeg not found
- [x] Disable generation button if ffmpeg missing

**Validation:** App shows clear error if ffmpeg not in PATH

---

### Step 5.2: Connect Generation Button
- [x] Connect "Générer" button to worker creation
- [x] Pass all parameters to worker
- [x] Connect worker signals to UI updates
- [x] Disable controls during encoding
- [x] Enable "Annuler" button during encoding

**Validation:** Clicking generate starts encoding, UI updates properly

---

### Step 5.3: Progress and Log Display
- [x] Connect progress signal to QProgressBar
- [x] Connect log signal to QTextEdit
- [x] Auto-scroll QTextEdit to bottom
- [x] Handle completion signal
- [x] Re-enable controls on completion
- [x] Show success/error message

**Validation:** Progress bar updates, logs display, completion handled

---

### Step 5.4: Error Handling
- [x] Catch subprocess errors
- [x] Parse ffmpeg error messages
- [x] Display user-friendly error in QMessageBox
- [x] Handle invalid parameters
- [x] Handle file permission errors

**Validation:** Errors show clear messages in UI

---

## Phase 6: Cross-Platform Compatibility

### Step 6.1: Path Handling
- [ ] Ensure all paths use pathlib.Path
- [ ] Test path joining on Linux
- [ ] Verify no hardcoded forward/backward slashes
- [ ] Handle path separators in ffmpeg patterns

**Validation:** Paths work correctly on Linux

---

### Step 6.2: Theme Compatibility
- [ ] Test dark theme on Linux (Breeze/Adwaita)
- [ ] Ensure UI readable in both light/dark themes
- [ ] Test on Windows if possible

**Validation:** UI looks correct in system dark theme

---

## Phase 7: Code Quality and Documentation

### Step 7.1: Type Hints
- [ ] Add type hints to all functions
- [ ] Add type hints to class attributes
- [ ] Use proper typing imports (Optional, List, Dict, etc.)

**Validation:** mypy passes without errors

---

### Step 7.2: Comments and Docstrings
- [ ] Add docstrings to all classes
- [ ] Add docstrings to all public methods
- [ ] Add inline comments for complex logic
- [ ] Document ffmpeg command parameters

**Validation:** Code is well-documented and understandable

---

### Step 7.3: Requirements and README
- [ ] Update requirements.txt with exact PySide6 version
- [ ] Add Python version requirement (3.11+)
- [ ] Create README.md with:
  - Project description
  - Installation instructions
  - Usage guide
  - Requirements (ffmpeg)
  - Known limitations

**Validation:** README is complete and helpful

---

## Phase 8: Testing and Validation

### Step 8.1: Manual Testing
- [ ] Test with PNG sequence
- [ ] Test with JPG sequence
- [ ] Test with different framerates
- [ ] Test with different CRF values
- [ ] Test with different presets
- [ ] Test cancellation during encoding
- [ ] Test with gaps in sequence
- [ ] Test with non-sequential files

**Validation:** All scenarios work correctly

---

### Step 8.2: Edge Cases
- [ ] Test with single image
- [ ] Test with very large sequence
- [ ] Test with special characters in path
- [ ] Test with non-existent output directory
- [ ] Test with read-only output location

**Validation:** Edge cases handled gracefully

---

## Phase 9: Final Polish

### Step 9.1: UI Refinements
- [ ] Ensure consistent spacing and alignment
- [ ] Add keyboard shortcuts (Escape to cancel)
- [ ] Set reasonable window size
- [ ] Add status bar for additional info

**Validation:** UI feels polished and professional

---

### Step 9.2: Performance Check
- [ ] Verify UI remains responsive during encoding
- [ ] Check memory usage with large sequences
- [ ] Ensure log display doesn't slow down encoding

**Validation:** No performance issues detected

---

## Completion Criteria

- [ ] All phases completed
- [ ] Application successfully converts image sequences to MP4
- [ ] FFmpeg integration works smoothly
- [ ] Error handling is robust
- [ ] Code is well-documented and typed
- [ ] Cross-platform paths handled correctly
- [ ] README provides complete setup instructions

---

## Notes

- FFmpeg must be installed separately (not bundled)
- Priority is robustness over fancy UI
- Dark theme should respect system preferences
- All paths must use pathlib for cross-platform compatibility
