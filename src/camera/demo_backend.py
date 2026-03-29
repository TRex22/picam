"""
src/camera/demo_backend.py — Synthetic camera backend for non-Pi development.

Generates animated demo frames without any camera hardware.  Implements
the full CameraBackend interface so the rest of the app is completely
unaware it is running without a real camera.
"""

from __future__ import annotations

import logging
import math
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .backend import CameraBackend, CameraConfig, SensorInfo
from .sensor_registry import get_registry

logger = logging.getLogger(__name__)


class DemoBackend(CameraBackend):
    """
    Synthetic camera backend.

    Produces animated gradient frames with a live timestamp and current
    control values overlaid.  DNG 'captures' save a small JPEG placeholder.
    """

    DEMO_SENSOR_ID = "imx477"

    def __init__(self) -> None:
        self._config: CameraConfig | None = None
        self._controls: dict = {}
        self._last_metadata: dict = {}
        self._frame_count: int = 0
        self._started: bool = False
        self._sensor_info = get_registry().lookup(self.DEMO_SENSOR_ID)
        # Override to make it obvious this is a demo sensor
        self._sensor_info = SensorInfo(
            name="Demo Sensor (IMX477 simulated)",
            model_id="demo",
            native_w=4056, native_h=3040,
            base_iso=100,
            max_gain=32.0,
            has_raw=True,
            supported_formats=["DNG", "JPEG", "PNG"],
        )

    # ── CameraBackend interface ───────────────────────────────────────────────

    def start(self, config: CameraConfig) -> None:
        self._config = config
        self._started = True
        logger.info("DemoBackend started (%dx%d preview)",
                    config.preview_w, config.preview_h)

    def stop(self) -> None:
        self._started = False
        logger.info("DemoBackend stopped.")

    def capture_preview_frame(self) -> Image.Image | None:
        if self._config is None:
            return None
        w, h = self._config.preview_w, self._config.preview_h
        return self._make_frame(w, h)

    def capture_still(self, controls: dict, path: Path,
                      fmt: str) -> tuple[Path, dict]:
        w = self._config.preview_w if self._config else 100
        h = self._config.preview_h if self._config else 80
        img = self._make_frame(w, h, label="CAPTURE")

        ext = fmt.lower()
        if ext == "dng":
            save_path = path.with_suffix(".jpg")
            img.save(save_path, "JPEG", quality=90)
        elif ext == "jpeg":
            save_path = path.with_suffix(".jpg")
            img.save(save_path, "JPEG", quality=90)
        else:
            save_path = path.with_suffix(f".{ext}")
            img.save(save_path)

        metadata = {
            "ExposureTime": controls.get("ExposureTime", 16667),
            "AnalogueGain": controls.get("AnalogueGain", 1.0),
            "AeEnable": controls.get("AeEnable", True),
        }
        self._last_metadata = metadata
        logger.info("DemoBackend: captured %s", save_path)
        return save_path, metadata

    def apply_controls(self, controls: dict) -> None:
        self._controls = dict(controls)

    def get_metadata(self) -> dict:
        return dict(self._last_metadata)

    def get_sensor_info(self) -> SensorInfo:
        return self._sensor_info

    @property
    def is_available(self) -> bool:
        return self._started

    # ── Frame generation ──────────────────────────────────────────────────────

    def _make_frame(self, w: int, h: int, label: str = "") -> Image.Image:
        self._frame_count += 1
        t = time.time()

        # Animated gradient
        img = Image.new("RGB", (w, h))
        pixels = img.load()
        for y in range(h):
            for x in range(w):
                r = int(127 + 127 * math.sin(t * 0.7 + x * 0.02))
                g = int(127 + 127 * math.sin(t * 0.5 + y * 0.015))
                b = int(60 + 40 * math.sin(t * 0.3 + (x + y) * 0.01))
                # Apply brightness/contrast from controls
                brightness = self._controls.get("Brightness", 0.0)
                contrast   = self._controls.get("Contrast",   1.0)
                r = int(max(0, min(255, (r + brightness * 128) * contrast)))
                g = int(max(0, min(255, (g + brightness * 128) * contrast)))
                b = int(max(0, min(255, (b + brightness * 128) * contrast)))
                pixels[x, y] = (r, g, b)

        # Overlay
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 11)
            font_sm = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 9)
        except (IOError, OSError):
            font = ImageFont.load_default()
            font_sm = font

        from datetime import datetime
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]

        # Semi-transparent top bar
        draw.rectangle([(0, 0), (w, 20)], fill=(0, 0, 0, 180))
        draw.text((4, 3), f"DEMO MODE  {ts}  frame #{self._frame_count}",
                  fill=(0, 255, 136), font=font)

        if label:
            draw.text((w // 2 - 30, h // 2 - 8), label,
                      fill=(255, 255, 255), font=font)

        # Control values bottom
        iso   = self._controls.get("AnalogueGain", "—")
        shutter = self._controls.get("ExposureTime", "—")
        draw.rectangle([(0, h - 16), (w, h)], fill=(0, 0, 0, 160))
        draw.text((4, h - 13),
                  f"gain={iso}  exp={shutter}µs",
                  fill=(200, 200, 200), font=font_sm)

        return img
