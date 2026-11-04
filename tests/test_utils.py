"""Unit tests for configuration, exceptions, and logging utilities."""

import unittest
from src.utils.config import Settings
from src.utils.exceptions import (
    ProjectionError,
    GeometryValidationError,
    CoplanarityError,
    VolumeIOError,
    VideoEncodingError,
    CSVFormatError,
)
from src.utils.logger import setup_logger


class TestUtils(unittest.TestCase):
    """Test suite for utilities and baseline configuration."""

    def test_settings_immutability_and_values(self):
        """Verify that Settings constants match SRS and cannot be overwritten."""
        self.assertEqual(Settings.GEOMETRY_EPSILON, 0.001)
        self.assertEqual(Settings.DEFAULT_VIDEO_FPS, 30)
        self.assertEqual(Settings.DEFAULT_FOURCC, "mp4v")
        self.assertEqual(Settings.TARGET_MIN_FPS, 30.0)
        self.assertEqual(Settings.TARGET_EXPECTED_FPS, 100.0)

        with self.assertRaises(Exception):
            # Dataclass is frozen; mutating should raise an error
            Settings.GEOMETRY_EPSILON = 0.05  # type: ignore

    def test_exception_inheritance_hierarchy(self):
        """Verify that all domain exceptions properly inherit from ProjectionError."""
        self.assertTrue(issubclass(GeometryValidationError, ProjectionError))
        self.assertTrue(issubclass(CoplanarityError, GeometryValidationError))
        self.assertTrue(issubclass(VolumeIOError, ProjectionError))
        self.assertTrue(issubclass(VideoEncodingError, ProjectionError))
        self.assertTrue(issubclass(CSVFormatError, ProjectionError))

        # Test instantiation and details preservation
        coplanar_err = CoplanarityError("Points not coplanar", triple_product=0.045)
        self.assertEqual(coplanar_err.triple_product, 0.045)
        self.assertEqual(coplanar_err.details["scalar_triple_product"], 0.045)

    def test_logger_setup(self):
        """Verify logger instantiation and handler registration."""
        logger = setup_logger("test_logger")
        self.assertIsNotNone(logger)
        self.assertTrue(len(logger.handlers) >= 1)


if __name__ == "__main__":
    unittest.main()
