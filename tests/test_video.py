"""Unit tests for VideoWriterService and end-to-end CLI execution."""

import os
import tempfile
import unittest
import numpy as np
import cv2
from src.io.video_writer import VideoWriterService
from src.utils.exceptions import VideoEncodingError


class TestVideoWriterService(unittest.TestCase):
    """Test suite for video writer initialization, dimension padding, and streaming."""

    def test_even_dimension_enforcement(self):
        """Odd dimensions must be automatically rounded up to the nearest even number."""
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".mp4") as f:
            tmp_video = f.name

        try:
            # Requesting odd canvas: 137 x 245
            with VideoWriterService(tmp_video, canvas_width=137, canvas_height=245, fps=30) as writer:
                self.assertEqual(writer.canvas_width, 138)
                self.assertEqual(writer.canvas_height, 246)

                # Write a dummy slice
                slice_data = np.full((100, 100), 200, dtype=np.uint8)
                writer.write_slice(slice_data)
                self.assertEqual(writer.frames_written, 1)

            # Re-read with OpenCV to verify physical container dimensions
            cap = cv2.VideoCapture(tmp_video)
            self.assertTrue(cap.isOpened())
            self.assertEqual(int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), 138)
            self.assertEqual(int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)), 246)
            cap.release()
        finally:
            if os.path.exists(tmp_video):
                os.remove(tmp_video)

    def test_memory_streaming_multiple_frames(self):
        """Frames must be streamed sequentially without accumulating in memory."""
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".mp4") as f:
            tmp_video = f.name

        try:
            with VideoWriterService(tmp_video, canvas_width=64, canvas_height=64, fps=30) as writer:
                for i in range(10):
                    frame = np.full((32, 32), i * 20, dtype=np.uint8)
                    writer.write_slice(frame)
                self.assertEqual(writer.frames_written, 10)

            cap = cv2.VideoCapture(tmp_video)
            self.assertTrue(cap.isOpened())
            self.assertEqual(int(cap.get(cv2.CAP_PROP_FRAME_COUNT)), 10)
            cap.release()
        finally:
            if os.path.exists(tmp_video):
                os.remove(tmp_video)


if __name__ == "__main__":
    unittest.main()
