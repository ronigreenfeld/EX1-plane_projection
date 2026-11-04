"""Planar geometry abstractions and concrete triangle/trapezoid representations."""

from __future__ import annotations
import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from src.geometry.point import Point3D
from src.geometry.vector import Vector3D
from src.utils.config import Settings
from src.utils.exceptions import GeometryValidationError, CoplanarityError


class PlaneGeometry(ABC):
    """Abstract Base Class defining the cutting plane contract."""

    @abstractmethod
    def validate(self) -> bool:
        """Validates geometric constraints according to SRS tolerances.

        Returns:
            True if geometry meets all constraints.

        Raises:
            GeometryValidationError or CoplanarityError if constraints are violated.
        """
        pass

    @property
    def is_valid(self) -> bool:
        """Convenience property safely checking validity without raising exceptions."""
        try:
            return self.validate()
        except GeometryValidationError:
            return False

    @abstractmethod
    def get_dimensions(self) -> tuple[int, int]:
        """Calculates pixel dimensions (D_height, D_width) for the unpadded output matrix.

        Returns:
            tuple of (D_height, D_width) as integers.
        """
        pass

    @abstractmethod
    def get_scanline_endpoints(self, y: int) -> tuple[Point3D, Point3D]:
        """Computes continuous 3D spatial endpoints for a given discrete scanline row y.

        Args:
            y: Scanline row index in range [0, D_height - 1].

        Returns:
            tuple of (p_start, p_end) 3D points.
        """
        pass


@dataclass(frozen=True)
class IsoscelesTrianglePlane(PlaneGeometry):
    """Cutting plane defined by 3 vertices (a, b, c) forming an isosceles triangle."""

    a: Point3D
    b: Point3D
    c: Point3D

    def validate(self) -> bool:
        d_ab = self.a.distance_to(self.b)
        d_ac = self.a.distance_to(self.c)
        d_bc = self.b.distance_to(self.c)

        # Degeneracy check
        if d_ab < Settings.GEOMETRY_EPSILON or d_bc < Settings.GEOMETRY_EPSILON:
            raise GeometryValidationError(
                f"Degenerate triangle: side lengths too small (dist(a,b)={d_ab:.6f}, dist(b,c)={d_bc:.6f})"
            )

        # Isosceles leg equality check: |dist(a,b) - dist(a,c)| < EPS
        leg_diff = abs(d_ab - d_ac)
        if leg_diff >= Settings.GEOMETRY_EPSILON:
            raise GeometryValidationError(
                f"Triangle is not isosceles: |dist(a,b) - dist(a,c)| = {leg_diff:.6f} >= {Settings.GEOMETRY_EPSILON}",
                details={"dist_ab": d_ab, "dist_ac": d_ac, "diff": leg_diff}
            )

        return True

    def get_dimensions(self) -> tuple[int, int]:
        d_ab = self.a.distance_to(self.b)
        d_bc = self.b.distance_to(self.c)
        return math.ceil(d_ab), math.ceil(d_bc)

    def get_scanline_endpoints(self, y: int) -> tuple[Point3D, Point3D]:
        d_ab = self.a.distance_to(self.b)
        d_ac = self.a.distance_to(self.c)
        v_ab = (self.b - self.a).normalize()
        v_ac = (self.c - self.a).normalize()

        p_start = self.a + (v_ab * float(y))
        p_end = self.a + (v_ac * float(y))
        return p_start, p_end


@dataclass(frozen=True)
class IsoscelesTrapezoidPlane(PlaneGeometry):
    """Cutting plane defined by 4 coplanar vertices (a1, a2, b, c) forming an isosceles trapezoid."""

    a1: Point3D
    a2: Point3D
    b: Point3D
    c: Point3D

    def validate(self) -> bool:
        d_a1b = self.a1.distance_to(self.b)
        d_a2c = self.a2.distance_to(self.c)
        d_a1a2 = self.a1.distance_to(self.a2)
        d_bc = self.b.distance_to(self.c)

        # Degeneracy check
        if d_a1b < Settings.GEOMETRY_EPSILON or d_bc < Settings.GEOMETRY_EPSILON:
            raise GeometryValidationError(
                f"Degenerate trapezoid: side lengths too small (dist(a1,b)={d_a1b:.6f}, dist(b,c)={d_bc:.6f})"
            )

        # 1. Leg equality check: |dist(a1,b) - dist(a2,c)| < EPS
        leg_diff = abs(d_a1b - d_a2c)
        if leg_diff >= Settings.GEOMETRY_EPSILON:
            raise GeometryValidationError(
                f"Trapezoid legs not equal: |dist(a1,b) - dist(a2,c)| = {leg_diff:.6f} >= {Settings.GEOMETRY_EPSILON}",
                details={"dist_a1b": d_a1b, "dist_a2c": d_a2c, "diff": leg_diff}
            )

        # 2. Width inequality: dist(a1, a2) <= dist(b, c) + EPS
        if d_a1a2 > d_bc + Settings.GEOMETRY_EPSILON:
            raise GeometryValidationError(
                f"Trapezoid top base exceeds bottom base: dist(a1,a2)={d_a1a2:.4f} > dist(b,c)={d_bc:.4f}",
                details={"dist_a1a2": d_a1a2, "dist_bc": d_bc}
            )

        # 3. Coplanarity check via Scalar Triple Product: |(v1 x v2) . v3| < EPS
        v1 = self.a2 - self.a1
        v2 = self.b - self.a1
        v3 = self.c - self.a1
        triple_product = abs(v1.cross(v2).dot(v3))

        if triple_product >= Settings.GEOMETRY_EPSILON:
            raise CoplanarityError(
                f"Trapezoid vertices are not coplanar: triple product = {triple_product:.6f} >= {Settings.GEOMETRY_EPSILON}",
                triple_product=triple_product
            )

        return True

    def get_dimensions(self) -> tuple[int, int]:
        d_a1b = self.a1.distance_to(self.b)
        d_bc = self.b.distance_to(self.c)
        return math.ceil(d_a1b), math.ceil(d_bc)

    def get_scanline_endpoints(self, y: int) -> tuple[Point3D, Point3D]:
        v_a1b = (self.b - self.a1).normalize()
        v_a2c = (self.c - self.a2).normalize()

        p_start = self.a1 + (v_a1b * float(y))
        p_end = self.a2 + (v_a2c * float(y))
        return p_start, p_end
