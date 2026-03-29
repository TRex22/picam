"""Unit tests for SettingsManager and ProfileManager."""

from __future__ import annotations

import json
import pytest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from settings.defaults import DEFAULTS
from settings.settings_manager import SettingsManager
from settings.profiles import ProfileManager, BUILTIN_PROFILES


# ── SettingsManager ───────────────────────────────────────────────────────────

class TestSettingsManager:
    def test_first_boot_creates_file(self, tmp_path: Path) -> None:
        path = tmp_path / "settings.json"
        sm = SettingsManager(path)
        assert path.exists()

    def test_first_boot_writes_defaults(self, tmp_path: Path) -> None:
        sm = SettingsManager(tmp_path / "s.json")
        assert sm.get("camera.iso") == DEFAULTS["camera"]["iso"]
        assert sm.get("camera.awb") == DEFAULTS["camera"]["awb"]

    def test_set_and_get(self, tmp_path: Path) -> None:
        sm = SettingsManager(tmp_path / "s.json")
        sm.set("camera.iso", "400")
        assert sm.get("camera.iso") == "400"

    def test_persist_and_reload(self, tmp_path: Path) -> None:
        path = tmp_path / "s.json"
        sm = SettingsManager(path)
        sm.set("camera.iso", "800")
        sm.save()

        sm2 = SettingsManager(path)
        assert sm2.get("camera.iso") == "800"

    def test_get_missing_key_returns_default(self, tmp_path: Path) -> None:
        sm = SettingsManager(tmp_path / "s.json")
        assert sm.get("nonexistent.key", "fallback") == "fallback"

    def test_save_user_defaults(self, tmp_path: Path) -> None:
        sm = SettingsManager(tmp_path / "s.json")
        state = {"iso": "200", "shutter": "1/250", "awb": False,
                 "brightness": 0.1, "contrast": 1.5,
                 "saturation": 0.5, "sharpness": 2.0, "dpc": "Off"}
        sm.save_user_defaults(state)
        boot = sm.get_boot_camera_state()
        assert boot["iso"] == "200"
        assert boot["awb"] is False

    def test_boot_state_falls_back_to_factory(self, tmp_path: Path) -> None:
        sm = SettingsManager(tmp_path / "s.json")
        boot = sm.get_boot_camera_state()
        assert boot["iso"] == DEFAULTS["camera"]["iso"]

    def test_corrupt_file_falls_back_to_defaults(self, tmp_path: Path) -> None:
        path = tmp_path / "s.json"
        path.write_text("not json{{{", encoding="utf-8")
        sm = SettingsManager(path)
        assert sm.get("camera.iso") == DEFAULTS["camera"]["iso"]


# ── ProfileManager ────────────────────────────────────────────────────────────

class TestProfileManager:
    def test_builtins_present(self, tmp_path: Path) -> None:
        pm = ProfileManager(tmp_path)
        names = pm.list_names()
        for builtin in BUILTIN_PROFILES:
            assert builtin in names

    def test_builtins_written_to_disk(self, tmp_path: Path) -> None:
        pm = ProfileManager(tmp_path)
        assert (tmp_path / "Default.json").exists()

    def test_load_builtin_camera_state(self, tmp_path: Path) -> None:
        pm = ProfileManager(tmp_path)
        state = pm.get_camera_state("Default")
        assert state is not None
        assert "iso" in state

    def test_save_and_load_user_profile(self, tmp_path: Path) -> None:
        pm = ProfileManager(tmp_path)
        camera_state = {"iso": "400", "shutter": "1/60", "awb": True,
                        "brightness": 0.0, "contrast": 1.0,
                        "saturation": 1.0, "sharpness": 1.0, "dpc": "Fast"}
        pm.save("My Profile", camera_state, description="test")
        loaded = pm.get_camera_state("My Profile")
        assert loaded is not None
        assert loaded["iso"] == "400"

    def test_delete_user_profile(self, tmp_path: Path) -> None:
        pm = ProfileManager(tmp_path)
        pm.save("Temp", {"iso": "100"})
        assert pm.delete("Temp") is True
        assert pm.load("Temp") is None

    def test_cannot_delete_builtin(self, tmp_path: Path) -> None:
        pm = ProfileManager(tmp_path)
        assert pm.delete("Default") is False

    def test_user_profiles_appear_after_builtins(self, tmp_path: Path) -> None:
        pm = ProfileManager(tmp_path)
        pm.save("Zzz Profile", {"iso": "100"})
        names = pm.list_names()
        builtin_indices = [names.index(b) for b in BUILTIN_PROFILES if b in names]
        user_index = names.index("Zzz Profile")
        assert all(user_index > bi for bi in builtin_indices)
