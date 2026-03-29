"""
src/camera/picamera2_backend.py — Picamera2 camera backend for PiCam V2.

Implements CameraBackend using picamera2/libcamera.  Single-configuration
design: configured once at startup with both a preview stream and a raw
stream; never reconfigures at runtime.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path

from PIL import Image

from .backend import CameraBackend, CameraConfig, SensorInfo
from .sensor_registry import get_registry

logger = logging.getLogger(__name__)

try:
    from picamera2 import Picamera2
    _PICAMERA2_AVAILABLE = True
except ImportError:
    _PICAMERA2_AVAILABLE = False


class Picamera2Backend(CameraBackend):
    """
    Picamera2 / libcamera backend.

    IMPORTANT: Never call Picamera2.configure() after start() — this would
    trigger the Pi 5 PiSP TDN crash.  All runtime changes go through
    set_controls() only.
    """

    def __init__(self) -> None:
        if not _PICAMERA2_AVAILABLE:
            raise RuntimeError(
                "picamera2 is not installed.  "
                "Use DemoBackend for non-Pi development."
            )
        self._cam: Picamera2 | None = None
        self._last_metadata: dict = {}
        self._sensor_info: SensorInfo | None = None

    def start(self, config: CameraConfig) -> None:
        self._cam = Picamera2()

        # Detect sensor before configuring
        try:
            model_id = self._cam.camera_properties.get("Model", "unknown")
            self._sensor_info = get_registry().lookup(model_id)
            logger.info("Detected sensor: %s", self._sensor_info.name)
        except Exception as exc:
            logger.warning("Sensor detection failed: %s", exc)
            self._sensor_info = get_registry().lookup("unknown")

        camera_config = self._cam.create_preview_configuration(
            main={"size": (config.preview_w, config.preview_h), "format": "RGB888"},
            raw={"size": (config.sensor_w, config.sensor_h)},
            buffer_count=config.buffer_count,
            controls={"NoiseReductionMode": 0},
        )
        self._cam.configure(camera_config)
        self._cam.start()
        time.sleep(1)   # let 3A settle
        logger.info("Picamera2Backend started (%dx%d preview)",
                    config.preview_w, config.preview_h)

    def stop(self) -> None:
        if self._cam is not None:
            try:
                self._cam.stop()
                self._cam.close()
            except Exception as exc:
                logger.warning("Error stopping camera: %s", exc)
            finally:
                self._cam = None
        logger.info("Picamera2Backend stopped.")

    def capture_preview_frame(self) -> Image.Image | None:
        if self._cam is None:
            return None
        try:
            arr = self._cam.capture_array("main")
            return Image.fromarray(arr, "RGB")
        except Exception as exc:
            logger.debug("Preview frame capture failed: %s", exc)
            return None

    def capture_still(self, controls: dict, path: Path,
                      fmt: str) -> tuple[Path, dict]:
        if self._cam is None:
            raise RuntimeError("Camera not started.")

        cap_controls: dict = {
            "NoiseReductionMode": 0,
            "Brightness":  controls.get("Brightness",  0.0),
            "Contrast":    controls.get("Contrast",    1.0),
            "Saturation":  controls.get("Saturation",  1.0),
            "Sharpness":   controls.get("Sharpness",   1.0),
            "AwbEnable":   controls.get("AwbEnable",   True),
        }

        ae_enable = controls.get("AeEnable", True)
        cap_controls["AeEnable"] = ae_enable
        if not ae_enable:
            if "ExposureTime" in controls:
                cap_controls["ExposureTime"] = int(controls["ExposureTime"])
            if "AnalogueGain" in controls:
                cap_controls["AnalogueGain"] = float(controls["AnalogueGain"])

        self._cam.set_controls(cap_controls)
        time.sleep(0.25)   # let controls propagate

        request = self._cam.capture_request()
        try:
            metadata = request.get_metadata()
            self._last_metadata = metadata

            fmt_lower = fmt.lower()
            if fmt_lower == "dng":
                save_path = path.with_suffix(".dng")
                request.save_dng(str(save_path))
            elif fmt_lower in ("jpeg", "jpg"):
                save_path = path.with_suffix(".jpg")
                request.save("main", str(save_path))
            elif fmt_lower == "png":
                save_path = path.with_suffix(".png")
                request.save("main", str(save_path))
            else:
                save_path = path.with_suffix(".dng")
                request.save_dng(str(save_path))
        finally:
            request.release()

        return save_path, metadata

    def apply_controls(self, controls: dict) -> None:
        if self._cam is None:
            return
        try:
            safe = dict(controls)
            safe.setdefault("NoiseReductionMode", 0)
            self._cam.set_controls(safe)
        except Exception as exc:
            logger.warning("set_controls failed: %s", exc)

    def get_metadata(self) -> dict:
        return dict(self._last_metadata)

    def get_sensor_info(self) -> SensorInfo:
        if self._sensor_info is None:
            return get_registry().lookup("unknown")
        return self._sensor_info

    @property
    def is_available(self) -> bool:
        return self._cam is not None
