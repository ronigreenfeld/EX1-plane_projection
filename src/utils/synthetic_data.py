"""Synthetic volume generation for deterministic unit testing and benchmarking."""

import os
import numpy as np
import nrrd


def create_synthetic_sphere_volume(
    shape: tuple[int, int, int] = (100, 100, 100),
    radius: float = 30.0,
    dtype: np.dtype = np.uint8,
    save_path: str | None = None
) -> np.ndarray:
    """Generates a binary 3D sphere centered inside a volumetric matrix.

    Voxels inside the sphere have value 255 (or 1), while background voxels are 0.
    A planar slice passing through the center analytically yields a circle of the given radius.

    Args:
        shape: (sx, sy, sz) volume dimensions.
        radius: Radius of the sphere in voxel units.
        dtype: Desired NumPy datatype (uint8, uint16, etc.).
        save_path: Optional file path to serialize as NRRD.

    Returns:
        3D NumPy array containing the rasterized sphere.
    """
    sx, sy, sz = shape
    cx, cy, cz = sx / 2.0, sy / 2.0, sz / 2.0

    # Vectorized coordinate grid creation
    x = np.arange(sx, dtype=np.float32) - cx
    y = np.arange(sy, dtype=np.float32) - cy
    z = np.arange(sz, dtype=np.float32) - cz

    # Compute Euclidean distance squared from center
    xx, yy, zz = np.meshgrid(x, y, z, indexing="ij")
    dist_sq = xx ** 2 + yy ** 2 + zz ** 2

    volume = np.zeros(shape, dtype=dtype)
    inside_mask = dist_sq <= (radius ** 2)
    volume[inside_mask] = 255 if dtype == np.uint8 else 1000

    if save_path:
        os.makedirs(os.path.dirname(os.path.abspath(save_path)), exist_ok=True)
        nrrd.write(save_path, volume)

    return volume


def create_benchmark_volume(shape: tuple[int, int, int] = (500, 500, 500)) -> np.ndarray:
    """Generates a 500^3 volume in memory to benchmark against assignment NFR-1."""
    return np.random.randint(0, 256, size=shape, dtype=np.uint8)
