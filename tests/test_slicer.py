"""Comprehensive tests and FPS benchmarks for the vectorized ProjectionEngine."""

import math
import time
import unittest
import numpy as np
from src.geometry.point import Point3D
from src.geometry.plane import IsoscelesTrianglePlane, IsoscelesTrapezoidPlane
from src.io.nrrd_loader import NRRDVolume
from src.engine.slicer import ProjectionEngine
from src.utils.synthetic_data import create_synthetic_sphere_volume, create_benchmark_volume


class TestProjectionEngine(unittest.TestCase):
    """Test suite for planar slicing accuracy, boundary handling, and performance."""

    @classmethod
    def setUpClass(cls):
        # 100^3 sphere volume with radius 30 centered at (50, 50, 50)
        cls.sphere_data = create_synthetic_sphere_volume(shape=(100, 100, 100), radius=30.0)
        cls.sphere_volume = NRRDVolume(cls.sphere_data)
        cls.engine = ProjectionEngine(cls.sphere_volume)

    def test_sphere_equatorial_slice_accuracy(self):
        """A plane slicing through the center of the sphere yields an analytical circle of radius 30."""
        # Isosceles triangle plane aligned with XY at z=50 (equator of the sphere)
        # Apex a at (50, 10, 50), legs reaching to (10, 90, 50) and (90, 90, 50)
        # dist(a, b) = sqrt((-40)^2 + 80^2) = sqrt(8000) ~ 89.44
        # dist(a, c) = sqrt(40^2 + 80^2) = sqrt(8000) ~ 89.44
        # dist(b, c) = 80.0
        a = Point3D(50.0, 10.0, 50.0)
        b = Point3D(10.0, 90.0, 50.0)
        c = Point3D(90.0, 90.0, 50.0)

        plane = IsoscelesTrianglePlane(a, b, c)
        slice_img = self.engine.slice_plane(plane)

        self.assertGreater(slice_img.shape[0], 0)
        self.assertGreater(slice_img.shape[1], 0)

        # Non-zero voxels must exist (the sphere intersection)
        non_zeros = np.count_nonzero(slice_img == 255)
        self.assertGreater(non_zeros, 500)

        # Background corners must remain zero (black)
        self.assertEqual(slice_img[0, 0], 0)
        self.assertEqual(slice_img[0, -1], 0)

    def test_invalid_plane_returns_zeros(self):
        """Invalid planes must return a zero-filled array without raising unhandled exceptions."""
        # Non-isosceles triangle: dist(a,b) != dist(a,c)
        a = Point3D(0.0, 0.0, 0.0)
        b = Point3D(0.0, 50.0, 0.0)
        c = Point3D(0.0, 0.0, 80.0)

        invalid_plane = IsoscelesTrianglePlane(a, b, c)
        slice_img = self.engine.slice_plane(invalid_plane)

        self.assertIsInstance(slice_img, np.ndarray)
        self.assertEqual(np.count_nonzero(slice_img), 0)

    def test_oob_plane_returns_zeros(self):
        """A plane placed entirely outside the volume boundaries yields all zeros."""
        a = Point3D(5000.0, 5000.0, 5000.0)
        b = Point3D(4970.0, 5040.0, 5000.0)
        c = Point3D(5030.0, 5040.0, 5000.0)

        plane = IsoscelesTrianglePlane(a, b, c)
        slice_img = self.engine.slice_plane(plane)
        self.assertEqual(np.count_nonzero(slice_img), 0)

    def test_absolute_negative_oob(self):
        """A plane placed strictly in negative coordinates (e.g., x in [-100, -10])
        must return a zero-filled black matrix without Python negative index wrapping.
        """
        # Valid isosceles triangle with all coordinates strictly negative
        # Apex a at (-50, -50, -50), legs to (-90, -10, -50) and (-10, -10, -50)
        # dist(a, b) = sqrt(40^2 + 40^2) = sqrt(3200) ~ 56.57
        # dist(a, c) = sqrt(40^2 + 40^2) = sqrt(3200) ~ 56.57
        # dist(b, c) = 80.0
        a = Point3D(-50.0, -50.0, -50.0)
        b = Point3D(-90.0, -10.0, -50.0)
        c = Point3D(-10.0, -10.0, -50.0)

        plane = IsoscelesTrianglePlane(a, b, c)
        self.assertTrue(plane.is_valid)

        slice_img = self.engine.slice_plane(plane)
        d_h, d_w = plane.get_dimensions()

        self.assertIsInstance(slice_img, np.ndarray)
        self.assertEqual(slice_img.shape, (d_h, d_w))
        self.assertEqual(np.count_nonzero(slice_img), 0)

    def test_trapezoid_slice(self):
        """Verify that trapezoid slicing works with correct dimensions."""
        a1 = Point3D(30.0, 20.0, 50.0)
        a2 = Point3D(70.0, 20.0, 50.0)
        b = Point3D(10.0, 80.0, 50.0)
        c = Point3D(90.0, 80.0, 50.0)

        trapezoid = IsoscelesTrapezoidPlane(a1, a2, b, c)
        slice_img = self.engine.slice_plane(trapezoid)

        d_h, d_w = trapezoid.get_dimensions()
        self.assertEqual(slice_img.shape, (d_h, d_w))
        self.assertGreater(np.count_nonzero(slice_img), 0)

    def test_intensity_normalization(self):
        """Verifies normalization to uint8 [0, 255]."""
        int16_frame = np.array([[0, 100], [200, 300]], dtype=np.int16)
        normalized = ProjectionEngine.normalize_frame_to_uint8(int16_frame)

        self.assertEqual(normalized.dtype, np.uint8)
        self.assertEqual(normalized[0, 0], 0)
        self.assertEqual(normalized[1, 1], 255)

    def test_fps_throughput_benchmark_on_500_cube(self):
        """Assignment NFR-1 Benchmark: Throughput on 500^3 volume must exceed 30+ FPS."""
        # Generate 500^3 volume in memory
        bench_data = create_benchmark_volume((500, 500, 500))
        bench_volume = NRRDVolume(bench_data)
        engine = ProjectionEngine(bench_volume)

        # Full-sized 500x500 isosceles triangle plane with exact leg equality:
        # dist(a,b) = sqrt(250^2 + 500^2) == dist(a,c) = sqrt(250^2 + 500^2)
        a = Point3D(250.0, 0.0, 250.0)
        b = Point3D(0.0, 500.0, 250.0)
        c = Point3D(500.0, 500.0, 250.0)
        plane = IsoscelesTrianglePlane(a, b, c)

        # Warm-up run
        _ = engine.slice_plane(plane)

        # Benchmark 20 consecutive full-sized slices
        num_frames = 20
        start_time = time.perf_counter()
        for _ in range(num_frames):
            _ = engine.slice_plane(plane)
        elapsed = time.perf_counter() - start_time

        fps = num_frames / elapsed
        print(f"\n[BENCHMARK RESULT] 500^3 Volume Throughput: {fps:.2f} FPS ({elapsed*1000/num_frames:.2f} ms/frame)")

        # Verify strict compliance with assignment threshold: >= 30 FPS
        self.assertGreaterEqual(fps, 30.0, f"Performance ({fps:.2f} FPS) below required 30 FPS")


if __name__ == "__main__":
    unittest.main()
