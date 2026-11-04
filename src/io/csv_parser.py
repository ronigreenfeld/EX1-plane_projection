"""CSV parsing for cutting plane coordinate definitions (3 points or 4 points)."""

import os
import re
from typing import Iterator
from src.geometry.point import Point3D
from src.geometry.plane import (
    PlaneGeometry,
    IsoscelesTrianglePlane,
    IsoscelesTrapezoidPlane,
    InvalidPlane,
)
from src.utils.config import Settings
from src.utils.exceptions import CSVFormatError
from src.utils.logger import setup_logger

logger = setup_logger("csv_parser")


class CSVPlaneParser:
    """Parses sequential plane specifications from CSV files according to SRS FR-2 and lecturer format."""

    @staticmethod
    def parse_line(raw_line: str, line_number: int = 1) -> PlaneGeometry | None:
        """Parses a single CSV line into a PlaneGeometry instance.

        Supports both:
        - Pure coordinate rows (9 coords for triangle, 12 coords for trapezoid).
        - Lecturer format with leading count column and optional header:
          '3, x1, y1, z1, x2, y2, z2, x3, y3, z3, , ,'
          '4, x1, y1, z1, x2, y2, z2, x3, y3, z3, x4, y4, z4'

        Args:
            raw_line: String line from the CSV file.
            line_number: Line index for diagnostic reporting.

        Returns:
            PlaneGeometry instance (Triangle or Trapezoid), or None if line is blank/comment/header.

        Raises:
            CSVFormatError: If column count is invalid or tokens cannot be parsed as floats.
        """
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            return None

        # Check for header line
        if "number of points" in stripped.lower() or "x1" in stripped.lower():
            logger.info("Skipping CSV header at line %d", line_number)
            return None

        # Split on commas, semicolons, or whitespace delimiters
        raw_tokens = [t.strip() for t in re.split(r"[,;\s]+", stripped) if t.strip()]

        if not raw_tokens:
            return None

        # Determine if first token is the point count (3 or 4)
        has_leading_count = raw_tokens[0] in ("3", "4") and len(raw_tokens) > 1

        if has_leading_count:
            pt_count = int(raw_tokens[0])
            coord_tokens = raw_tokens[1:]
        else:
            pt_count = None
            coord_tokens = raw_tokens

        try:
            coords = [float(t) for t in coord_tokens]
        except ValueError as err:
            raise CSVFormatError(
                f"Line {line_number}: Non-numeric coordinate value encountered in '{raw_line}'",
                line_number=line_number
            ) from err

        num_coords = len(coords)

        if pt_count == 3 or (pt_count is None and num_coords == 9):
            if len(coords) < 9:
                raise CSVFormatError(f"Line {line_number}: Expected at least 9 coordinates for triangle, got {len(coords)}")
            # Triangle: a, b, c
            a = Point3D(coords[0], coords[1], coords[2])
            b = Point3D(coords[3], coords[4], coords[5])
            c = Point3D(coords[6], coords[7], coords[8])
            return IsoscelesTrianglePlane(a, b, c)

        elif pt_count == 4 or (pt_count is None and num_coords == 12):
            if len(coords) < 12:
                raise CSVFormatError(f"Line {line_number}: Expected at least 12 coordinates for trapezoid, got {len(coords)}")

            p1 = Point3D(coords[0], coords[1], coords[2])
            p2 = Point3D(coords[3], coords[4], coords[5])
            p3 = Point3D(coords[6], coords[7], coords[8])
            p4 = Point3D(coords[9], coords[10], coords[11])

            # In lecturer's CSV: points are given as (a', b, a'', c)
            # where dist(p1, p2) == dist(p3, p4) represents the equal legs a'->b and a''->c.
            # In standard notation: points are given as (a1, a2, b, c).
            # Auto-detect which ordering satisfies equal leg geometry:
            diff_p1p2_p3p4 = abs(p1.distance_to(p2) - p3.distance_to(p4))
            diff_p1p3_p2p4 = abs(p1.distance_to(p3) - p2.distance_to(p4))

            if diff_p1p2_p3p4 <= diff_p1p3_p2p4:
                # Lecturer's ordering: (a1, b, a2, c)
                a1, b, a2, c = p1, p2, p3, p4
            else:
                # Alternative ordering: (a1, a2, b, c)
                a1, a2, b, c = p1, p2, p3, p4

            return IsoscelesTrapezoidPlane(a1, a2, b, c)

        else:
            raise CSVFormatError(
                f"Line {line_number}: Unrecognized format with {len(coords)} coordinates "
                f"(expected 9 for triangle or 12 for trapezoid).",
                line_number=line_number
            )

    @classmethod
    def parse_file(cls, filepath: str, tolerate_errors: bool = True) -> list[PlaneGeometry]:
        """Parses an entire CSV file into a list of cutting planes.

        Args:
            filepath: Path to the plane definition CSV file.
            tolerate_errors: If True (default, per FR-24), malformed lines log a warning
                and append an InvalidPlane instance to render a black frame without crashing.
                If False, raises CSVFormatError.

        Returns:
            List of parsed PlaneGeometry objects.
        """
        if not os.path.exists(filepath):
            raise CSVFormatError(f"CSV file not found: '{filepath}'")

        planes: list[PlaneGeometry] = []
        with open(filepath, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f, start=1):
                try:
                    plane = cls.parse_line(line, line_number=idx)
                    if plane is not None:
                        planes.append(plane)
                except Exception as err:
                    if tolerate_errors:
                        logger.warning(
                            "Line %d in '%s': %s (generating black frame per FR-24)",
                            idx, filepath, err
                        )
                        planes.append(InvalidPlane(reason=str(err)))
                    else:
                        raise

        if not planes:
            logger.warning("Parsed CSV file '%s' contains 0 valid plane definitions.", filepath)

        return planes

    @classmethod
    def iter_planes(cls, filepath: str, tolerate_errors: bool = True) -> Iterator[PlaneGeometry]:
        """Streams plane definitions lazily from disk line-by-line."""
        if not os.path.exists(filepath):
            raise CSVFormatError(f"CSV file not found: '{filepath}'")

        with open(filepath, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f, start=1):
                try:
                    plane = cls.parse_line(line, line_number=idx)
                    if plane is not None:
                        yield plane
                except Exception as err:
                    if tolerate_errors:
                        logger.warning(
                            "Line %d in '%s': %s (generating black frame per FR-24)",
                            idx, filepath, err
                        )
                        yield InvalidPlane(reason=str(err))
                    else:
                        raise
