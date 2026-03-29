"""
src/camera/sensor_registry.py — Sensor detection and registry for PiCam V2.

Known sensors are defined here with their capabilities.  The registry is
extensible via ~/.config/picam2/sensors.json for user-added sensors.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

from .backend import SensorInfo

logger = logging.getLogger(__name__)

USER_SENSORS_FILE = Path.home() / ".config" / "picam2" / "sensors.json"

# ── Known sensor definitions ──────────────────────────────────────────────────
_KNOWN_SENSORS: dict[str, SensorInfo] = {
    # Raspberry Pi HQ Camera
    "imx477": SensorInfo(
        name="IMX477 (HQ Camera)",
        model_id="imx477",
        native_w=4056, native_h=3040,
        base_iso=100,
        max_gain=32.0,
        has_raw=True,
        supported_formats=["DNG", "JPEG", "PNG"],
        default_colour_profile="imx477_standard",
        dpc_modes=["Off", "Fast", "HighQuality"],
    ),
    # Raspberry Pi Camera Module 3
    "imx708": SensorInfo(
        name="IMX708 (Camera Module 3)",
        model_id="imx708",
        native_w=4608, native_h=2592,
        base_iso=100,
        max_gain=16.0,
        has_raw=True,
        supported_formats=["DNG", "JPEG", "PNG"],
        default_colour_profile="imx708_standard",
        dpc_modes=["Off", "Fast", "HighQuality"],
    ),
    # Raspberry Pi Camera Module 2
    "imx219": SensorInfo(
        name="IMX219 (Camera Module 2)",
        model_id="imx219",
        native_w=3280, native_h=2464,
        base_iso=100,
        max_gain=16.0,
        has_raw=True,
        supported_formats=["DNG", "JPEG", "PNG"],
        default_colour_profile="imx219_standard",
        dpc_modes=["Off", "Fast", "HighQuality"],
    ),
    # Raspberry Pi Camera Module v1
    "ov5647": SensorInfo(
        name="OV5647 (Camera Module v1)",
        model_id="ov5647",
        native_w=2592, native_h=1944,
        base_iso=100,
        max_gain=8.0,
        has_raw=False,
        supported_formats=["JPEG", "PNG"],
        default_colour_profile="",
        dpc_modes=["Off", "Fast"],
    ),
    # Arducam 64MP Hawkeye
    "arducam_64mp": SensorInfo(
        name="Arducam 64MP Hawkeye",
        model_id="arducam_64mp",
        native_w=9152, native_h=6944,
        base_iso=100,
        max_gain=64.0,
        has_raw=True,
        supported_formats=["DNG", "JPEG", "PNG"],
        default_colour_profile="",
        dpc_modes=["Off", "Fast", "HighQuality"],
    ),
    # Generic / unknown sensor fallback
    "unknown": SensorInfo(
        name="Unknown Sensor",
        model_id="unknown",
        native_w=0, native_h=0,
        base_iso=100,
        max_gain=32.0,
        has_raw=True,
        supported_formats=["DNG", "JPEG"],
        default_colour_profile="",
        dpc_modes=["Off", "Fast", "HighQuality"],
    ),
}


class SensorRegistry:
    """
    Registry of known camera sensors.

    Looks up a sensor by its model_id (from camera_properties["Model"]).
    User-defined entries in ~/.config/picam2/sensors.json override or extend
    the built-in list.
    """

    def __init__(self) -> None:
        self._sensors: dict[str, SensorInfo] = dict(_KNOWN_SENSORS)
        self._load_user_sensors()

    def lookup(self, model_id: str) -> SensorInfo:
        """
        Return SensorInfo for the given model_id.
        Falls back to the 'unknown' entry if not found.
        Matching is case-insensitive and strips whitespace.
        """
        key = model_id.strip().lower()
        if key in self._sensors:
            return self._sensors[key]
        # Partial match: some drivers report "imx477 rev3" style strings
        for k, info in self._sensors.items():
            if k != "unknown" and k in key:
                logger.debug("Sensor '%s' matched via partial key '%s'", model_id, k)
                return info
        logger.warning("Unknown sensor model_id '%s'; using fallback.", model_id)
        fallback = _KNOWN_SENSORS["unknown"]
        fallback.model_id = model_id
        return fallback

    def register(self, info: SensorInfo) -> None:
        """Register (or replace) a sensor entry."""
        self._sensors[info.model_id.lower()] = info

    def list_sensors(self) -> list[SensorInfo]:
        return list(self._sensors.values())

    def _load_user_sensors(self) -> None:
        if not USER_SENSORS_FILE.exists():
            return
        try:
            raw = json.loads(USER_SENSORS_FILE.read_text(encoding="utf-8"))
            for entry in raw:
                info = SensorInfo(
                    name=entry.get("name", "Custom"),
                    model_id=entry["model_id"],
                    native_w=entry.get("native_w", 0),
                    native_h=entry.get("native_h", 0),
                    base_iso=entry.get("base_iso", 100),
                    max_gain=float(entry.get("max_gain", 32.0)),
                    has_raw=entry.get("has_raw", True),
                    supported_formats=entry.get("supported_formats", ["DNG"]),
                    default_colour_profile=entry.get("default_colour_profile", ""),
                    dpc_modes=entry.get("dpc_modes", ["Off", "Fast", "HighQuality"]),
                )
                self._sensors[info.model_id.lower()] = info
                logger.info("Loaded user sensor: %s", info.name)
        except (OSError, json.JSONDecodeError, KeyError) as exc:
            logger.warning("Could not load user sensors from %s: %s",
                           USER_SENSORS_FILE, exc)


# Module-level singleton
_registry: SensorRegistry | None = None


def get_registry() -> SensorRegistry:
    global _registry
    if _registry is None:
        _registry = SensorRegistry()
    return _registry
