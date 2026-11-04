"""3D Algebraic Vector primitive with linear algebra operations."""

from __future__ import annotations
import math
from dataclasses import dataclass
import numpy as np
from src.utils.config import Settings
from src.utils.exceptions import GeometryValidationError


@dataclass(frozen=True)
class Vector3D:
    """Represents an immutable 3D displacement vector (dx, dy, dz)."""

    dx: float
    dy: float
    dz: float

    def length(self) -> float:
        """Computes Euclidean magnitude of the vector."""
        return math.sqrt(self.dx ** 2 + self.dy ** 2 + self.dz ** 2)

    def normalize(self) -> Vector3D:
        """Returns a normalized unit vector in the same direction.

        Raises:
            GeometryValidationError: If the vector magnitude is near zero (< Settings.GEOMETRY_EPSILON).
        """
        mag = self.length()
        if mag < Settings.GEOMETRY_EPSILON:
            raise GeometryValidationError(
                f"Cannot normalize degenerate zero-length vector with magnitude {mag:.6f}"
            )
        return Vector3D(self.dx / mag, self.dy / mag, self.dz / mag)

    def dot(self, other: Vector3D) -> float:
        """Computes scalar (dot) product with another Vector3D."""
        return (self.dx * other.dx) + (self.dy * other.dy) + (self.dz * other.dz)

    def cross(self, other: Vector3D) -> Vector3D:
        """Computes cross product with another Vector3D (self x other)."""
        return Vector3D(
            self.dy * other.dz - self.dz * other.dy,
            self.dz * other.dx - self.dx * other.dz,
            self.dx * other.dy - self.dy * other.dx
        )

    def __add__(self, other: Vector3D) -> Vector3D:
        if not isinstance(other, Vector3D):
            return NotImplemented
        return Vector3D(self.dx + other.dx, self.dy + other.dy, self.dz + other.dz)

    def __sub__(self, other: Vector3D) -> Vector3D:
        if not isinstance(other, Vector3D):
            return NotImplemented
        return Vector3D(self.dx - other.dx, self.dy - other.dy, self.dz - other.dz)

    def __mul__(self, scalar: float) -> Vector3D:
        """Vector scaling by scalar."""
        if not isinstance(scalar, (int, float)):
            return NotImplemented
        return Vector3D(self.dx * scalar, self.dy * scalar, self.dz * scalar)

    def __rmul__(self, scalar: float) -> Vector3D:
        """Reflected scalar multiplication (scalar * vector)."""
        return self.__mul__(scalar)

    def __truediv__(self, scalar: float) -> Vector3D:
        """Vector scalar division."""
        if not isinstance(scalar, (int, float)):
            return NotImplemented
        if abs(scalar) < Settings.GEOMETRY_EPSILON:
            raise GeometryValidationError("Cannot divide vector by near-zero scalar.")
        return Vector3D(self.dx / scalar, self.dy / scalar, self.dz / scalar)

    def __neg__(self) -> Vector3D:
        """Negates vector coordinates."""
        return Vector3D(-self.dx, -self.dy, -self.dz)

    def to_numpy(self) -> np.ndarray:
        """Converts vector to 1D NumPy float64 array."""
        return np.array([self.dx, self.dy, self.dz], dtype=np.float64)

    def __repr__(self) -> str:
        return f"Vector3D({self.dx:.4f}, {self.dy:.4f}, {self.dz:.4f})"
