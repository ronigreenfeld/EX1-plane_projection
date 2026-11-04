"""Domain-specific typed exception hierarchy for the projection pipeline."""


class ProjectionError(Exception):
    """Base exception for all domain errors within the 3D projection engine."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class GeometryValidationError(ProjectionError):
    """Raised when plane coordinates violate geometric constraints (e.g., non-isosceles)."""

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message)
        self.details = details or {}


class CoplanarityError(GeometryValidationError):
    """Raised when 4 points intended to define a trapezoid plane are not coplanar."""

    def __init__(self, message: str, triple_product: float | None = None) -> None:
        details = {"scalar_triple_product": triple_product} if triple_product is not None else {}
        super().__init__(message, details=details)
        self.triple_product = triple_product


class VolumeIOError(ProjectionError):
    """Raised when volume file loading, format validation, or dimensional checks fail."""

    def __init__(self, message: str, filepath: str | None = None) -> None:
        super().__init__(message)
        self.filepath = filepath


class VideoEncodingError(ProjectionError):
    """Raised when video initialization or frame encoding encounters a codec/dimension failure."""

    def __init__(self, message: str, dimensions: tuple[int, int] | None = None) -> None:
        super().__init__(message)
        self.dimensions = dimensions


class CSVFormatError(ProjectionError):
    """Raised when CSV parsing encounters malformed rows or invalid coordinate counts."""

    def __init__(self, message: str, line_number: int | None = None) -> None:
        super().__init__(message)
        self.line_number = line_number
