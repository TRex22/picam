"""
src/settings/settings_manager.py — Persistent settings for PiCam V2.

Reads/writes  ~/.config/picam2/settings.json.
On first boot writes the factory defaults; on subsequent boots restores
the last-used values.
"""

from __future__ import annotations

import copy
import json
import logging
from pathlib import Path
from typing import Any

from .defaults import DEFAULTS

logger = logging.getLogger(__name__)

CONFIG_DIR = Path.home() / ".config" / "picam2"
SETTINGS_FILE = CONFIG_DIR / "settings.json"


class SettingsManager:
    """
    Thread-safe (read-only from worker threads) settings persistence.

    Usage::

        sm = SettingsManager()
        iso = sm.get("camera.iso")
        sm.set("camera.iso", "400")
        sm.save()
    """

    def __init__(self, path: Path = SETTINGS_FILE) -> None:
        self._path = path
        self._data: dict = {}
        self._load()

    # ── Public API ────────────────────────────────────────────────────────────

    def get(self, key: str, default: Any = None) -> Any:
        """
        Read a setting using dot-notation (e.g. "camera.iso").
        Returns *default* if the key is absent.
        """
        parts = key.split(".")
        node = self._data
        for part in parts:
            if not isinstance(node, dict) or part not in node:
                return default
            node = node[part]
        return node

    def set(self, key: str, value: Any) -> None:
        """Write a setting using dot-notation.  Does NOT auto-save."""
        parts = key.split(".")
        node = self._data
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = value

    def save(self) -> None:
        """Persist current settings to disk."""
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._path.write_text(
                json.dumps(self._data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except OSError as exc:
            logger.warning("Could not save settings to %s: %s", self._path, exc)

    def save_user_defaults(self, camera_state: dict) -> None:
        """
        Snapshot *camera_state* as the user's default boot state.
        This is what "Save as Default Boot State" writes; it is what
        "Reset to Defaults" restores.
        """
        self._data["user_defaults"] = copy.deepcopy(camera_state)
        self.save()

    def get_boot_camera_state(self) -> dict:
        """
        Return the camera state to restore on startup.
        Prefers user_defaults if set, otherwise falls back to factory defaults.
        """
        user = self._data.get("user_defaults")
        if user and isinstance(user, dict):
            return copy.deepcopy(user)
        return copy.deepcopy(DEFAULTS["camera"])

    def get_all(self) -> dict:
        return copy.deepcopy(self._data)

    # ── Internal ──────────────────────────────────────────────────────────────

    def _load(self) -> None:
        if self._path.exists():
            try:
                raw = self._path.read_text(encoding="utf-8")
                loaded = json.loads(raw)
                # Deep-merge: start from factory defaults then overlay saved values
                self._data = _deep_merge(copy.deepcopy(DEFAULTS), loaded)
                logger.debug("Settings loaded from %s", self._path)
                return
            except (OSError, json.JSONDecodeError) as exc:
                logger.warning(
                    "Could not read settings file %s (%s); using defaults.",
                    self._path, exc,
                )
        # First boot or corrupt file
        self._data = copy.deepcopy(DEFAULTS)
        self.save()
        logger.info("Settings file created at %s with factory defaults.", self._path)


def _deep_merge(base: dict, overlay: dict) -> dict:
    """Recursively merge *overlay* into *base*, returning *base*."""
    for key, value in overlay.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
    return base
