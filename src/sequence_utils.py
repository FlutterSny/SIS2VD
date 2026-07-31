import re
from pathlib import Path
from typing import Optional, Dict, Any, List


def extract_pattern(filename: str) -> Optional[Dict[str, Any]]:
    """
    Extract sequence pattern from a filename.
    
    Parses filename to extract prefix, padding digits, and start_number.
    Handles various formats: Shot_1_0100.png, seq.0001.exr, frame_00123.jpg
    
    Args:
        filename: The filename to analyze (e.g., "Shot_1_0100.png")
    
    Returns:
        Dictionary with pattern info or None if no pattern detected:
        {
            'prefix': 'Shot_1_',          # Everything before the number
            'padding': 4,                  # Number of digits (e.g., 0100 = 4)
            'start_number': 100,           # The actual number value
            'extension': '.png',           # File extension
            'pattern': 'Shot_1_%04d.png'   # printf-style pattern for ffmpeg
        }
    """
    # Remove directory path if present
    filename = Path(filename).name
    
    # Split into name and extension
    name_parts = filename.rsplit('.', 1)
    if len(name_parts) != 2:
        return None
    
    name, extension = name_parts
    extension = f".{extension}"
    
    # Find the last sequence of digits in the filename
    # This handles cases like Shot_1_0100.png (we want the 0100 part)
    match = re.search(r'(\d+)$', name)
    if not match:
        return None
    
    number_str = match.group(1)
    number_start = match.start()
    number_end = match.end()
    
    # Extract prefix (everything before the number)
    prefix = name[:number_start]
    
    # Extract the number
    start_number = int(number_str)
    padding = len(number_str)
    
    # Create ffmpeg-style pattern
    pattern = f"{prefix}%0{padding}d{extension}"
    
    return {
        'prefix': prefix,
        'padding': padding,
        'start_number': start_number,
        'extension': extension,
        'pattern': pattern
    }


def scan_sequence(directory: Path, pattern_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Scan directory for files matching the sequence pattern.
    
    Args:
        directory: Path to the directory containing the sequence
        pattern_info: Dictionary from extract_pattern() with pattern details
    
    Returns:
        Dictionary with sequence info or None if no files found:
        {
            'total_count': 150,              # Total number of files in sequence
            'start_number': 100,             # Starting frame number
            'end_number': 249,               # Ending frame number
            'gaps': [(110, 115), (200, 205)], # List of (start, end) tuples for gaps
            'missing_count': 11,             # Total number of missing frames
            'files': [Path(...), ...]        # List of actual file paths found
        }
    """
    prefix = pattern_info['prefix']
    extension = pattern_info['extension']
    padding = pattern_info['padding']
    
    # Build regex pattern to match files
    # e.g., Shot_1_(\d{4})\.png
    regex_pattern = re.escape(prefix) + r'(\d{' + str(padding) + r'})' + re.escape(extension) + r'$'
    pattern = re.compile(regex_pattern)
    
    # Scan directory for matching files
    files = []
    numbers = []
    
    try:
        for file_path in directory.iterdir():
            if file_path.is_file():
                match = pattern.match(file_path.name)
                if match:
                    number = int(match.group(1))
                    files.append((number, file_path))
                    numbers.append(number)
    except (PermissionError, OSError):
        return None
    
    if not files:
        return None
    
    # Sort by frame number
    files.sort(key=lambda x: x[0])
    numbers.sort()
    
    # Extract just the file paths in order
    sorted_files = [f[1] for f in files]
    
    # Calculate sequence info
    start_number = numbers[0]
    end_number = numbers[-1]
    total_count = len(numbers)
    
    # Detect gaps
    gaps = []
    missing_count = 0
    
    for i in range(len(numbers) - 1):
        current = numbers[i]
        next_num = numbers[i + 1]
        
        if next_num > current + 1:
            gaps.append((current + 1, next_num - 1))
            missing_count += (next_num - current - 1)
    
    return {
        'total_count': total_count,
        'start_number': start_number,
        'end_number': end_number,
        'gaps': gaps,
        'missing_count': missing_count,
        'files': sorted_files
    }