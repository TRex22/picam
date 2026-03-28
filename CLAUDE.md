# CLAUDE.md — PiCam V2 Project Guide

## Project Overview

PiCam V2 is a Raspberry Pi camera application built on picamera2/libcamera with a Tkinter desktop GUI targeting Raspberry Pi 4 & 5 with a DSP touchscreen display.

**Entry point:** `src/main.py`
**Target platform:** Raspberry Pi 4 & 5, Raspberry Pi OS Bookworm (64-bit)
**Python:** 3.11+

## Stack

- **Camera:** `picamera2` >= 0.3.12 (libcamera backend)
- **GUI:** `tkinter` + `ttk` (standard library)
- **Image:** `Pillow` (PIL), `rawpy`, `piexif`
- **Hardware:** `gpiozero` (optional), `RPi.GPIO` (optional)
- **Tests:** `pytest`

## Key Commands

```bash
# Run the app (on Pi)
python src/main.py

# Run in demo mode (no camera required)
python src/main.py --demo

# Run fullscreen on DSP display
python src/main.py --fullscreen --geometry 800x480

# Run tests
pytest tests/

# Run unit tests only
pytest tests/unit/

# Install dependencies (Pi)
sudo apt install python3-picamera2 python3-pil python3-pil.imagetk python3-piexif
pip install -r requirements.txt
```

## Architecture

```
src/
├── main.py                 # Entry point; parses args, creates Tk root, starts app
├── app.py                  # PiCamApp — top-level Tk application class
├── camera/
│   ├── backend.py          # CameraBackend abstract base class
│   ├── picamera2_backend.py # Picamera2 implementation (Pi 4 & 5)
│   ├── demo_backend.py     # DemoBackend — synthetic frames, no hardware needed
│   ├── sensor_registry.py  # SensorInfo dataclass + sensor detection
│   ├── colour_profiles.py  # ColourProfileManager
│   └── simulated_preview.py # SimulatedPreviewEngine for long exposures
├── ui/
│   ├── app_window.py       # Main window layout
│   ├── viewfinder.py       # Live preview widget
│   ├── control_panel.py    # Right-hand controls panel
│   ├── overlays.py         # Countdown, capture flash, histogram overlays
│   ├── touch_handler.py    # Touch/gesture event handling
│   ├── screen_manager.py   # Backlight, DPMS, orientation
│   ├── gallery/            # Gallery browser and image viewer
│   └── themes/             # ThemeManager + built-in themes
├── storage/
│   ├── capture_controller.py # Orchestrates capture, EXIF, save
│   ├── exif_writer.py      # piexif / exiftool EXIF injection
│   ├── ramdrive.py         # Tmpfs ramdisk management
│   └── samba.py            # SMB/CIFS network share
├── hardware/
│   ├── gpio_manager.py     # Optional GPIO button mapping
│   ├── battery_monitor.py  # UPS HAT battery monitoring
│   └── temp_monitor.py     # CPU/GPU temperature monitoring
└── settings/
    ├── settings_manager.py # Read/write ~/.config/picam2/settings.json
    ├── defaults.py         # Factory default values
    ├── profiles.py         # ProfileManager — named capture profiles
    └── lens_database.py    # LensDatabase — lens metadata lookup
```

## Critical Design Rules

1. **Single-configuration model** — never reconfigure the camera at runtime. The Pi 5 PiSP TDN crashes on mode switches. Configure once at startup with both preview and raw streams.
2. **Main-thread Tkinter var access** — all `StringVar/.get()` calls must happen on the Tk main thread before handing off to worker threads.
3. **Raw stream always on** — raw Bayer stream runs alongside RGB preview at all times.
4. **GPIO is optional** — app must start cleanly with no GPIO hardware present.
5. **Demo mode** — `DemoBackend` must work on any OS without camera hardware for development.

## Commit Convention

```
[Phase X.Y] Short description
```

Examples:
- `[Phase 0.1] Fix aspect ratio in viewfinder`
- `[Phase 1.1] Add CameraBackend abstract base class`
- `chore: update dependencies`

## PR Convention

- Target branch: `development`
- Merge to `main` only for releases
- Include test coverage for new features

## Settings File

User settings live at `~/.config/picam2/settings.json`. Never hardcode paths — always use `SettingsManager`.

## Colour Profiles

Colour profiles are stored in `colour_profiles/` (intended as a git submodule: `trex22/Colour_Profiles`). The app works without them (uses sensor defaults).
