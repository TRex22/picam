"""Unit tests for camera backends and sensor registry."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from camera.backend import CameraConfig, SensorInfo
from camera.sensor_registry import SensorRegistry, get_registry
from camera.demo_backend import DemoBackend


# ── SensorRegistry ────────────────────────────────────────────────────────────

class TestSensorRegistry:
    def test_lookup_known_sensor(self) -> None:
        reg = SensorRegistry()
        info = reg.lookup("imx477")
        assert info.name == "IMX477 (HQ Camera)"
        assert info.native_w == 4056
        assert info.native_h == 3040

    def test_lookup_case_insensitive(self) -> None:
        reg = SensorRegistry()
        info = reg.lookup("IMX477")
        assert info.model_id == "imx477"

    def test_lookup_partial_match(self) -> None:
        reg = SensorRegistry()
        info = reg.lookup("imx477 rev3")
        assert "imx477" in info.model_id.lower() or "IMX477" in info.name

    def test_lookup_unknown_returns_fallback(self) -> None:
        reg = SensorRegistry()
        info = reg.lookup("totally_unknown_sensor_xyz")
        assert info.model_id == "totally_unknown_sensor_xyz"

    def test_register_custom_sensor(self) -> None:
        reg = SensorRegistry()
        custom = SensorInfo(name="My Sensor", model_id="custom_001",
                            native_w=1920, native_h=1080)
        reg.register(custom)
        assert reg.lookup("custom_001").name == "My Sensor"

    def test_user_sensors_file_loaded(self, tmp_path: Path) -> None:
        import json
        sensors_file = tmp_path / "sensors.json"
        sensors_file.write_text(json.dumps([
            {"name": "User Sensor", "model_id": "user_test",
             "native_w": 640, "native_h": 480}
        ]), encoding="utf-8")

        # Patch USER_SENSORS_FILE
        import camera.sensor_registry as sr
        orig = sr.USER_SENSORS_FILE
        sr.USER_SENSORS_FILE = sensors_file
        try:
            reg = SensorRegistry()
            info = reg.lookup("user_test")
            assert info.name == "User Sensor"
        finally:
            sr.USER_SENSORS_FILE = orig

    def test_imx708_present(self) -> None:
        reg = SensorRegistry()
        info = reg.lookup("imx708")
        assert info.native_w == 4608


# ── DemoBackend ───────────────────────────────────────────────────────────────

class TestDemoBackend:
    def _started_backend(self) -> DemoBackend:
        b = DemoBackend()
        b.start(CameraConfig(preview_w=320, preview_h=240))
        return b

    def test_is_available_after_start(self) -> None:
        b = self._started_backend()
        assert b.is_available is True
        b.stop()

    def test_not_available_before_start(self) -> None:
        b = DemoBackend()
        assert b.is_available is False

    def test_not_available_after_stop(self) -> None:
        b = self._started_backend()
        b.stop()
        assert b.is_available is False

    def test_capture_preview_frame_returns_image(self) -> None:
        from PIL import Image
        b = self._started_backend()
        frame = b.capture_preview_frame()
        assert frame is not None
        assert isinstance(frame, Image.Image)
        assert frame.size == (320, 240)
        b.stop()

    def test_capture_preview_before_start_returns_none(self) -> None:
        b = DemoBackend()
        assert b.capture_preview_frame() is None

    def test_capture_still_creates_file(self, tmp_path: Path) -> None:
        b = self._started_backend()
        path = tmp_path / "IMG_test.dng"
        saved_path, metadata = b.capture_still({}, path, "DNG")
        assert saved_path.exists()
        assert "ExposureTime" in metadata
        b.stop()

    def test_capture_still_jpeg(self, tmp_path: Path) -> None:
        b = self._started_backend()
        path = tmp_path / "IMG_test.jpg"
        saved_path, _ = b.capture_still({}, path, "JPEG")
        assert saved_path.suffix == ".jpg"
        assert saved_path.exists()
        b.stop()

    def test_apply_controls_stored(self) -> None:
        b = self._started_backend()
        b.apply_controls({"Brightness": 0.5, "Contrast": 1.2})
        assert b._controls["Brightness"] == 0.5
        b.stop()

    def test_get_metadata_empty_before_capture(self) -> None:
        b = self._started_backend()
        assert b.get_metadata() == {}
        b.stop()

    def test_get_metadata_after_capture(self, tmp_path: Path) -> None:
        b = self._started_backend()
        b.capture_still({"ExposureTime": 16667}, tmp_path / "test.dng", "DNG")
        meta = b.get_metadata()
        assert "ExposureTime" in meta
        b.stop()

    def test_get_sensor_info(self) -> None:
        b = DemoBackend()
        info = b.get_sensor_info()
        assert info.name != ""
        assert info.has_raw is True
