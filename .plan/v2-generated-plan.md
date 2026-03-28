# PiCam V2 — Migration & Development Plan

> **From:** v1.5 (legacy picamera/MMAL, Pi 4, framebuffer, GPIO buttons, headless)
> **To:** V2 (picamera2/libcamera, Pi 5, DSP touchscreen, Tkinter desktop GUI)
> **Proof of Concept baseline:** `picam2_proof_of_concept.py`
> **Image processing tooling:** MagicForge (OpenCV / rawpy / drizzle pipeline)
> **CI/CD reference:** artemis repo pattern
> **Target platforms:** Raspberry Pi 4 & 5
> **Date:** March 2026

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Repository Cleanup & Migration](#repository-cleanup--migration)
3. [Phase 0 — PoC Fixes & Stabilisation](#phase-0--poc-fixes--stabilisation)
4. [Phase 1 — Core Foundation](#phase-1--core-foundation)
5. [Phase 2 — Camera Features](#phase-2--camera-features)
6. [Phase 3 — Storage & Output](#phase-3--storage--output)
7. [Phase 4 — UI & Touchscreen](#phase-4--ui--touchscreen)
8. [Phase 5 — Advanced Imaging & MagicForge Integration](#phase-5--advanced-imaging--magicforge-integration)
9. [Phase 6 — Connectivity & Remote](#phase-6--connectivity--remote)
10. [Phase 7 — Video & Audio](#phase-7--video--audio)
11. [Phase 8 — Hardware & Platform](#phase-8--hardware--platform)
12. [Phase 9 — Gallery & Media Browser](#phase-9--gallery--media-browser)
13. [Phase 10 — Astrophotography & Science Modes](#phase-10--astrophotography--science-modes)
14. [Phase 11 — Polish & Distribution](#phase-11--polish--distribution)
15. [Testing Strategy](#testing-strategy)
16. [CI/CD Pipeline](#cicd-pipeline)
17. [Deferred / Low Priority Items](#deferred--low-priority-items)
18. [Colour Profile Implementation Notes](#colour-profile-implementation-notes)
19. [Sensor Support Matrix](#sensor-support-matrix)
20. [Known Hardware Constraints](#known-hardware-constraints)
21. [UI Theme & Visual Design System](#ui-theme--visual-design-system)

---

## Architecture Overview

V2 adopts a clean layered architecture to replace the tangled v1.5 MMAL handler spaghetti:

```
┌─────────────────────────────────────────────────────┐
│                    UI Layer (Tkinter)               │
│  PiCamApp · Panels · Overlays · Touch · Gallery     │
│  ThemeManager · FontRegistry · LayoutManager        │
├─────────────────────────────────────────────────────┤
│                 Application Layer                   │
│  SettingsManager · CaptureController · TimerCtrl    │
│  ProfileManager · LensDatabase · BufferManager      │
├─────────────────────────────────────────────────────┤
│              Camera Abstraction                     │
│  CameraBackend (abstract)                           │
│    └─ Picamera2Backend  (Pi 4 & 5, single-config)   │
│    └─ DemoBackend       (dev / no-Pi)               │
│  SensorRegistry · ColourProfileManager              │
│  SimulatedPreviewEngine                             │
├─────────────────────────────────────────────────────┤
│           Hardware / Platform Layer                 │
│  GPIOManager · BatteryMonitor · TempMonitor         │
│  ScreenManager · BacklightController                │
└─────────────────────────────────────────────────────┘
```

**Key design decisions:**
- **Single-configuration model** — never reconfigure the camera at runtime; prevents the Pi 5 PiSP TDN crash.
- **Main-thread capture of Tkinter vars** — all `StringVar/.get()` calls happen on the Tk main thread before handing off to worker threads.
- **Raw stream always on** — raw Bayer stream runs continuously; capture is grab-from-queue with no mode switch.
- **Simulated preview for slow shutters** — shutter speeds below a configurable threshold (default 1/4s) switch the viewfinder into a synthetic simulation mode so the UI remains responsive and useful for composing long exposures.
- **Headless / legacy fallback** — the hardware layer is abstract enough to support both the DSP/desktop path and a future low-cost headless Pi 4 build with GPIO buttons and framebuffer output.

---

## Repository Cleanup & Migration

### Step 1 — Tag v1.5

```bash
git checkout development
git tag -a v1.5.0 -m "PiCam v1.5 — legacy MMAL/picamera, Pi 4, framebuffer, GPIO buttons"
git push origin v1.5.0
```

### Step 2 — Archive the legacy branches

```bash
# Create archive branches from the current state before clearing anything
git checkout -b archive/v1.5-legacy
git push origin archive/v1.5-legacy

git checkout main
git branch archive/main-v1.5
git push origin archive/main-v1.5
```

### Step 3 — Reset development and main

```bash
# Create a clean orphan branch for V2
git checkout --orphan v2-init
git rm -rf .
# Add the new skeleton structure, then:
git add .
git commit -m "chore: init PiCam V2 — clean start (legacy preserved at tag v1.5.0 and archive/* branches)"

# Replace branches with the clean history
git branch -D development
git branch -m development
git push origin development --force

git checkout -b main
git push origin main --force
```

### Step 4 — New Repository Structure

```
picam/
├── .ai-reviewer/                   # AI reviewer scripts (artemis pattern)
│   ├── build-system-prompt.sh
│   └── extract-claude-sections.sh
├── .ai-reviewer-config.yml
├── .github/
│   └── workflows/
│       ├── ci.yml
│       ├── ai-pr-review.yml
│       ├── ai-pr-review-on-comment.yml
│       ├── security.yml
│       ├── semgrep.yml
│       └── license-check.yml
├── AGENTS.md                       # Guidelines for AI coding agents
├── CLAUDE.md                       # Claude Code project context & dev rules
├── src/
│   ├── main.py
│   ├── app.py
│   ├── camera/
│   │   ├── backend.py              # abstract CameraBackend
│   │   ├── picamera2_backend.py
│   │   ├── demo_backend.py
│   │   ├── sensor_registry.py
│   │   ├── colour_profiles.py
│   │   └── simulated_preview.py   # slow-shutter simulation engine
│   ├── ui/
│   │   ├── app_window.py
│   │   ├── viewfinder.py
│   │   ├── control_panel.py
│   │   ├── overlays.py
│   │   ├── touch_handler.py
│   │   ├── screen_manager.py
│   │   ├── gallery/
│   │   │   ├── gallery_view.py
│   │   │   ├── image_viewer.py
│   │   │   └── video_player.py
│   │   └── themes/
│   │       ├── theme_manager.py
│   │       ├── dark_blue.py       # default PoC theme
│   │       ├── dark_red.py
│   │       ├── night_mode.py      # red-on-black for astrophotography
│   │       └── high_contrast.py
│   ├── storage/
│   │   ├── capture_controller.py
│   │   ├── exif_writer.py
│   │   ├── ramdrive.py
│   │   └── samba.py
│   ├── hardware/
│   │   ├── gpio_manager.py
│   │   ├── battery_monitor.py
│   │   └── temp_monitor.py
│   └── settings/
│       ├── settings_manager.py
│       ├── defaults.py
│       ├── profiles.py            # named capture profiles
│       └── lens_database.py
├── colour_profiles/               # git submodule → trex22/Colour_Profiles
├── lenses/
│   └── lenses.json                # bundled lens seed database
├── case/                          # 3D models (OpenSCAD / STL)
├── docs/
├── tools/
│   ├── intrinsics.py
│   └── lens_exif.py
├── web/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── install.sh
├── requirements.txt
├── CLAUDE.md
└── AGENTS.md
```

### Step 5 — CLAUDE.md & AGENTS.md

- [ ] Write `CLAUDE.md` following the artemis pattern: project stack, essential commands, dev rules, UI/styling rules, testing requirements, PR conventions.
- [ ] Write `AGENTS.md` for AI coding agent guidelines (tool restrictions, testing requirements, commit message format).

---

## Phase 0 — PoC Fixes & Stabilisation

> Fix all issues identified in the proof-of-concept before building on top of it.

### P0.1 — Preview Aspect Ratio

- [ ] Compute viewfinder dimensions to exactly match the sensor's native aspect ratio (IMX477 = 4056:3040 = 4:3).
- [ ] Implement `aspect_fit(sensor_w, sensor_h, container_w, container_h)` returning a letterboxed rect.
- [ ] Pass the corrected `size` to `create_preview_configuration`.

### P0.2 — Drop-down Text Visibility

- [ ] Fix `ttk.Combobox` drop-down list text (currently invisible due to system theme conflicts).
- [ ] Apply a `ttk.Style` patch forcing `fieldbackground`, `foreground`, and popdown list background to theme colours.
- [ ] Consider a custom `tk.OptionMenu` wrapper for full colour control.

### P0.3 — Proper Fullscreen / Display Mode

- [ ] Add `--fullscreen` CLI flag; `root.attributes("-fullscreen", True)`.
- [ ] Add `--geometry WxH` for fixed-resolution DSP screens (800×480 default).
- [ ] In fullscreen, hide the title bar and reflow the viewfinder to fill the screen with a collapsible control overlay.

### P0.4 — Capture Confirmation Feedback

- [ ] Flash a coloured border on the viewfinder for ~500 ms after capture.
- [ ] Optional shutter sound (configurable).
- [ ] Show thumbnail of the last captured image in the status bar.
- [ ] Auto-clear "Saved ✓" status after 3 seconds.

### P0.5 — EXIF Data Improvements

- [ ] Inject `DateTimeOriginal`, `Make` = `"Raspberry Pi"`, `Model` = `"PiCam2 v{VERSION}"`.
- [ ] Inject `LensModel` from the lens database or user-configured string.
- [ ] Inject sensor name in `UserComment`.
- [ ] Inject applied shutter speed, ISO, and aperture from the controls metadata returned by `capture_request()`.
- [ ] Use `piexif` for JPEG/PNG; post-process DNG with `exiftool` subprocess.

### P0.6 — Settings File

- [ ] `SettingsManager` reads/writes `~/.config/picam2/settings.json`.
- [ ] All UI variables persist on change.
- [ ] "Save as Default Boot State" button writes current state as the settings default section.

### P0.7 — White Balance Manual Controls

- [ ] Expose `ColourGains` (red gain, blue gain) sliders when AWB is off.
- [ ] Add `AwbMode` combobox: Auto / Incandescent / Tungsten / Fluorescent / Indoor / Daylight / Cloudy / Custom.
- [ ] Pass `ColourGains=(r, b)` when AWB is disabled and custom gains are set.

---

## Phase 1 — Core Foundation

### P1.1 — Abstract Camera Backend

- [ ] Define `CameraBackend` abstract base class:
  ```python
  def start(self, config: CameraConfig) -> None
  def stop(self) -> None
  def capture_preview_frame(self) -> Image.Image | None
  def capture_still(self, controls: dict, path: Path, fmt: str) -> Path
  def apply_controls(self, controls: dict) -> None
  def get_metadata(self) -> dict
  def get_sensor_info(self) -> SensorInfo
  ```
- [ ] `Picamera2Backend` implements the single-config design from the PoC.
- [ ] `DemoBackend` generates synthetic gradient frames for non-Pi development.

### P1.2 — Sensor Registry & DPC Controls

- [ ] Auto-detect sensor(s) via `Picamera2().camera_properties`.
- [ ] Define `SensorInfo` dataclass: `name`, `model_id`, `native_resolution`, `base_iso`, `max_gain`, `has_raw`, `supported_formats`, `default_colour_profile`, `dpc_modes`.
- [ ] Expose all per-sensor tunable controls that were available in v1.5 via MMAL, now via libcamera controls in an "Advanced / Sensor" collapsible section:
  - Dead Pixel Correction (DPC) on-sensor modes 0–3: None / Mapped / Dynamic / Both.
  - Noise Reduction Mode (ISP NR): Off / Fast / HighQuality (Pi 4 only when raw stream active).
  - Black level offset slider.
  - Digital gain slider (separate from analogue gain).
  - Flicker avoidance (`AeFlickerMode`): Off / 50Hz / 60Hz / Auto.
  - FPS cap via `FrameDurationLimits` (max fps slider).
- [ ] Sensor registry is extensible via `~/.config/picam2/sensors.json`.

### P1.3 — Colour Profile System *(highest priority feature)*

- [ ] Add `colour_profiles/` as a git submodule pointing to `https://github.com/trex22/Colour_Profiles.git`.
- [ ] `ColourProfileManager`:
  - Discover `.json` profiles for the detected sensor.
  - **Default for IMX477**: auto-select `Raspberry Pi High Quality Camera Lumariver 2860k-5960k Neutral Look.json`.
  - Expose a combobox listing available profiles.
  - Pass the selected profile path to `Picamera2.set_tuning_file()` **before** `configure()`.
  - Profile switching requires a ~2 s camera restart (stop → reinstantiate with new tuning → reconfigure → start).
- [ ] Embed the active profile name in `UserComment` EXIF on every capture.
- [ ] Optionally embed ICC profile bytes in JPEG/PNG output via Pillow.
- [ ] "Embed colour profile in output" toggle in Settings.

### P1.4 — Pi 4 / Pi 5 Compatibility Layer

- [ ] Detect hardware platform at startup via `/proc/device-tree/model`.
- [ ] Pi 5 (PiSP): enforce `NoiseReductionMode=0` when raw stream is active.
- [ ] Pi 4 (BCM2711): `NoiseReductionMode` is freely settable.
- [ ] Abstract into `CameraConfig.noise_reduction_mode` with platform-aware defaults.

### P1.5 — Reset Settings Button & Named Capture Profiles

**Reset to Defaults:**
- [ ] A **"Reset to Defaults"** button in the control panel instantly restores all controls to the configured default boot state (from `settings.json` defaults section, not hardcoded compile-time constants).

**Named Capture Profiles:**
- [ ] `ProfileManager` stores named profiles in `~/.config/picam2/profiles/`.
- [ ] Each profile is a JSON snapshot of all control values plus a name, description, and optional colour profile reference.
- [ ] UI: profile selector combobox at the top of the control panel with **Load**, **Save As**, and **Delete** buttons.
- [ ] Built-in shipped profiles:
  - `Default` — restore factory defaults.
  - `Astrophotography – Moon` — ISO 200, 1/250s, NR off, DPC mapped-only, no AWB, high contrast.
  - `Astrophotography – Planets` — ISO 400, 1/60s, NR off, DPC off, saturation boosted.
  - `Astrophotography – Long Exposure Stars` — ISO 800–1600, 30s/bulb, NR off, DPC off, simulated preview enabled.
  - `Daylight Auto` — all Auto, AWB on, NR HighQuality.
  - `Indoor Manual` — ISO 400, 1/30s, Tungsten AWB.
- [ ] Profiles integrate with the Simulated Preview system: any profile with a shutter speed slower than the simulation threshold automatically enables simulated preview.

---

## Phase 2 — Camera Features

### P2.1 — Simulated Preview for Long Exposures *(important)*

Long shutter speeds (slower than ~1/4 s) make the live viewfinder useless — the sensor either saturates to white, or the frame update rate falls below 1 fps. The simulated preview keeps the UI responsive and useful for composing long exposures.

**Implementation:**

- [ ] Define a configurable `PREVIEW_SIMULATION_THRESHOLD_US` (default: 250 000 µs = 1/4 s). Any selected shutter speed slower than this triggers simulation mode automatically.
- [ ] When simulation is active, the viewfinder switches to a **simulated exposure** frame:
  - The camera continues running at a fast metering exposure internally (e.g. 1/500 s, ISO auto), keeping the hardware in a stable state.
  - A reference frame is grabbed from this fast metering exposure.
  - The reference frame is transformed with a pixel-wise brightness scale: `simulated = clip(reference * (selected_exposure_us / metering_exposure_us) * gain_ratio)`.
  - This produces a brightened/saturated preview that approximates the brightness of the intended long exposure.
  - Note: the simulation is a quick approximation, not a perfect render of the final image — it helps with framing and composition but not fine exposure judgement.
- [ ] Display a red **"SIM"** badge on the viewfinder title bar when simulation is active.
- [ ] The metering reference frame refreshes every 5 seconds so the simulation stays current if the scene changes.
- [ ] Simulation is automatically deactivated when the user selects a shutter speed faster than the threshold.
- [ ] A manual **"Simulate"** toggle button allows forcing simulation on for any shutter speed (useful for very dim scenes where even 1/30 s produces an almost-black preview).
- [ ] The simulated preview setting is included in capture profiles; the "Long Exposure Stars" profile enables it by default.

### P2.2 — Timer Delay *(elevated priority — Phase 2)*

- [ ] Timer delay selector in the UI: Off / 2s / 5s / 10s / Custom.
- [ ] Large, readable countdown overlay on the viewfinder.
- [ ] Audible beeps at 3, 2, 1 if audio is available.
- [ ] GPIO button: press to start timer; press again during countdown to cancel.
- [ ] Timer persists in `settings.json` and is included in capture profiles.
- [ ] Timer supported in both still and burst modes.

### P2.3 — Multi-Sensor & Dual Sensor Support

*(Multi-sensor and dual-sensor are the same feature — combined.)*

- [ ] Enumerate all connected cameras via `Picamera2.global_camera_info()` at startup.
- [ ] **Sensor selector** at the top of the control panel showing detected sensors by model name.
- [ ] **Single sensor mode** (default): one viewfinder; switching sensors stops and restarts the backend.
- [ ] **Dual sensor mode** (when two sensors are detected): two preview panes side-by-side or stacked, each with its own independent (collapsible) control column.
- [ ] Dual capture: both sensors fire simultaneously from two threads; outputs saved with matching timestamps.
- [ ] Per-sensor settings stored independently in `settings.json` keyed by sensor model.
- [ ] Pi 5: two concurrent streams supported. Pi 4: one active sensor at a time (switching stops/restarts).
- [ ] **Scroll-through-sensors** mode: cycles through all detected sensors via touch swipe or GPIO button.

### P2.4 — ArduCam Autofocus Support

- [ ] Detect ArduCam AF modules via camera properties.
- [ ] `AfMode` combobox: Manual / Continuous / Auto-on-capture.
- [ ] `LensPosition` slider for manual focus (0.0–1.0).
- [ ] `AutoFocusCycle` triggered on shutter-half-press (GPIO) or focus window tap.

### P2.5 — Metering Modes

- [ ] `AeMeteringMode` combobox: Centre-weighted / Spot / Matrix / Custom.

### P2.6 — Exposure Compensation (EV)

- [ ] `ExposureValue` slider: −4 EV to +4 EV in 1/3-stop steps. Active only when `AeEnable=True`.

### P2.7 — Advanced Sensor Controls (from v1.5 MMAL)

The following controls were in v1.5 and must be preserved in v2 via libcamera in the "Advanced" collapsible section:

- [ ] `AnalogueGain` / `DigitalGain` — separate sliders.
- [ ] `BlackLevel` — offset slider.
- [ ] `AeFlickerMode` — Off / 50Hz / 60Hz / Auto.
- [ ] `NoiseReductionMode` — per platform (see P1.4).
- [ ] DPC on-sensor modes 0–3.
- [ ] `Saturation`, `Sharpness`, `Contrast`, `Brightness` — already in PoC.
- [ ] FPS cap slider via `FrameDurationLimits`.

---

## Phase 3 — Storage & Output

### P3.1 — Save Format Options

- [ ] Format picker in Settings: `RAW only (DNG)`, `JPEG only`, `PNG only`, `RAW + JPEG`, `RAW + PNG`.
- [ ] JPEG quality slider (1–100, default 95); PNG compression slider (0–9, default 6).
- [ ] Capture button label updates to reflect current format.

### P3.2 — In-Memory Buffer (RAMDrive)

- [ ] `/dev/shm/picam/` buffer; configurable allocation limit (default 2 GB on Pi 5).
- [ ] `BufferManager`: write to RAMDrive first, flush to persistent storage asynchronously.
- [ ] Progress indicator for pending flushes.
- [ ] Burst mode captures to RAMDrive; flush after burst ends.

### P3.3 — DCIM Directory Structure

- [ ] `~/Pictures/DCIM/YYYYMMDD/IMG_YYYYMMDD_HHMMSS.dng`.
- [ ] Configurable DCIM root in settings.

### P3.4 — Colour Profile Embedding

- [ ] DNG: profile name in `UserComment`; optional ICC inject via `exiftool`.
- [ ] JPEG/PNG: ICC profile bytes via Pillow.
- [ ] XMP sidecar alongside DNG.

### P3.5 — Samba / Network Share

- [ ] `samba.py` writes a minimal `smb.conf` sharing the DCIM folder.
- [ ] Settings toggle restarts `smbd`.
- [ ] Advertise via Avahi/mDNS (`picam2.local`).

### P3.6 — PTP/MTP Mount

- [ ] `gphoto2` virtual camera daemon for macOS Image Capture and Darktable PTP import.

### P3.7 — Darktable on Device

- [ ] Optional install; "Open in Darktable" context menu on last-captured file.

---

## Phase 4 — UI & Touchscreen

### P4.1 — Focus Window (Draggable / Resizable)

- [ ] Semi-transparent rectangle overlay; drag to reposition, corner handles to resize.
- [ ] Normalised rect passed as `AfWindows` and `ScalerCrop`.
- [ ] Doubles as digital zoom region.

### P4.2 — Touch Zoom (Pinch / Expand)

- [ ] Pinch-to-zoom mapped to `ScalerCrop`.
- [ ] Zoom level indicator overlay.
- [ ] Long-press: set AF point.

### P4.3 — Collapsible Control Panel

- [ ] In fullscreen, collapse to a thin tab; swipe from right to expand.

### P4.4 — Screen Brightness Control

- [ ] Write to `/sys/class/backlight/*/brightness`.
- [ ] Brightness slider in Settings → Display.
- [ ] Auto-dim after N seconds of inactivity.

### P4.5 — Overlay Indicators

- [ ] **Focus Peaking**: Laplacian-of-preview, configurable highlight colour.
- [ ] **Histogram**: live luminance/RGB via NumPy overlay widget.
- [ ] **Zebra Stripes**: overexposure warning; configurable threshold.
- [ ] **Grid Overlay**: rule-of-thirds / square / diagonal / centre-cross.

### P4.6 — Screen Support Matrix

| Display Type | Backend | Notes |
|---|---|---|
| DSP Touchscreen (800×480) | Tkinter/X11 | Primary v2 target |
| HDMI (any resolution) | Tkinter/X11 | Fullscreen or windowed |
| Framebuffer (headless) | pygame / fbdev | Pi 4 legacy / future small model |

- [ ] `ScreenManager` selects backend at startup via environment or `--display` flag.
- [ ] **Framebuffer path preserved** for a future low-cost headless Pi 4 build; all GPIO button actions work in this mode.

---

## Phase 5 — Advanced Imaging & MagicForge Integration

MagicForge (`/Users/trex22/development/MagicForge`) provides a mature pipeline: SIFT/ORB feature matching, drizzle stacking, lucky-drizzle mosaic, EXIF editing, scan2stl. It uses `opencv-contrib-python`, `rawpy`, `numpy`, `Pillow`, and optionally `drizzle` + `astropy`.

### P5.1 — Auto Mode & Programme Mode

- [ ] "Auto" button: set all controls to Auto.
- [ ] "Programme" mode: user fixes one parameter; camera auto-handles the rest.

### P5.2 — Burst / Continuous Shot

- [ ] Hold capture button for burst; release to stop.
- [ ] Frames to RAMDrive; flushed after burst.

### P5.3 — Manual Focus Bracketing Continuous Shot

- [ ] **Focus Bracket** mode: captures N stills stepping `LensPosition` through a user-defined range (start, end, step count).
- [ ] Designed for ArduCam AF modules; gracefully no-ops on fixed-focus lenses.
- [ ] Configurable: start position (0.0–1.0), end position, N steps, inter-frame delay.
- [ ] Output saved to `FOCUSBRACKET_YYYYMMDD_HHMMSS/` sub-folder in DCIM.
- [ ] Post-processing hook: optionally invoke MagicForge's focus-stack pipeline on the sequence.
- [ ] Simulated-bracket variant: step `Sharpness` control values for lenses without electronic focus for comparison purposes.

### P5.4 — Stop Motion Mode

- [ ] N frames at configurable interval; onion-skin overlay; optional GIF/MP4 assembly.

### P5.5 — MagicForge Pipeline Integration

- [ ] Gallery "Process in MagicForge" button on selected file(s).
- [ ] Focus bracket sequences: auto-invoke MagicForge focus-stack / lucky-drizzle pipeline.
- [ ] Astrophotography sequences: auto-invoke `lucky_drizzle_mosaic()`.
- [ ] Integration is optional; detects MagicForge via `which magicforge` or configured path.
- [ ] Can run on the Pi itself (ARM64 compatible) or on a connected host over SSH/Samba.

### P5.6 — Camera Intrinsics Tool

- [ ] `tools/intrinsics.py`: checkerboard capture → OpenCV calibration → `K` + distortion saved to `~/.config/picam2/intrinsics_{sensor}.json`.

### P5.7 — Image Statistics

- [ ] Per-capture: mean luminance, clipping %, estimated colour temperature to a JSON stats sidecar.

### P5.8 — HDR Bracket Capture

- [ ] Capture at −2EV, 0EV, +2EV; optionally invoke MagicForge for software HDR merge.

---

## Phase 6 — Connectivity & Remote

### P6.1 — Web Control Interface

- [ ] Flask/FastAPI server (`web/server.py`).
- [ ] MJPEG stream: `GET /stream`; Capture: `POST /capture`; Settings: `GET/PUT /settings`.
- [ ] Mobile-optimised UI for use as a remote shutter from a phone.
- [ ] Optional PIN authentication (settings toggle).
- [ ] Advertised via Avahi as `picam2.local`.

### P6.2 — GPIO Button Mapping

- [ ] `GPIOManager` using `gpiozero`; graceful fallback on non-Pi hardware.
- [ ] Settings: `"gpio_map": {pin: action}`. Default layout preserves v1.5 mapping.
- [ ] Available actions: Capture, TimerCapture, ToggleAWB, ZoomIn, ZoomOut, ToggleOverlay, NextSensor, BurstStart/Stop, Shutdown.
- [ ] **Headless / legacy model**: GPIO buttons are the primary UI in framebuffer mode; all capture and menu navigation actions must be reachable via buttons alone.

### P6.3 — Remote Control

Two supported remote control paths (IR explicitly excluded):

**Bluetooth HID Shutter Remote:**
- [ ] Listen for HID events from paired BT devices via `evdev`.
- [ ] Map HID key codes to actions in `settings.json` under `"bt_remote_map": {hid_code: action}`.
- [ ] Works with standard BT camera shutters, gamepads, or any HID device.

**Web Remote Access:**
- [ ] The web control interface (P6.1) is the primary remote mechanism.
- [ ] The web UI mobile layout acts as a full remote control panel.

---

## Phase 7 — Video & Audio

### P7.1 — Video Capture

- [ ] "VIDEO" mode toggle in the UI.
- [ ] `H264Encoder` with configurable bitrate (slider: 1–50 Mbps).
- [ ] Output to `~/Videos/DCIM/VID_YYYYMMDD_HHMMSS.mp4` via `FfmpegOutput`.
- [ ] Resolution/FPS presets; H.264 profile selector (Baseline / Main / High).

### P7.2 — RAW Video

- [ ] Raw Bayer video to `.dng` sequence or `.raw` binary.
- [ ] RAMDrive buffer essential; downsampled option for manageable file sizes.

### P7.3 — Audio Input

- [ ] Detect USB/3.5mm audio via `arecord -l`.
- [ ] Record alongside video via `ffmpeg` subprocess muxer.
- [ ] VU meter overlay in video mode.

---

## Phase 8 — Hardware & Platform

### P8.1 — Battery Monitor

- [ ] Detect battery HATs via I²C (PiJuice, Waveshare, Pimoroni LiPo SHIM).
- [ ] Charge, voltage, charging status polled every 30 s.
- [ ] Battery icon in status bar; low-battery warning at 15%; auto-shutdown at 5%.

### P8.2 — Fast Boot

- [ ] Disable unnecessary services; `systemd` service targeting `graphical-session.target`.
- [ ] Target: boot-to-live-view < 10 s on Pi 5.

### P8.3 — Auto Login & Auto-Run

- [ ] `raspi-config nonint do_boot_behaviour B4` in install script.
- [ ] `.config/autostart/picam2.desktop`.

### P8.4 — Power Optimisation

- [ ] Disable HDMI in DSP-only mode; CPU governor scaling; screen auto-dim.

### P8.5 — Temperature Monitoring

- [ ] `vcgencmd measure_temp` every 60 s; red indicator above 80°C; throttle overlay.

### P8.6 — 3D Case Improvements

- [ ] Ergonomic cage with handles; battery pack mounting; cold shoe mount; ventilation; OpenSCAD source in `case/`.

### P8.7 — Headless / Small Model Support (Future Pi 4 Build)

- [ ] All UI flows navigable via GPIO buttons alone in framebuffer mode.
- [ ] Key-driven menu system for settings changes.
- [ ] `--headless` flag or `PICAM2_HEADLESS=1` env var selects the framebuffer path.
- [ ] Console output retained for debug/status in headless mode.
- [ ] `pygame` drawing for the framebuffer rendering path.

---

## Phase 9 — Gallery & Media Browser

### P9.1 — Gallery View

- [ ] Gallery button in the main UI opens the gallery panel.
- [ ] Grid of thumbnails from the DCIM folder.
- [ ] Thumbnails generated lazily in a background thread; cached at `~/.cache/picam2/thumbs/`.
- [ ] Tap/click to open full-screen viewer.
- [ ] Swipe or arrow keys to navigate.
- [ ] Video files show a play-button overlay on their thumbnail.

### P9.2 — Image Viewer

- [ ] Full-screen display with pinch/scroll zoom.
- [ ] Toggleable EXIF data panel.
- [ ] Delete with confirmation; share via Samba / web download.
- [ ] "Open in Darktable" / "Process in MagicForge" contextual buttons.

### P9.3 — Video Player

- [ ] Inline playback via `ffplay` or embedded player; play/pause, seek, volume.

### P9.4 — Gallery Organisation

- [ ] Group by date, session, or capture profile.
- [ ] Filter by format (RAW / JPEG / video).

---

## Phase 10 — Astrophotography & Science Modes

### P10.1 — Astrophotography Capture Profiles

- [ ] Ship three built-in profiles (Moon, Planets, Long Exposure Stars — see P1.5).
- [ ] Long Exposure Stars: simulated preview auto-enabled; all ISP processing off.
- [ ] Dark frame subtraction: capture dark frame; subtract in post.

### P10.2 — Focus Bracket for Astrophotography

- [ ] Focus bracket mode (P5.3) especially useful for planetary/lunar imaging.
- [ ] Auto-invoke MagicForge's `lucky_drizzle_mosaic()` on the sequence.

### P10.3 — Motion Detection

- [ ] H.264 motion vectors for motion-triggered capture (wildlife / security mode).

### P10.4 — Science Overlays

- [ ] Canny edge detection overlay (focus confirmation).
- [ ] Face detection bounding boxes (OpenCV haarcascade, background thread).

---

## Phase 11 — Polish & Distribution

### P11.1 — Lens Database

- [ ] `LensDatabase` loads from bundled `lenses/lenses.json` and user file `~/.config/picam2/lenses.json`.
- [ ] Each entry: `id`, `make`, `model`, `focal_length_mm`, `max_aperture`, `min_aperture`, `mount`, `is_adapted`, `notes`, `serial_number_pattern`.
- [ ] Ship with a seed database of common lenses — especially M42 mount lenses used with adapters.
- [ ] **Lens selector UI**: searchable dropdown or pop-up list in the control panel.
- [ ] Selected lens injected into EXIF (`LensModel`, `FocalLength`, `MaxApertureValue`) on every capture.
- [ ] **Teleconverter support**: a "TC" multiplier field adjusts the reported focal length (e.g. Vivitar 2× teleconverter doubles effective focal length).
- [ ] "Add Lens" form: fill in lens details manually; saved to user lenses JSON.
- [ ] Selected lens persists in `settings.json`.

### P11.2 — Install Script (`install.sh`)

- [ ] Detect Pi 4 vs Pi 5; install Python deps, init submodule; optional darktable / samba / gphoto2.
- [ ] Configure autologin and autostart.

### P11.3 — `requirements.txt`

```
picamera2>=0.3.12
Pillow>=10.0
piexif>=1.1.3
numpy>=1.24
gpiozero>=2.0
```

### P11.4 — Logging

- [ ] Replace all `print()` with `logging`; log file with rotation; in-app log viewer.

### P11.5 — README & Docs

- [ ] `README.md`, `docs/SENSORS.md`, `docs/COLOUR_PROFILES.md`, `docs/GPIO.md`, `docs/LENSES.md`.

---

## Testing Strategy

### Test Architecture

```
tests/
├── unit/               # isolated module tests
├── integration/        # pipeline tests using DemoBackend
└── fixtures/           # sample images, mock responses, settings JSON
```

### Unit Tests

| Module | What to Test |
|---|---|
| `SettingsManager` | Load / save / defaults / migration / corrupt-file handling |
| `ColourProfileManager` | Profile discovery, IMX477 auto-select, missing profiles |
| `SensorRegistry` | Detection, property parsing, unsupported sensor fallback |
| `ExifWriter` | EXIF injection for DNG / JPEG / PNG; lens data injection |
| `LensDatabase` | Load bundled DB, load user DB, merge, search, add entry |
| `ProfileManager` | Load / save / delete / apply; built-in profiles |
| `BufferManager` | Write to RAMDrive, flush, size limits, eviction |
| `SimulatedPreviewEngine` | Threshold detection, brightness transform, SIM badge trigger |
| `TimerController` | Countdown, cancel, capture trigger integration |
| `CameraConfig` | Platform detection, Pi 4 / Pi 5 NR mode selection |
| `DemoBackend` | Synthetic frame generation, controls dict pass-through |

### Integration Tests

- [ ] Full still capture pipeline with `DemoBackend` (settings → controls → capture → EXIF → save).
- [ ] Profile load and apply (snapshot → camera restart → controls restore).
- [ ] Sensor enumeration and single/dual sensor switching.
- [ ] Focus bracket sequence capture and folder structure.
- [ ] Burst mode with RAMDrive buffer and flush.
- [ ] Simulated preview activation/deactivation on shutter speed change.
- [ ] Timer delay countdown with mock time.
- [ ] Save format combinations (DNG, JPEG, DNG+JPEG).

### UI Smoke Tests

- [ ] App starts in `DemoBackend` mode and all widgets render without exceptions.
- [ ] Control changes propagate to the backend (mock `apply_controls`, assert call args).
- [ ] Gallery thumbnail generation and display.
- [ ] Theme switching changes widget colours.

### Hardware-in-the-Loop (HiL) Tests

Run on the self-hosted Pi runner only:
- [ ] Live preview frame rate (≥ 15 fps on Pi 5).
- [ ] DNG capture and DNG validity (`exiftool -validate`).
- [ ] Colour profile loading (verify tuning file reflected in capture metadata).
- [ ] GPIO button mapping (requires physical buttons or GPIO stimulator).

### Coverage Requirements

- Minimum **80% overall coverage** for all non-hardware modules.
- No coverage reduction allowed on PRs (enforced by CI).
- `Picamera2Backend`, `GPIOManager`, `BatteryMonitor` excluded from thresholds; tested by HiL.

---

## CI/CD Pipeline

Following the artemis repo pattern, the following GitHub Actions workflows are implemented:

### `ci.yml` — Main CI Workflow

Triggers on every PR and push to `main` / `development`.

```
Jobs:
  lint         → flake8, black --check, isort --check, pylint
  test         → pytest tests/unit tests/integration + coverage check (≥80%)
  hil-test     → pytest tests/hil on [self-hosted, raspberry-pi] runner
                 (only on PRs targeting main)
  accessibility → pa11y-ci + axe-core on the web control interface
                 (only when web/ files change)
```

### `ai-pr-review.yml` — AI PR Reviewer

Adapted from artemis:

- [ ] Triggers on every opened/synchronised/reopened PR.
- [ ] Uses GitHub Models API (Codestral-2501).
- [ ] Dismisses stale `REQUEST_CHANGES` reviews on re-push.
- [ ] Incremental review: checks whether previously flagged issues were fixed.
- [ ] Reads `CLAUDE.md` guidelines on the first review of a PR.

**PiCam2-specific system prompt focus areas:**
```
1. CRITICAL: Threading safety — Tkinter vars (.get()/.set()) ONLY on the main thread.
   Worker threads must use root.after() callbacks.
2. CRITICAL: Camera resource management — always stop/close in finally blocks.
3. Single-config design — never call configure() or stop() on the running camera
   except for deliberate profile switches with a full restart sequence.
4. Pi 5 PiSP constraint — NoiseReductionMode must stay 0 when a raw stream
   is active. Warn on any code that modifies this without a platform check.
5. Type hints on all public methods.
6. No bare except — always catch specific exceptions.
7. Subprocess security — no shell=True; escape all user-supplied arguments.
8. File path safety — validate user-supplied paths; no open() on unchecked input.
```

### `ai-pr-review-on-comment.yml`

- [ ] Trigger AI review via a `/ai-review` comment on a PR.

### `security.yml` — Security Scanning

- [ ] **TruffleHog**: scans for secrets/credentials in commits and PRs.
- [ ] **Semgrep**: Python + security rule sets; custom rules for subprocess injection, path traversal, insecure `/tmp` usage.
- [ ] **pip-audit**: scans `requirements.txt` for known CVEs.
- [ ] **Trivy**: Dockerfile config scan (when added).
- [ ] Scheduled weekly (Monday 6 AM UTC) + on PR/push to main.

### `semgrep.yml`

- [ ] Standalone Semgrep with `SEMGREP_APP_TOKEN`; daily cron + manual trigger.

### `license-check.yml` — License Compliance

- [ ] `pip-licenses` audits all Python dependencies.
- [ ] Flags non-permissive licenses (GPL, AGPL) that conflict with the project's MIT license.
- [ ] Weekly scheduled run + on PRs that modify `requirements.txt`.
- [ ] Monthly detailed license audit artifact.

### Self-Hosted Pi Runner

- [ ] Register a Raspberry Pi 5 as a GitHub Actions self-hosted runner.
- [ ] Runner tagged `[self-hosted, raspberry-pi, pi5]`.
- [ ] Only the `hil-test` job uses the self-hosted runner.
- [ ] Runner has the IMX477 camera and GPIO hardware attached.

### Dependabot

- [ ] Enable Dependabot for `requirements.txt` (weekly Python dependency updates).
- [ ] Enable Dependabot for GitHub Actions workflow versions.

---

## Deferred / Low Priority Items

- **GPS EXIF support** — lowest priority; add `gpsd-py3` integration when time permits.
- **DOL-HDR** — requires sensor-level support not yet in libcamera stable.
- **Video stabilisation** — software only; lower priority.
- **Image watermark tool** — post-processing CLI; low urgency.
- **Lens shading control** — via custom tuning JSON; complex to implement correctly.
- **IR remote** — explicitly excluded; Bluetooth HID and web remote are the supported paths.
- **Zero Shutter Lag** — research `ZeroShutterLag` mode for Pi 4 later.
- **Python module packaging** — pip-installable module for a future release.
- **Face detection** — OpenCV haarcascade; deferred to astrophotography/science phase.

---

## Colour Profile Implementation Notes

The v1.5 config already pointed at the correct default:
```python
"colour_profile_path": "/home/pi/Colour_Profiles/imx477/Raspberry Pi High Quality Camera Lumariver 2860k-5960k Neutral Look.json"
```

In V2, the profile is loaded **before** `configure()`:

```python
tuning = Picamera2.load_tuning_file(
    "Raspberry Pi High Quality Camera Lumariver 2860k-5960k Neutral Look.json",
    dir=str(COLOUR_PROFILES_DIR / "imx477")
)
cam = Picamera2(tuning=tuning)
cam.configure(config)
cam.start()
```

**Runtime profile switching** requires a full restart (~2 s on Pi 5):
1. `cam.stop()` → `cam.close()`.
2. Re-instantiate `Picamera2(tuning=new_tuning)`.
3. Reconfigure and restart.
4. Restore controls from settings.

**Sensor → profile auto-selection map:**
```python
SENSOR_PROFILE_DEFAULTS = {
    "imx477": "imx477/Raspberry Pi High Quality Camera Lumariver 2860k-5960k Neutral Look.json",
    "imx219": "imx219/default.json",
}
```

---

## Sensor Support Matrix

| Sensor | Module | Resolution | Raw Format | AF | Colour Profile |
|--------|--------|------------|------------|-----|----------------|
| IMX477 | HQ Camera | 4056×3040 | SRGGB12 | No | ✅ Lumariver custom |
| IMX219 | V2 Camera | 3280×2464 | SRGGB10 | No | Built-in |
| IMX296 | Global Shutter | 1456×1088 | SRGGB10 | No | Built-in |
| OV9281 | Global Shutter Mono | 1280×800 | Y8/Y10 | No | N/A |
| IMX519 | ArduCam 16MP AF | 4656×3496 | SRGGB10 | ✅ | Built-in |
| AR0234 | ArduCam Global | 1920×1200 | SGRBG10 | No | Built-in |

---

## Known Hardware Constraints

| Constraint | Platform | Mitigation |
|---|---|---|
| PiSP TDN crash on mode switch | Pi 5 | Single-config design |
| One concurrent camera stream | Pi 4 | Sequential sensor switching; no dual-sensor |
| Raw stream memory (~15 MB/frame) | All | `buffer_count=2`; RAMDrive flush |
| `set_tuning_file()` requires restart | All | Accept ~2 s delay on profile switch |
| GPIO requires `gpiozero` / `RPi.GPIO` | All | Graceful fallback on non-Pi |
| DSP touchscreen multi-touch limited | Pi 5 DSP | `xinput` events for best pinch support |
| No OIS on any Pi camera module | All | Software stabilisation only |

---

## UI Theme & Visual Design System

### Current Theme (PoC)

Dark blue palette defined as constants in the PoC:
```python
BG_DARK  = "#1a1a2e"
BG_MID   = "#16213e"
BG_PANEL = "#0f3460"
ACCENT   = "#e94560"
```

### Theme System Plan

- [ ] Implement `ThemeManager` loading a theme from `~/.config/picam2/theme.json` or `--theme` CLI flag.
- [ ] Each theme defines a colour palette dict: `bg_dark`, `bg_mid`, `bg_panel`, `accent`, `text_light`, `text_dim`, `btn_capture`, `btn_ok`, `btn_warn`.
- [ ] Theme is applied globally through a style registry; hot-swap without restart.

### Planned Built-in Themes

| Theme | Description | Use Case |
|---|---|---|
| `dark_blue` | PoC default — navy/teal/red | General use |
| `dark_red` | Crimson/charcoal | Alternative aesthetic |
| `night_mode` | Deep red-on-black | Astrophotography — preserves dark-adapted vision |
| `high_contrast` | White/yellow on black | Outdoor bright light readability |
| `classic` | Grey/green terminal feel | Nostalgic; v1.5 callback |

### Font Plan

- [ ] `FontRegistry` with named font roles: `ui_small`, `ui_body`, `ui_label`, `vf_overlay`, `status`, `mono`.
- [ ] Defaults: Helvetica (labels), Courier (status/metadata), system monospace (log viewer).
- [ ] Font sizes scale with screen resolution (larger on 1080p+, smaller on 800×480).
- [ ] `--font-scale` CLI flag for accessibility.
- [ ] Fonts configurable per theme.

### Responsive Layout

- [ ] **Compact mode** (800×480 DSP): minimal visible controls, collapsible side panel, viewfinder maximised.
- [ ] **Standard mode** (1080p+): full side panel with all controls visible.
- [ ] Auto-detected from window geometry or `--layout compact|standard` CLI flag.

### Future Theme Possibilities

- [ ] User-defined themes via a JSON editor in Settings → Appearance.
- [ ] High-DPI / Retina support for 4K HDMI displays.
