"""
src/settings/defaults.py — Factory default values for PiCam V2.

These are the hardcoded baseline values.  The SettingsManager reads these
on first boot (no settings.json yet) and writes them as the initial settings
file.  They are also the values used by "Reset to Defaults" if the user has
never pressed "Save as Default Boot State".
"""

from __future__ import annotations

VERSION = "2.0.0"

# ── Window geometry ───────────────────────────────────────────────────────────
WINDOW_W: int = 800
WINDOW_H: int = 480

# ── Camera / ISP ─────────────────────────────────────────────────────────────
ISO_DEFAULT: str = "Auto"
SHUTTER_DEFAULT: str = "Auto"
DPC_DEFAULT: str = "HighQuality"
AWB_DEFAULT: bool = True
BRIGHTNESS_DEFAULT: float = 0.0
CONTRAST_DEFAULT: float = 1.0
SATURATION_DEFAULT: float = 1.0
SHARPNESS_DEFAULT: float = 1.0

# ── Capture ───────────────────────────────────────────────────────────────────
TIMER_DEFAULT: str = "Off"       # Off / 2s / 5s / 10s / Custom
TIMER_CUSTOM_S: int = 3          # seconds when "Custom" is selected
SHUTTER_SOUND_ENABLED: bool = False
SHUTTER_SOUND_PATH: str = ""     # empty = no sound

# ── Output ────────────────────────────────────────────────────────────────────
OUTPUT_FORMAT: str = "DNG"       # DNG / JPEG / PNG
JPEG_QUALITY: int = 95

# ── UI ────────────────────────────────────────────────────────────────────────
THEME: str = "dark_blue"
FULLSCREEN: bool = False

# ── Convenience dict for serialisation ───────────────────────────────────────
DEFAULTS: dict = {
    "version": VERSION,
    "camera": {
        "iso": ISO_DEFAULT,
        "shutter": SHUTTER_DEFAULT,
        "dpc": DPC_DEFAULT,
        "awb": AWB_DEFAULT,
        "brightness": BRIGHTNESS_DEFAULT,
        "contrast": CONTRAST_DEFAULT,
        "saturation": SATURATION_DEFAULT,
        "sharpness": SHARPNESS_DEFAULT,
    },
    "capture": {
        "timer": TIMER_DEFAULT,
        "timer_custom_s": TIMER_CUSTOM_S,
        "shutter_sound_enabled": SHUTTER_SOUND_ENABLED,
        "shutter_sound_path": SHUTTER_SOUND_PATH,
        "output_format": OUTPUT_FORMAT,
        "jpeg_quality": JPEG_QUALITY,
    },
    "ui": {
        "theme": THEME,
        "fullscreen": FULLSCREEN,
        "window_w": WINDOW_W,
        "window_h": WINDOW_H,
    },
    "user_defaults": None,   # populated by "Save as Default Boot State"
}
