"""CSV parsing for cutting plane coordinate definitions (3 points or 4 points)."""

import csv
import os
import re
from typing import Iterator
from src.geometry.point import Point3D
from src.geometry.plane import (
    PlaneGeometry,
    IsoscelesTrianglePlane,
    IsoscelesTrapezoidPlane,
)
from src.utils.exceptions import CSVFormatError
from src.utils.logger import setup_logger

logger = setup_logger("csv_parser")


class CSVPlaneParser:
    """Parses sequential plane specifications from CSV files according to SRS FR-2."""

    @staticmethod
    def parse_line(raw_line: str, line_number: int = 1) -> PlaneGeometry | None:
        """Parses a single CSV line into a PlaneGeometry instance.

        Args:
            raw_line: String line from the CSV file.
            line_number: Line index for diagnostic reporting.

        Returns:
            PlaneGeometry instance (Triangle or Trapezoid), or None if line is blank/comment.

        Raises:
            CSVFormatError: If column count is invalid or tokens cannot be parsed as floats.
        """
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            return None

        # Split on commas, semicolons, or whitespace delimiters
        tokens = [t for t in re.split(r"[,;\s]+", stripped) if t]

        try:
            coords = [float(t) for t in tokens]
        except ValueError as err:
            raise CSVFormatError(
                f"Line {line_number}: Non-numeric coordinate value encountered in '{raw_line}'",
                line_number=line_number
            ) from err

        count = len(coords)

        if count == 9:
            # 3 points: a(x, y, z), b(x, y, z), c(x, y, z)
            a = Point3D(coords[0], coords[1], coords[2])
            b = Point3D(coords[3], coords[4], coords[5])
            c = Point3D(coords[6], coords[7], coords[8])
            return IsoscelesTrianglePlane(a, b, c)

        elif count == 12:
            # 4 points: a1(x, y, z), a2(x, y, z), b(x, y, z), c(x, y, z)
            a1 = Point3D(coords[0], coords[1], coords[2])
            a2 = Point3D(coords[3], coords[4], coords[5])
            b = Point3D(coords[6], coords[7], coords[8])
            c = Point3D(coords[9], coords[10], coords[11])
            return IsoscelesTrapezoidPlane(a1, a2, b, c)

        else:
            raise CSVFormatError(
                f"Line {line_number}: Expected 9 values (triangle) or 12 values (trapezoid), got {count}.",
                line_number=line_number
            )

    @classmethod
    def parse_file(cls, filepath: str) -> list[PlaneGeometry]:
        """Parses an entire CSV file into a list of cutting planes.

        Args:
            filepath: Path to the plane definition CSV file.

        Returns:
            List of parsed PlaneGeometry objects.

        Raises:
            CSVFormatError: If file is missing, empty, or contains malformed lines.
        """
        if not os.path.exists(filepath):
            raise CSVFormatError(f"CSV file not found: '{filepath}'")

        planes: list[PlaneGeometry] = []
        with open(filepath, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f, start=1):
                plane = cls.parse_line(line, line_number=idx)
                if plane is not None:
                    planes.append(plane)

        if not planes:
            logger.warning("Parsed CSV file '%s' contains 0 valid plane definitions.", filepath)

        return planes

    @classmethod
    def iter_planes(cls, filepath: str) -> Iterator[PlaneGeometry]:
        """Streams plane definitions lazily from disk line-by-line."""
        if not os.path.exists(filepath):
            raise CSVFormatError(f"CSV file not found: '{filepath}'")

        with open(filepath, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f, start=1):
                plane = cls.parse_line(line, line_number=idx)
                if plane is not None:
                    yield plane
