"""High-performance MP4 video streaming service with uniform canvas and even-dimension padding."""

from __future__ import annotations
import os
import cv2
import numpy as np
from src.engine.slicer import ProjectionEngine
from src.utils.config import Settings
from src.utils.exceptions import VideoEncodingError
from src.utils.logger import setup_logger

logger = setup_logger("video_writer")


class VideoWriterService:
    """Manages streaming video encoding into an MP4 container adhering to H.264 constraints."""

    def __init__(
        self,
        output_path: str,
        canvas_width: int,
        canvas_height: int,
        fps: int = Settings.DEFAULT_VIDEO_FPS
    ) -> None:
        self.output_path = output_path
        self.fps = fps

        # Even-dimensions constraint: round up odd dimensions to the nearest even integer
        self.canvas_width = canvas_width if (canvas_width % 2 == 0) else (canvas_width + 1)
        self.canvas_height = canvas_height if (canvas_height % 2 == 0) else (canvas_height + 1)

        self._writer: cv2.VideoWriter | None = None
        self._frames_written = 0
        self._init_writer()

    def _init_writer(self) -> None:
        """Initializes the underlying OpenCV VideoWriter with fallback codecs."""
        # Ensure parent output directories exist
        parent_dir = os.path.dirname(os.path.abspath(self.output_path))
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)

        # Cross-platform FOURCC codecs to attempt in sequence
        codecs_to_try = [
            Settings.DEFAULT_FOURCC,  # "mp4v"
            "avc1",                   # H.264
            "XVID",                   # Standard MPEG-4
        ]

        writer_initialized = False
        for codec_str in codecs_to_try:
            fourcc = cv2.VideoWriter_fourcc(*codec_str)
            writer = cv2.VideoWriter(
                self.output_path,
                fourcc,
                float(self.fps),
                (self.canvas_width, self.canvas_height),
                isColor=True  # 3-channel BGR ensures universal player/browser compatibility
            )

            if writer.isOpened():
                self._writer = writer
                writer_initialized = True
                logger.info(
                    "Initialized VideoWriter ('%s') at %dx%d @ %d FPS (file: %s)",
                    codec_str, self.canvas_width, self.canvas_height, self.fps, self.output_path
                )
                break
            else:
                writer.release()

        if not writer_initialized or self._writer is None:
            raise VideoEncodingError(
                f"Failed to initialize VideoWriter at path '{self.output_path}'. "
                f"Attempted codecs: {codecs_to_try}",
                dimensions=(self.canvas_width, self.canvas_height)
            )

    def write_slice(
        self,
        slice_frame: np.ndarray,
        v_min: float | None = None,
        v_max: float | None = None
    ) -> None:
        """Normalizes intensity, centers slice on the uniform canvas, and streams directly to disk.

        Memory Efficiency: Operates in O(1) buffer memory; frames are written immediately
        to the video container without accumulation in RAM.

        Args:
            slice_frame: 2D NumPy array from ProjectionEngine.
            v_min: Minimum global intensity bound for normalization.
            v_max: Maximum global intensity bound for normalization.
        """
        if self._writer is None or not self._writer.isOpened():
            raise VideoEncodingError("Cannot write frame: VideoWriter is closed or uninitialized.")

        # 1. Normalize intensity to uint8 [0, 255]
        uint8_slice = ProjectionEngine.normalize_frame_to_uint8(slice_frame, v_min=v_min, v_max=v_max)
        sh, sw = uint8_slice.shape

        # 2. Centering onto Uniform Canvas of dimensions (canvas_height, canvas_width)
        canvas = np.zeros((self.canvas_height, self.canvas_width), dtype=np.uint8)

        # Calculate centering offsets
        y_offset = max(0, (self.canvas_height - sh) // 2)
        x_offset = max(0, (self.canvas_width - sw) // 2)

        # Slice bounds clipping (in case an individual slice exceeds canvas)
        copy_h = min(sh, self.canvas_height - y_offset)
        copy_w = min(sw, self.canvas_width - x_offset)

        canvas[y_offset : y_offset + copy_h, x_offset : x_offset + copy_w] = uint8_slice[:copy_h, :copy_w]

        # 3. Convert 1-channel grayscale to 3-channel BGR for standard MP4 container compatibility
        bgr_frame = cv2.cvtColor(canvas, cv2.COLOR_GRAY2BGR)

        # 4. Stream frame directly to disk
        self._writer.write(bgr_frame)
        self._frames_written += 1

    @property
    def frames_written(self) -> int:
        """Total number of frames successfully streamed to the video container."""
        return self._frames_written

    def release(self) -> None:
        """Finalizes and closes the video file container."""
        if self._writer is not None:
            self._writer.release()
            self._writer = None
            logger.info("VideoWriter released successfully. Total frames written: %d", self._frames_written)

    def __enter__(self) -> VideoWriterService:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.release()
