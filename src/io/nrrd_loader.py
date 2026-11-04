"""NRRD 3D volume ingestion, metadata validation, and memory-mapped querying."""

from __future__ import annotations
import os
import numpy as np
import nrrd
from src.utils.config import Settings
from src.utils.exceptions import VolumeIOError
from src.utils.logger import setup_logger

logger = setup_logger("nrrd_loader")


class NRRDVolume:
    """Encapsulates a 3D volumetric raster array with validation and spatial sampling."""

    def __init__(self, data: np.ndarray, header: dict | None = None, filepath: str | None = None) -> None:
        self.data = np.ascontiguousarray(data)
        self.header = header or {}
        self.filepath = filepath

        self._validate_volume()

    def _validate_volume(self) -> None:
        """Validates dimensionality and size constraints specified in SRS FR-1."""
        if self.data.ndim != 3:
            raise VolumeIOError(
                f"Volume must be strictly 3-dimensional. Received {self.data.ndim}D array.",
                filepath=self.filepath
            )

        sx, sy, sz = self.shape
        if not (Settings.MIN_VOLUME_DIM <= sx < Settings.MAX_VOLUME_DIM and
                Settings.MIN_VOLUME_DIM <= sy < Settings.MAX_VOLUME_DIM and
                Settings.MIN_VOLUME_DIM <= sz < Settings.MAX_VOLUME_DIM):
            raise VolumeIOError(
                f"Volume dimensions ({sx}, {sy}, {sz}) violate constraints (1 <= dim < {Settings.MAX_VOLUME_DIM})",
                filepath=self.filepath
            )

    @classmethod
    def load(cls, filepath: str) -> NRRDVolume:
        """Loads and parses an NRRD file from disk.

        Args:
            filepath: Path to the target .nrrd file.

        Returns:
            Instantiated and validated NRRDVolume.

        Raises:
            VolumeIOError: On file not found, corrupt header, or invalid dimensions.
        """
        if not os.path.exists(filepath):
            raise VolumeIOError(f"NRRD file not found: {filepath}", filepath=filepath)

        try:
            data, header = nrrd.read(filepath)
            logger.info("Successfully loaded NRRD volume '%s' with shape %s, dtype %s", filepath, data.shape, data.dtype)
            return cls(data, header=header, filepath=filepath)
        except Exception as err:
            if isinstance(err, VolumeIOError):
                raise
            raise VolumeIOError(f"Failed to read NRRD file '{filepath}': {err}", filepath=filepath) from err

    @property
    def shape(self) -> tuple[int, int, int]:
        """Volume dimensions (sx, sy, sz)."""
        return self.data.shape

    @property
    def dtype(self) -> np.dtype:
        """NumPy data type of the underlying voxels."""
        return self.data.dtype

    def sample_voxels_vectorized(
        self,
        x_idx: np.ndarray,
        y_idx: np.ndarray,
        z_idx: np.ndarray
    ) -> np.ndarray:
        """Vectorized spatial sampling with branchless Out-of-Bounds (OOB) zero-padding.

        Args:
            x_idx: 1D array of integer x-coordinates.
            y_idx: 1D array of integer y-coordinates.
            z_idx: 1D array of integer z-coordinates.

        Returns:
            1D array containing sampled voxel intensities, with out-of-bounds voxels set to 0.
        """
        sx, sy, sz = self.shape
        result = np.zeros(x_idx.shape, dtype=self.data.dtype)

        # Boolean in-bounds mask (branchless)
        in_bounds = (
            (x_idx >= 0) & (x_idx < sx) &
            (y_idx >= 0) & (y_idx < sy) &
            (z_idx >= 0) & (z_idx < sz)
        )

        if np.any(in_bounds):
            valid_x = x_idx[in_bounds]
            valid_y = y_idx[in_bounds]
            valid_z = z_idx[in_bounds]
            result[in_bounds] = self.data[valid_x, valid_y, valid_z]

        return result
