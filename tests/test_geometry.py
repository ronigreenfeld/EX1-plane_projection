"""Comprehensive unit tests for 3D geometric primitives and plane models."""

import math
import unittest
import numpy as np
from src.geometry.point import Point3D
from src.geometry.vector import Vector3D
from src.geometry.plane import (
    IsoscelesTrianglePlane,
    IsoscelesTrapezoidPlane,
)
from src.utils.exceptions import GeometryValidationError, CoplanarityError


class TestGeometryPrimitives(unittest.TestCase):
    """Test suite for Point3D and Vector3D arithmetic and operators."""

    def test_point_distance(self):
        p1 = Point3D(0.0, 0.0, 0.0)
        p2 = Point3D(3.0, 4.0, 0.0)
        self.assertAlmostEqual(p1.distance_to(p2), 5.0)

    def test_point_subtraction_operator(self):
        p1 = Point3D(1.0, 2.0, 3.0)
        p2 = Point3D(4.0, 6.0, 8.0)
        v = p2 - p1
        self.assertIsInstance(v, Vector3D)
        self.assertAlmostEqual(v.dx, 3.0)
        self.assertAlmostEqual(v.dy, 4.0)
        self.assertAlmostEqual(v.dz, 5.0)

    def test_point_vector_addition_operator(self):
        p = Point3D(10.0, 20.0, 30.0)
        v = Vector3D(1.0, -2.0, 5.0)
        p_res = p + v
        self.assertIsInstance(p_res, Point3D)
        self.assertAlmostEqual(p_res.x, 11.0)
        self.assertAlmostEqual(p_res.y, 18.0)
        self.assertAlmostEqual(p_res.z, 35.0)

    def test_vector_algebra(self):
        v1 = Vector3D(1.0, 0.0, 0.0)
        v2 = Vector3D(0.0, 1.0, 0.0)

        # Dot product of perpendicular vectors
        self.assertAlmostEqual(v1.dot(v2), 0.0)

        # Cross product (x cross y = z)
        v_cross = v1.cross(v2)
        self.assertAlmostEqual(v_cross.dx, 0.0)
        self.assertAlmostEqual(v_cross.dy, 0.0)
        self.assertAlmostEqual(v_cross.dz, 1.0)

        # Length and normalize
        v3 = Vector3D(0.0, 3.0, 4.0)
        self.assertAlmostEqual(v3.length(), 5.0)
        v3_unit = v3.normalize()
        self.assertAlmostEqual(v3_unit.length(), 1.0)
        self.assertAlmostEqual(v3_unit.dy, 0.6)
        self.assertAlmostEqual(v3_unit.dz, 0.8)

        # Scalar operations
        v_scaled = v3 * 2.0
        self.assertAlmostEqual(v_scaled.dy, 6.0)
        v_div = v3 / 2.0
        self.assertAlmostEqual(v_div.dz, 2.0)
        v_neg = -v3
        self.assertAlmostEqual(v_neg.dy, -3.0)

    def test_vector_degenerate_normalization(self):
        zero_v = Vector3D(0.0, 0.0, 0.0)
        with self.assertRaises(GeometryValidationError):
            zero_v.normalize()


class TestPlanarGeometries(unittest.TestCase):
    """Test suite for triangle and trapezoid validation and scanline endpoints."""

    def test_valid_isosceles_triangle(self):
        # Isosceles triangle with apex at origin and symmetrical base in XY plane
        # dist(a, b) = 5.0, dist(a, c) = 5.0, dist(b, c) = 6.0
        a = Point3D(0.0, 0.0, 0.0)
        b = Point3D(-3.0, 4.0, 0.0)
        c = Point3D(3.0, 4.0, 0.0)

        triangle = IsoscelesTrianglePlane(a, b, c)
        self.assertTrue(triangle.validate())
        self.assertTrue(triangle.is_valid)

        height, width = triangle.get_dimensions()
        self.assertEqual(height, 5)
        self.assertEqual(width, 6)

        # At y=0, both endpoints must start at apex a
        p_start, p_end = triangle.get_scanline_endpoints(0)
        self.assertAlmostEqual(p_start.distance_to(a), 0.0)
        self.assertAlmostEqual(p_end.distance_to(a), 0.0)

    def test_invalid_triangle_non_isosceles(self):
        a = Point3D(0.0, 0.0, 0.0)
        b = Point3D(0.0, 5.0, 0.0)  # dist(a,b) = 5.0
        c = Point3D(0.0, 0.0, 6.0)  # dist(a,c) = 6.0

        triangle = IsoscelesTrianglePlane(a, b, c)
        self.assertFalse(triangle.is_valid)
        with self.assertRaises(GeometryValidationError):
            triangle.validate()

    def test_valid_isosceles_trapezoid(self):
        # Symmetric trapezoid in XY plane:
        # Top base: (-1, 0, 0) to (1, 0, 0) -> width = 2
        # Bottom base: (-3, 4, 0) to (3, 4, 0) -> width = 6
        # Legs: (-1,0,0) to (-3,4,0) -> dist = sqrt(2^2 + 4^2) = sqrt(20) ~ 4.472
        #       (1,0,0) to (3,4,0) -> dist = sqrt(2^2 + 4^2) = sqrt(20) ~ 4.472
        a1 = Point3D(-1.0, 0.0, 0.0)
        a2 = Point3D(1.0, 0.0, 0.0)
        b = Point3D(-3.0, 4.0, 0.0)
        c = Point3D(3.0, 4.0, 0.0)

        trapezoid = IsoscelesTrapezoidPlane(a1, a2, b, c)
        self.assertTrue(trapezoid.validate())
        self.assertTrue(trapezoid.is_valid)

        height, width = trapezoid.get_dimensions()
        self.assertEqual(height, math.ceil(math.sqrt(20)))
        self.assertEqual(width, 6)

        # At y=0, endpoints must match top base vertices a1 and a2
        p_start, p_end = trapezoid.get_scanline_endpoints(0)
        self.assertAlmostEqual(p_start.distance_to(a1), 0.0)
        self.assertAlmostEqual(p_end.distance_to(a2), 0.0)

    def test_invalid_trapezoid_non_coplanar(self):
        # 4 vertices where legs are equal in length, but the quad is skewed in 3D (non-coplanar)
        # dist(a1,b) = sqrt(2^2 + 4^2 + 2^2) = sqrt(24)
        # dist(a2,c) = sqrt(2^2 + 4^2 + 2^2) = sqrt(24)
        a1 = Point3D(-1.0, 0.0, 1.0)
        a2 = Point3D(1.0, 0.0, -1.0)
        b = Point3D(-3.0, 4.0, -1.0)
        c = Point3D(3.0, 4.0, 1.0)

        trapezoid = IsoscelesTrapezoidPlane(a1, a2, b, c)
        self.assertFalse(trapezoid.is_valid)
        with self.assertRaises(CoplanarityError) as ctx:
            trapezoid.validate()
        self.assertGreater(ctx.exception.triple_product, 0.001)

    def test_invalid_trapezoid_top_exceeds_bottom(self):
        # Top base is wider than bottom base
        a1 = Point3D(-5.0, 0.0, 0.0)
        a2 = Point3D(5.0, 0.0, 0.0)  # Top base width = 10
        b = Point3D(-2.0, 4.0, 0.0)
        c = Point3D(2.0, 4.0, 0.0)   # Bottom base width = 4

        trapezoid = IsoscelesTrapezoidPlane(a1, a2, b, c)
        self.assertFalse(trapezoid.is_valid)
        with self.assertRaises(GeometryValidationError):
            trapezoid.validate()


if __name__ == "__main__":
    unittest.main()
