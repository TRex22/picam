"""
src/camera/backend.py — Abstract camera backend for PiCam V2.

All camera implementations must subclass CameraBackend and implement
every abstract method.  This allows the rest of the application to be
completely agnostic about whether it is talking to a real Picamera2
instance or a synthetic DemoBackend.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PIL import Image


@dataclass
class CameraConfig:
    """Configuration parameters for starting the camera."""
    preview_w: int = 480
    preview_h: int = 360
    sensor_w: int = 4056
    sensor_h: int = 3040
    buffer_count: int = 2


@dataclass
class SensorInfo:
    """Static information about a detected camera sensor."""
    name: str                           # Human-readable name, e.g. "IMX477"
    model_id: str                       # Raw camera_properties["Model"] string
    native_w: int = 0
    native_h: int = 0
    base_iso: int = 100                 # ISO at AnalogueGain=1.0
    max_gain: float = 32.0
    has_raw: bool = True
    supported_formats: list[str] = field(default_factory=lambda: ["DNG"])
    default_colour_profile: str = ""
    dpc_modes: list[str] = field(
        default_factory=lambda: ["Off", "Fast", "HighQuality"]
    )

    @property
    def native_resolution(self) -> tuple[int, int]:
        return self.native_w, self.native_h


class CameraBackend(ABC):
    """
    Abstract base class for all PiCam camera backends.

    Subclasses must implement every abstract method.  The single-config
    design constraint (never reconfigure at runtime) is enforced by the
    protocol: `start()` is called once at startup with a full config;
    subsequent calls are limited to `apply_controls()`, `capture_preview_frame()`,
    and `capture_still()`.
    """

    @abstractmethod
    def start(self, config: CameraConfig) -> None:
        """
        Initialise and start the camera with the given configuration.
        Must be called exactly once before any other method.
        """

    @abstractmethod
    def stop(self) -> None:
        """Stop the camera and release all hardware resources."""

    @abstractmethod
    def capture_preview_frame(self) -> "Image.Image | None":
        """
        Return the current preview frame as a PIL Image (RGB).
        Returns None if a frame is temporarily unavailable.
        This method is called on a background thread up to ~24 times/second.
        """

    @abstractmethod
    def capture_still(self, controls: dict, path: Path, fmt: str) -> tuple[Path, dict]:
        """
        Capture a full-resolution still image.

        Args:
            controls: picamera2-style controls dict (AeEnable, AnalogueGain, etc.)
            path:     Destination file path (extension ignored if fmt overrides it).
            fmt:      Output format: "DNG", "JPEG", or "PNG".

        Returns:
            (saved_path, metadata_dict) where metadata_dict contains the
            capture metadata (ExposureTime, AnalogueGain, etc.).
        """

    @abstractmethod
    def apply_controls(self, controls: dict) -> None:
        """
        Apply a dict of libcamera controls to the running camera.
        Called on the main thread; must not block for more than ~5 ms.
        """

    @abstractmethod
    def get_metadata(self) -> dict:
        """Return the metadata from the most recent captured frame."""

    @abstractmethod
    def get_sensor_info(self) -> SensorInfo:
        """Return static information about the attached sensor."""

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """True if the backend has a live camera connection."""
