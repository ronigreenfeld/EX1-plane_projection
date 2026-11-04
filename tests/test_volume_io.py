"""Unit tests for NRRDVolume ingestion and CSVPlaneParser."""

import os
import tempfile
import unittest
import numpy as np
from src.geometry.plane import IsoscelesTrianglePlane, IsoscelesTrapezoidPlane, InvalidPlane
from src.io.nrrd_loader import NRRDVolume
from src.io.csv_parser import CSVPlaneParser
from src.utils.exceptions import VolumeIOError, CSVFormatError, CoplanarityError


class TestNRRDVolume(unittest.TestCase):
    """Test suite for NRRD volume loading, validation, and vectorized sampling."""

    def setUp(self):
        self.test_data = np.zeros((10, 20, 30), dtype=np.uint8)
        self.test_data[5, 10, 15] = 42

    def test_volume_shape_and_dtype(self):
        volume = NRRDVolume(self.test_data)
        self.assertEqual(volume.shape, (10, 20, 30))
        self.assertEqual(volume.dtype, np.uint8)

    def test_rejection_of_non_3d_volume(self):
        array_2d = np.zeros((50, 50), dtype=np.uint8)
        with self.assertRaises(VolumeIOError):
            NRRDVolume(array_2d)

        array_4d = np.zeros((10, 10, 10, 3), dtype=np.uint8)
        with self.assertRaises(VolumeIOError):
            NRRDVolume(array_4d)

    def test_volume_max_dimension_rejection(self):
        """FR-1: Dimensions must satisfy 1 <= dim < 1024 (2^10). Violations must raise VolumeIOError."""
        # dim >= 1024 on x-axis
        oversized_x = np.zeros((1024, 10, 10), dtype=np.uint8)
        with self.assertRaises(VolumeIOError):
            NRRDVolume(oversized_x)

        # dim >= 1024 on y-axis
        oversized_y = np.zeros((10, 1024, 10), dtype=np.uint8)
        with self.assertRaises(VolumeIOError):
            NRRDVolume(oversized_y)

        # dim >= 1024 on z-axis
        oversized_z = np.zeros((10, 10, 1024), dtype=np.uint8)
        with self.assertRaises(VolumeIOError):
            NRRDVolume(oversized_z)

        # dim < 1 (zero dimension)
        zero_dim = np.zeros((0, 10, 10), dtype=np.uint8)
        with self.assertRaises(VolumeIOError):
            NRRDVolume(zero_dim)

    def test_vectorized_sampling_and_oob(self):
        volume = NRRDVolume(self.test_data)
        x_idx = np.array([-1, 5, 100, 5], dtype=np.int32)
        y_idx = np.array([0, 10, 10, -5], dtype=np.int32)
        z_idx = np.array([0, 15, 0, 15], dtype=np.int32)

        samples = volume.sample_voxels_vectorized(x_idx, y_idx, z_idx)
        self.assertEqual(samples[0], 0)   # x < 0 -> OOB 0
        self.assertEqual(samples[1], 42)  # In-bounds match
        self.assertEqual(samples[2], 0)   # x >= sx -> OOB 0
        self.assertEqual(samples[3], 0)   # y < 0 -> OOB 0

    def test_load_real_mrhead_volume(self):
        mrhead_path = "data/real/volumes/MRHead_1.nrrd"
        if not os.path.exists(mrhead_path):
            mrhead_path = "data/real/MRHead_1.nrrd"
        if os.path.exists(mrhead_path):
            volume = NRRDVolume.load(mrhead_path)
            self.assertEqual(volume.shape, (256, 256, 130))
            self.assertEqual(volume.dtype, np.int16)


class TestCSVPlaneParser(unittest.TestCase):
    """Test suite for CSV parsing of triangles and trapezoids."""

    def test_parse_triangle_line(self):
        line = "0.0, 0.0, 0.0, -3.0, 4.0, 0.0, 3.0, 4.0, 0.0"
        plane = CSVPlaneParser.parse_line(line)
        self.assertIsInstance(plane, IsoscelesTrianglePlane)
        self.assertTrue(plane.is_valid)

    def test_parse_trapezoid_line(self):
        line = "-1.0 0.0 0.0   1.0 0.0 0.0   -3.0 4.0 0.0   3.0 4.0 0.0"
        plane = CSVPlaneParser.parse_line(line)
        self.assertIsInstance(plane, IsoscelesTrapezoidPlane)
        self.assertTrue(plane.is_valid)

    def test_parse_blank_and_comment(self):
        self.assertIsNone(CSVPlaneParser.parse_line(""))
        self.assertIsNone(CSVPlaneParser.parse_line("   "))
        self.assertIsNone(CSVPlaneParser.parse_line("# Header comment"))

    def test_parse_invalid_count(self):
        # 8 coordinates instead of 9 or 12
        line = "1, 2, 3, 4, 5, 6, 7, 8"
        with self.assertRaises(CSVFormatError):
            CSVPlaneParser.parse_line(line)

    def test_parse_non_numeric(self):
        line = "1, 2, three, 4, 5, 6, 7, 8, 9"
        with self.assertRaises(CSVFormatError):
            CSVPlaneParser.parse_line(line)

    def test_parse_file(self):
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".csv") as f:
            f.write("# Cutting planes\n")
            f.write("0.0, 0.0, 0.0, -3.0, 4.0, 0.0, 3.0, 4.0, 0.0\n")
            f.write("\n")
            f.write("-1.0, 0.0, 0.0, 1.0, 0.0, 0.0, -3.0, 4.0, 0.0, 3.0, 4.0, 0.0\n")
            tmp_path = f.name

        try:
            planes = CSVPlaneParser.parse_file(tmp_path)
            self.assertEqual(len(planes), 2)
            self.assertIsInstance(planes[0], IsoscelesTrianglePlane)
            self.assertIsInstance(planes[1], IsoscelesTrapezoidPlane)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_parse_coplanarity_error(self):
        """Negative test: Non-coplanar trapezoid line must be detected and handled."""
        # 12 coordinates forming a trapezoid where points are non-coplanar:
        # a1=(-1, 0, 1), a2=(1, 0, -1), b=(-3, 4, -1), c=(3, 4, 1)
        # Legs are equal: dist(a1,b) = sqrt(24) == dist(a2,c) = sqrt(24), but z coordinates tilt out of plane
        non_coplanar_line = "-1.0, 0.0, 1.0, 1.0, 0.0, -1.0, -3.0, 4.0, -1.0, 3.0, 4.0, 1.0"

        # 1. Calling parse_line with validate_geometry=True must raise CoplanarityError
        with self.assertRaises(CoplanarityError):
            CSVPlaneParser.parse_line(non_coplanar_line, validate_geometry=True)

        # 2. Calling parse_line without validation returns plane, but calling validate() raises CoplanarityError
        plane = CSVPlaneParser.parse_line(non_coplanar_line)
        self.assertFalse(plane.is_valid)
        with self.assertRaises(CoplanarityError):
            plane.validate()

        # 3. File parsing: with tolerate_errors=True, recovers with an InvalidPlane (FR-24)
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".csv") as f:
            f.write(non_coplanar_line + "\n")
            tmp_path = f.name

        try:
            # When tolerate_errors=False and validate_geometry=True: raises CoplanarityError
            with self.assertRaises(CoplanarityError):
                CSVPlaneParser.parse_file(tmp_path, tolerate_errors=False, validate_geometry=True)

            # When tolerate_errors=True: gracefully outputs InvalidPlane
            planes = CSVPlaneParser.parse_file(tmp_path, tolerate_errors=True, validate_geometry=True)
            self.assertEqual(len(planes), 1)
            self.assertIsInstance(planes[0], InvalidPlane)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


if __name__ == "__main__":
    unittest.main()

