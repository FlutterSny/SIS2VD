from typing import Optional, List, Tuple
from PySide6.QtWidgets import QWidget, QToolTip
from PySide6.QtCore import QRectF
from PySide6.QtGui import QColor, QPainter


class SequencePreviewBar(QWidget):
    """Visual bar showing present vs missing frames in a sequence.

    Each frame gets a proportional slice of the bar width with 1 px dividers.
    Green = present, dark grey = missing/gap.  Hover tooltip shows frame #."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(12)
        self.setMinimumWidth(400)
        self.setToolTipDuration(3000)
        self._start_number: int = 0
        self._end_number: int = 0
        self._gaps: List[Tuple[int, int]] = []
        self._has_sequence: bool = False
        self._frame_color = QColor(76, 175, 80)
        self._gap_color = QColor(55, 55, 55)
        self._encoded_color = QColor(33, 150, 243)
        self._encoding_progress: int = 0
        self._present_frame_count: int = 0

    def set_sequence_info(self, start_number: int, end_number: int,
                          gaps: List[Tuple[int, int]]) -> None:
        self._start_number = start_number
        self._end_number = end_number
        self._gaps = list(gaps)
        self._has_sequence = (end_number >= start_number) and (end_number > 0)
        
        # Calculate present frame count (total range minus gap frames)
        total_range = end_number - start_number + 1
        gap_frames = sum(end - start + 1 for start, end in gaps)
        self._present_frame_count = total_range - gap_frames
        
        self.setToolTip("")
        self.update()

    def clear(self) -> None:
        self._start_number = 0
        self._end_number = 0
        self._gaps = []
        self._has_sequence = False
        self._encoding_progress = 0
        self._present_frame_count = 0
        self.setToolTip("")
        self.update()

    def set_encoding_progress(self, percentage: int) -> None:
        """Set encoding progress percentage (0-100)."""
        self._encoding_progress = percentage
        self.update()

    # ---------------------------------------------------------- internals
    def _build_segments(self) -> List[Tuple[int, int, bool]]:
        """Return [(start, end, is_present), ...] for contiguous runs."""
        if not self._has_sequence:
            return []
        segs: List[Tuple[int, int, bool]] = []
        current = self._start_number
        for gap_start, gap_end in self._gaps:
            if gap_start > current:
                segs.append((current, gap_start - 1, True))
            gs = max(gap_start, self._start_number)
            ge = min(gap_end, self._end_number)
            if gs <= ge:
                segs.append((gs, ge, False))
                current = ge + 1
        if current <= self._end_number:
            segs.append((current, self._end_number, True))
        return segs

    def _frame_at_x(self, x: int) -> Optional[int]:
        """Given pixel x, return the frame number at that position."""
        w = self.width()
        total_range = self._end_number - self._start_number + 1
        if total_range <= 0 or w <= 0:
            return None
        gap_px = 2
        available = w - (total_range - 1) * gap_px
        fw = max(available / total_range, 0.5)
        slot = int(x // (fw + gap_px))
        frame_num = self._start_number + slot
        if self._start_number <= frame_num <= self._end_number:
            return frame_num
        return None

    # ---------------------------------------------------------------- events
    def paintEvent(self, event) -> None:
        if not self._has_sequence:
            return
        painter = QPainter(self)
        width = self.width()
        height = self.height()
        total_range = self._end_number - self._start_number + 1
        if total_range <= 0:
            painter.end()
            return
        gap_px = 1
        available_width = width - (total_range - 1) * gap_px
        frame_width = max(available_width / total_range, 0.5)
        segments = self._build_segments()
        
        # Calculate encoded frame count based on percentage of present frames only
        encoded_present_frames = int((self._encoding_progress / 100) * self._present_frame_count)
        
        # Track how many present frames we've processed
        present_frame_offset = 0
        
        for seg_start, seg_end, is_present in segments:
            first_slot = seg_start - self._start_number
            num_frames = seg_end - seg_start + 1
            x_off = first_slot * (frame_width + gap_px)
            total_w = num_frames * frame_width + max(num_frames - 1, 0) * gap_px
            rect = QRectF(x_off, 0, total_w, height)
            
            if not is_present:
                painter.fillRect(rect, self._gap_color)
            else:
                # Calculate how many frames in this segment should be encoded
                segment_end_present_offset = present_frame_offset + num_frames
                encoded_frames_in_seg = min(encoded_present_frames - present_frame_offset, num_frames)
                
                if encoded_frames_in_seg <= 0:
                    # Entire segment not yet encoded
                    painter.fillRect(rect, self._frame_color)
                elif encoded_frames_in_seg >= num_frames:
                    # Entire segment encoded
                    painter.fillRect(rect, self._encoded_color)
                else:
                    # Partially encoded - split the segment
                    encoded_w = encoded_frames_in_seg * frame_width + max(encoded_frames_in_seg - 1, 0) * gap_px
                    encoded_rect = QRectF(x_off, 0, encoded_w, height)
                    painter.fillRect(encoded_rect, self._encoded_color)
                    
                    remaining_w = total_w - encoded_w
                    remaining_rect = QRectF(x_off + encoded_w, 0, remaining_w, height)
                    painter.fillRect(remaining_rect, self._frame_color)
                
                present_frame_offset += num_frames
        
        painter.end()

    def mouseMoveEvent(self, event) -> None:
        if not self._has_sequence:
            return
        frame = self._frame_at_x(event.position().toPoint().x())
        if frame is not None:
            in_gap = any(gs <= frame <= ge for gs, ge in self._gaps)
            status = "MISSING" if in_gap else "present"
            QToolTip.showText(event.globalPosition().toPoint(),
                              f"Frame {frame} ({status})")
        super().mouseMoveEvent(event)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.update()
