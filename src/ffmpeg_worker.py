import subprocess
import re
from pathlib import Path
from typing import Optional
from PySide6.QtCore import QThread, Signal

from .ffmpeg_locator import get_ffmpeg_path


class FFmpegWorker(QThread):
    """Worker thread for executing FFmpeg encoding."""
    
    # Signals
    progress_updated = Signal(int)  # Progress percentage (0-100)
    log_output = Signal(str)  # Log line from FFmpeg
    finished = Signal(bool, str)  # Completion signal (success, message)
    
    def __init__(self) -> None:
        super().__init__()
        self._cancelled: bool = False
        self._start_number: Optional[int] = None
        self._framerate: Optional[int] = None
        self._input_pattern: Optional[str] = None
        self._input_directory: Optional[Path] = None
        self._crf: Optional[int] = None
        self._preset: Optional[str] = None
        self._output_path: Optional[Path] = None
        self._total_frames: Optional[int] = None
        self._allow_overwrite: bool = False
        self._process: Optional[subprocess.Popen] = None
        self._output_file_created: bool = False
    
    def set_parameters(self, start_number: int, framerate: int, 
                       input_pattern: str, input_directory: Path,
                       crf: int, preset: str, output_path: Path, total_frames: int,
                       allow_overwrite: bool = False) -> None:
        """Set FFmpeg encoding parameters."""
        self._start_number = start_number
        self._framerate = framerate
        self._input_pattern = input_pattern
        self._input_directory = input_directory
        self._crf = crf
        self._preset = preset
        self._output_path = output_path
        self._total_frames = total_frames
        self._allow_overwrite = allow_overwrite
    
    def _build_ffmpeg_command(self) -> list[str]:
        """Build FFmpeg command with all parameters.
        
        FFmpeg command parameters:
        - start_number: Starting frame number for the sequence
        - framerate: Input framerate (frames per second)
        - i: Input file pattern (e.g., /path/to/Shot_1_%04d.png)
        - c:v:libx264: Use H.264 video codec
        - crf: Constant Rate Factor (quality, 0-51, lower = better quality)
        - preset: Encoding speed vs compression efficiency (ultrafast to veryslow)
        - pix_fmt:yuv420p: Pixel format for maximum compatibility
        - output_str: Output MP4 file path
        """
        # Convert output path to string for cross-platform compatibility
        output_str = str(self._output_path)
        
        # Build full input pattern with directory path
        # FFmpeg needs the full path to the pattern
        if self._input_directory:
            input_pattern = str(self._input_directory / self._input_pattern)
        else:
            input_pattern = self._input_pattern
        
        # Resolve FFmpeg binary (portable or system PATH)
        ffmpeg_binary = get_ffmpeg_path()
        if ffmpeg_binary is None:
            raise FileNotFoundError(
                "FFmpeg not found. Please install FFmpeg or download a portable binary."
            )

        # Build the command list
        command = [
            ffmpeg_binary,
            '-start_number', str(self._start_number),
            '-framerate', str(self._framerate),
            '-i', input_pattern,
            '-c:v', 'libx264',
            '-crf', str(self._crf),
            '-preset', self._preset,
            '-pix_fmt', 'yuv420p',
        ]
        
        # Add -y flag to allow overwriting existing output file
        if self._allow_overwrite:
            command.append('-y')
        
        command.append(output_str)
        
        return command
    
    def run(self) -> None:
        """Main thread execution method."""
        try:
            # Build FFmpeg command
            command = self._build_ffmpeg_command()
            
            # Log the command
            self.log_output.emit(f"Executing: {' '.join(command)}")
            
            # Start FFmpeg process
            self._process = subprocess.Popen(
                command,
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE,
                universal_newlines=True
            )
            
            # Read stderr line by line for progress
            while True:
                if self._cancelled:
                    self._terminate_process()
                    self._cleanup_output_file()
                    self.finished.emit(False, "Encoding cancelled by user")
                    return
                
                # Read line from stderr
                line = self._process.stderr.readline()
                
                if not line and self._process.poll() is not None:
                    break
                
                if line:
                    # Emit log line
                    self.log_output.emit(line.strip())
                    
                    # Parse for frame progress
                    self._parse_progress(line)
            
            # Check return code
            return_code = self._process.poll()
            if return_code == 0:
                self._output_file_created = True
                self.finished.emit(True, "Encoding completed successfully")
            else:
                self._cleanup_output_file()
                self.finished.emit(False, f"FFmpeg failed with return code {return_code}")
                
        except FileNotFoundError:
            self.finished.emit(False, "FFmpeg not found. Please install FFmpeg and add it to PATH.")
        except Exception as e:
            self.finished.emit(False, f"Error during encoding: {str(e)}")
    
    def _parse_progress(self, line: str) -> None:
        """Parse FFmpeg output line for progress information."""
        # Look for frame= indicator in FFmpeg output
        # Format: frame= 150 fps=30 q=28.0 size= 1024kB time=00:00:05.00 bitrate=1638.4kbits/s speed=1x
        match = re.search(r'frame=\s*(\d+)', line)
        if match:
            current_frame = int(match.group(1))
            
            # Calculate percentage based on total frames
            if self._total_frames and self._total_frames > 0:
                percentage = int((current_frame / self._total_frames) * 100)
                # Cap at 100
                percentage = min(percentage, 100)
                self.progress_updated.emit(percentage)
    
    def cancel(self) -> None:
        """Cancel the FFmpeg process."""
        self._cancelled = True
        self._terminate_process()
        self._cleanup_output_file()
    
    def _terminate_process(self) -> None:
        """Gracefully terminate the FFmpeg subprocess."""
        if self._process and self._process.poll() is None:
            # Try graceful termination first
            self._process.terminate()
            try:
                # Wait up to 5 seconds for process to terminate
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill if it doesn't terminate gracefully
                self._process.kill()
                self._process.wait()
    
    def _cleanup_output_file(self) -> None:
        """Clean up the output file if encoding was cancelled or failed."""
        if not self._output_file_created and self._output_path:
            try:
                output_file = Path(self._output_path)
                if output_file.exists():
                    output_file.unlink()
                    self.log_output.emit(f"Cleaned up incomplete output file: {output_file}")
            except Exception as e:
                self.log_output.emit(f"Warning: Could not clean up output file: {str(e)}")