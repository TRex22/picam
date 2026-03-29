"""
src/settings/profiles.py — Named capture profiles for PiCam V2.

Profiles are stored in ~/.config/picam2/profiles/<name>.json.
Built-in profiles are shipped with the application and cannot be deleted
(they are re-written if missing).
"""

from __future__ import annotations

import copy
import json
import logging
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

PROFILES_DIR = Path.home() / ".config" / "picam2" / "profiles"

# ── Built-in profiles ─────────────────────────────────────────────────────────
BUILTIN_PROFILES: dict[str, dict] = {
    "Default": {
        "name": "Default",
        "description": "Factory defaults — all Auto.",
        "builtin": True,
        "camera": {
            "iso": "Auto",
            "shutter": "Auto",
            "dpc": "HighQuality",
            "awb": True,
            "brightness": 0.0,
            "contrast": 1.0,
            "saturation": 1.0,
            "sharpness": 1.0,
        },
        "capture": {
            "timer": "Off",
        },
    },
    "Daylight Auto": {
        "name": "Daylight Auto",
        "description": "All Auto, AWB on, NR HighQuality — general outdoor shooting.",
        "builtin": True,
        "camera": {
            "iso": "Auto",
            "shutter": "Auto",
            "dpc": "HighQuality",
            "awb": True,
            "brightness": 0.0,
            "contrast": 1.1,
            "saturation": 1.1,
            "sharpness": 1.2,
        },
        "capture": {
            "timer": "Off",
        },
    },
    "Indoor Manual": {
        "name": "Indoor Manual",
        "description": "ISO 400, 1/30s, warm white balance for indoor/tungsten lighting.",
        "builtin": True,
        "camera": {
            "iso": "400",
            "shutter": "1/30",
            "dpc": "HighQuality",
            "awb": False,
            "brightness": 0.05,
            "contrast": 1.0,
            "saturation": 0.9,
            "sharpness": 1.0,
        },
        "capture": {
            "timer": "Off",
        },
    },
    "Astrophotography - Moon": {
        "name": "Astrophotography - Moon",
        "description": "ISO 200, 1/250s, NR off, high contrast — bright lunar surface.",
        "builtin": True,
        "camera": {
            "iso": "200",
            "shutter": "1/250",
            "dpc": "Fast",
            "awb": False,
            "brightness": 0.0,
            "contrast": 1.8,
            "saturation": 0.3,
            "sharpness": 2.0,
        },
        "capture": {
            "timer": "2s",
        },
    },
    "Astrophotography - Planets": {
        "name": "Astrophotography - Planets",
        "description": "ISO 400, 1/60s, NR off, saturated — planetary detail.",
        "builtin": True,
        "camera": {
            "iso": "400",
            "shutter": "1/60",
            "dpc": "Off",
            "awb": False,
            "brightness": 0.0,
            "contrast": 1.5,
            "saturation": 1.8,
            "sharpness": 2.5,
        },
        "capture": {
            "timer": "2s",
        },
    },
    "Astrophotography - Long Exposure Stars": {
        "name": "Astrophotography - Long Exposure Stars",
        "description": "ISO 800, 30s, NR off, DPC off — deep-sky long exposure.",
        "builtin": True,
        "camera": {
            "iso": "800",
            "shutter": "30s",
            "dpc": "Off",
            "awb": False,
            "brightness": 0.1,
            "contrast": 1.0,
            "saturation": 1.0,
            "sharpness": 1.0,
        },
        "capture": {
            "timer": "5s",
        },
    },
}


class ProfileManager:
    """
    Manages named capture profiles.

    Built-in profiles are re-written to disk on every startup to ensure
    they are always present.  User profiles are stored alongside them.
    """

    def __init__(self, profiles_dir: Path = PROFILES_DIR) -> None:
        self._dir = profiles_dir
        self._dir.mkdir(parents=True, exist_ok=True)
        self._ensure_builtins()

    # ── Query ─────────────────────────────────────────────────────────────────

    def list_names(self) -> list[str]:
        """Return sorted profile names, built-ins first."""
        builtin_names = list(BUILTIN_PROFILES.keys())
        user_names = [
            p.stem for p in sorted(self._dir.glob("*.json"))
            if p.stem not in builtin_names
        ]
        return builtin_names + user_names

    def load(self, name: str) -> dict | None:
        """Load a profile by name.  Returns None if not found."""
        path = self._path_for(name)
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Could not load profile '%s': %s", name, exc)
            return None

    def get_camera_state(self, name: str) -> dict | None:
        """Return the camera sub-dict of a profile, or None."""
        profile = self.load(name)
        if profile is None:
            return None
        return copy.deepcopy(profile.get("camera", {}))

    # ── Mutate ────────────────────────────────────────────────────────────────

    def save(self, name: str, camera_state: dict,
             description: str = "", capture_state: dict | None = None) -> None:
        """Save (create or overwrite) a user profile."""
        profile: dict[str, Any] = {
            "name": name,
            "description": description,
            "builtin": False,
            "camera": copy.deepcopy(camera_state),
        }
        if capture_state:
            profile["capture"] = copy.deepcopy(capture_state)
        path = self._path_for(name)
        try:
            path.write_text(
                json.dumps(profile, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            logger.info("Profile '%s' saved to %s", name, path)
        except OSError as exc:
            logger.warning("Could not save profile '%s': %s", name, exc)

    def delete(self, name: str) -> bool:
        """Delete a user profile.  Returns False if builtin or not found."""
        if name in BUILTIN_PROFILES:
            logger.warning("Cannot delete built-in profile '%s'.", name)
            return False
        path = self._path_for(name)
        if not path.exists():
            return False
        try:
            path.unlink()
            return True
        except OSError as exc:
            logger.warning("Could not delete profile '%s': %s", name, exc)
            return False

    # ── Internal ──────────────────────────────────────────────────────────────

    def _path_for(self, name: str) -> Path:
        safe = re.sub(r"[^\w\- ]", "_", name).strip()
        return self._dir / f"{safe}.json"

    def _ensure_builtins(self) -> None:
        for name, profile in BUILTIN_PROFILES.items():
            path = self._path_for(name)
            if not path.exists():
                try:
                    path.write_text(
                        json.dumps(profile, indent=2, ensure_ascii=False),
                        encoding="utf-8",
                    )
                except OSError as exc:
                    logger.warning(
                        "Could not write built-in profile '%s': %s", name, exc
                    )
