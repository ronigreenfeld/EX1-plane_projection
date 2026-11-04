"""Centralized configuration and constants (Single Source of Truth)."""


class _ImmutableMeta(type):
    """Metaclass preventing class-level attribute mutations."""

    def __setattr__(cls, name, value):
        raise AttributeError(f"Cannot modify immutable setting '{name}' on {cls.__name__}")


class Settings(metaclass=_ImmutableMeta):
    """Immutable project settings and thresholds."""

    # Geometric tolerances
    GEOMETRY_EPSILON: float = 0.001  # Tolerance for isosceles and coplanarity checks

    # Video pipeline constants
    DEFAULT_VIDEO_FPS: int = 30       # Playback rate for generated MP4 containers
    DEFAULT_FOURCC: str = "mp4v"      # Standard cross-platform MP4 codec
    TARGET_MIN_FPS: float = 30.0      # Assignment minimum throughput threshold
    TARGET_EXPECTED_FPS: float = 100.0  # Expected performance throughput target
    MAX_CANVAS_DIM: int = 4096        # Maximum video frame dimension (encoder profile limit)

    # Volume limits (1 <= dim < 2^10)
    MIN_VOLUME_DIM: int = 1
    MAX_VOLUME_DIM: int = 1024

    # Logging and UX
    LOG_FILENAME: str = "project.log"
    LOG_FORMAT: str = "%(asctime)s - [%(levelname)s] - %(name)s - %(message)s"

    def __setattr__(self, name, value):
        raise AttributeError(f"Cannot modify immutable setting '{name}'")
