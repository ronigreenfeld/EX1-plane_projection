"""High-performance vectorized 2D plane projection engine from 3D volumetric data."""

from __future__ import annotations
import math
import numpy as np
from src.geometry.plane import PlaneGeometry, IsoscelesTrianglePlane, IsoscelesTrapezoidPlane
from src.io.nrrd_loader import NRRDVolume
from src.utils.config import Settings
from src.utils.exceptions import GeometryValidationError
from src.utils.logger import setup_logger

logger = setup_logger("projection_engine")


class ProjectionEngine:
    """Orchestrates vectorized slicing of 3D volumes along arbitrary geometric cutting planes."""

    def __init__(self, volume: NRRDVolume | None = None) -> None:
        self.volume = volume

    def set_volume(self, volume: NRRDVolume) -> None:
        """Sets or replaces the active volumetric dataset."""
        self.volume = volume

    def slice_plane(self, plane: PlaneGeometry, volume: NRRDVolume | None = None) -> np.ndarray:
        """Extracts a 2D cross-sectional slice from the volume along the given plane.

        Adheres strictly to the assignment scanline algorithm with complete 2D NumPy SIMD
        vectorization, nearest-neighbor rounding, and horizontal centering.

        If the plane is geometrically invalid or degenerate, logs a warning and returns
        a zero-filled matrix (black frame) to preserve video synchronization.

        Args:
            plane: Cutting plane definition (Triangle or Trapezoid).
            volume: Optional override for the target volume; defaults to self.volume.

        Returns:
            2D NumPy array of dimensions [D_height, D_width] containing extracted voxel values.
        """
        vol = volume or self.volume
        if vol is None:
            raise ValueError("No volume provided to ProjectionEngine.")

        # 1. Validation & Degeneracy Protection
        try:
            plane.validate()
            d_height, d_width = plane.get_dimensions()
        except GeometryValidationError as err:
            logger.warning("Invalid plane geometry skipped (rendering black frame): %s", err)
            try:
                d_height, d_width = plane.get_dimensions()
            except Exception:
                d_height, d_width = (256, 256)
            safe_h = min(max(1, d_height), Settings.MAX_CANVAS_DIM)
            safe_w = min(max(1, d_width), Settings.MAX_CANVAS_DIM)
            return np.zeros((safe_h, safe_w), dtype=vol.dtype)

        # Ensure valid non-zero canvas dimensions
        if d_height <= 0 or d_width <= 0:
            logger.warning("Degenerate plane dimensions (%d, %d); returning 1x1 zero frame.", d_height, d_width)
            return np.zeros((max(1, d_height), max(1, d_width)), dtype=vol.dtype)

        # 2. Extract geometry parameters
        if isinstance(plane, IsoscelesTrianglePlane):
            a_start_x, a_start_y, a_start_z = plane.a.x, plane.a.y, plane.a.z
            a_end_x, a_end_y, a_end_z = plane.a.x, plane.a.y, plane.a.z
            v_left = (plane.b - plane.a).normalize()
            v_right = (plane.c - plane.a).normalize()
        elif isinstance(plane, IsoscelesTrapezoidPlane):
            a_start_x, a_start_y, a_start_z = plane.a1.x, plane.a1.y, plane.a1.z
            a_end_x, a_end_y, a_end_z = plane.a2.x, plane.a2.y, plane.a2.z
            v_left = (plane.b - plane.a1).normalize()
            v_right = (plane.c - plane.a2).normalize()
        else:
            return self._slice_generic(plane, vol, d_height, d_width)

        vl_x, vl_y, vl_z = v_left.dx, v_left.dy, v_left.dz
        vr_x, vr_y, vr_z = v_right.dx, v_right.dy, v_right.dz

        vol_data = vol.data
        sx, sy, sz = vol.shape

        # 3. Vectorized coordinate generation across all scanlines simultaneously
        y_vals = np.arange(d_height, dtype=np.float64)

        p_start_x = a_start_x + y_vals * vl_x
        p_start_y = a_start_y + y_vals * vl_y
        p_start_z = a_start_z + y_vals * vl_z

        p_end_x = a_end_x + y_vals * vr_x
        p_end_y = a_end_y + y_vals * vr_y
        p_end_z = a_end_z + y_vals * vr_z

        diff_x = p_end_x - p_start_x
        diff_y = p_end_y - p_start_y
        diff_z = p_end_z - p_start_z

        d12 = np.sqrt(diff_x * diff_x + diff_y * diff_y + diff_z * diff_z)

        # Safe step vector calculation
        safe_d12 = np.where(d12 < Settings.GEOMETRY_EPSILON, 1.0, d12)
        dp_x = diff_x / safe_d12
        dp_y = diff_y / safe_d12
        dp_z = diff_z / safe_d12

        # Horizontal centering offset: floor((D_width - d12) / 2)
        x_offset = np.floor((d_width - d12) / 2.0).astype(np.int32)
        num_steps = np.floor(d12).astype(np.int32) + 1

        # 4. Broadcasted 2D grid generation via open grid
        Y, X = np.ogrid[:d_height, :d_width]

        # Scanline active pixel mask
        active_mask = (
            (X >= x_offset[:, None]) &
            (X < (x_offset[:, None] + num_steps[:, None])) &
            (X >= 0) & (X < d_width)
        )

        valid_y, valid_x = np.where(active_mask)
        if len(valid_y) == 0:
            return np.zeros((d_height, d_width), dtype=vol.dtype)

        # Relative step t along the scanline
        t = (valid_x - x_offset[valid_y]).astype(np.float64)

        # Continuous 3D points
        pts_x = p_start_x[valid_y] + t * dp_x[valid_y]
        pts_y = p_start_y[valid_y] + t * dp_y[valid_y]
        pts_z = p_start_z[valid_y] + t * dp_z[valid_y]

        # Nearest-Neighbor discrete voxel indices
        idx_x = np.rint(pts_x).astype(np.int32)
        idx_y = np.rint(pts_y).astype(np.int32)
        idx_z = np.rint(pts_z).astype(np.int32)

        # Boolean in-bounds volume mask (branchless)
        in_bounds = (
            (idx_x >= 0) & (idx_x < sx) &
            (idx_y >= 0) & (idx_y < sy) &
            (idx_z >= 0) & (idx_z < sz)
        )

        # 5. Populate output image directly
        output_image = np.zeros((d_height, d_width), dtype=vol.dtype)
        if np.any(in_bounds):
            target_y = valid_y[in_bounds]
            target_x = valid_x[in_bounds]
            output_image[target_y, target_x] = vol_data[
                idx_x[in_bounds],
                idx_y[in_bounds],
                idx_z[in_bounds]
            ]

        return output_image

    def _slice_generic(
        self,
        plane: PlaneGeometry,
        vol: NRRDVolume,
        d_height: int,
        d_width: int
    ) -> np.ndarray:
        """Fallback slicing loop using general PlaneGeometry abstract interface."""
        output_image = np.zeros((d_height, d_width), dtype=vol.dtype)
        for y in range(d_height):
            p_start, p_end = plane.get_scanline_endpoints(y)
            d12 = p_start.distance_to(p_end)
            if d12 < Settings.GEOMETRY_EPSILON:
                continue
            dp = (p_end - p_start) / d12
            num_steps = int(math.floor(d12)) + 1
            t = np.arange(num_steps, dtype=np.float64)
            idx_x = np.rint(p_start.x + t * dp.dx).astype(np.int32)
            idx_y = np.rint(p_start.y + t * dp.dy).astype(np.int32)
            idx_z = np.rint(p_start.z + t * dp.dz).astype(np.int32)
            sampled = vol.sample_voxels_vectorized(idx_x, idx_y, idx_z)
            x_offset = int(math.floor((d_width - d12) / 2.0))
            col_start = max(0, x_offset)
            col_end = min(d_width, x_offset + num_steps)
            src_start = max(0, -x_offset)
            src_end = src_start + (col_end - col_start)
            if col_end > col_start and src_end > src_start:
                output_image[y, col_start:col_end] = sampled[src_start:src_end]
        return output_image

    @staticmethod
    def normalize_frame_to_uint8(
        frame: np.ndarray,
        v_min: float | None = None,
        v_max: float | None = None
    ) -> np.ndarray:
        """Scales voxel intensities linearly to uint8 [0, 255] for video encoding (SRS FR-5).

        Args:
            frame: 2D NumPy array of any numeric type.
            v_min: Minimum intensity bound; computed from frame if None.
            v_max: Maximum intensity bound; computed from frame if None.

        Returns:
            2D NumPy array of uint8 values in range [0, 255].
        """
        if frame.dtype == np.uint8:
            return frame

        min_val = float(v_min if v_min is not None else frame.min())
        max_val = float(v_max if v_max is not None else frame.max())

        diff = max_val - min_val
        if diff < 1e-6:
            return np.zeros(frame.shape, dtype=np.uint8)

        normalized = ((frame.astype(np.float32) - min_val) / diff) * 255.0
        return np.clip(normalized, 0, 255).astype(np.uint8)
