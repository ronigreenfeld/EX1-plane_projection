"""3D Point primitive with spatial arithmetic and operator overloading."""

from __future__ import annotations
import math
from dataclasses import dataclass
import numpy as np
from src.geometry.vector import Vector3D


@dataclass(frozen=True)
class Point3D:
    """Represents an immutable 3D Cartesian coordinate (x, y, z)."""

    x: float
    y: float
    z: float

    def distance_to(self, other: Point3D) -> float:
        """Calculates Euclidean distance to another 3D point."""
        return math.sqrt(
            (self.x - other.x) ** 2 +
            (self.y - other.y) ** 2 +
            (self.z - other.z) ** 2
        )

    def __sub__(self, other: Point3D) -> Vector3D:
        """Subtracting two points yields a displacement Vector3D (self - other)."""
        return Vector3D(self.x - other.x, self.y - other.y, self.z - other.z)

    def __add__(self, vec: Vector3D) -> Point3D:
        """Translating a point by a Vector3D yields a new Point3D."""
        if not isinstance(vec, Vector3D):
            return NotImplemented
        return Point3D(self.x + vec.dx, self.y + vec.dy, self.z + vec.dz)

    def to_numpy(self) -> np.ndarray:
        """Converts point to a 1D NumPy float64 coordinate array."""
        return np.array([self.x, self.y, self.z], dtype=np.float64)

    def __repr__(self) -> str:
        return f"Point3D({self.x:.4f}, {self.y:.4f}, {self.z:.4f})"
