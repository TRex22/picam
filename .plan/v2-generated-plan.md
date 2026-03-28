# PiCam V2 — Migration & Development Plan

> **From:** v1.5 (legacy picamera/MMAL, Pi 4, framebuffer, GPIO buttons, headless)
> **To:** V2 (picamera2/libcamera, Pi 5, DSP touchscreen, Tkinter desktop GUI)
> **Proof of Concept baseline:** `picam2_proof_of_concept.py`
> **Target platforms:** Raspberry Pi 4 & 5
> **Date:** March 2026

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Repository Structure](#repository-structure)
3. [Phase 0 — PoC Fixes & Stabilisation](#phase-0--poc-fixes--stabilisation)
4. [Phase 1 — Core Foundation](#phase-1--core-foundation)
5. [Phase 2 — Camera Features](#phase-2--camera-features)
6. [Phase 3 — Storage & Output](#phase-3--storage--output)
7. [Phase 4 — UI & Touchscreen](#phase-4--ui--touchscreen)
8. [Phase 5 — Advanced Imaging](#phase-5--advanced-imaging)
9. [Phase 6 — Connectivity & Remote](#phase-6--connectivity--remote)
10. [Phase 7 — Video & Audio](#phase-7--video--audio)
11. [Phase 8 — Hardware & Platform](#phase-8--hardware--platform)
12. [Phase 9 — Astrophotography & Science Modes](#phase-9--astrophotography--science-modes)
13. [Phase 10 — Polish & Distribution](#phase-10--polish--distribution)
14. [Deferred / Research Items](#deferred--research-items)
15. [Colour Profile Implementation Notes](#colour-profile-implementation-notes)
16. [Sensor Support Matrix](#sensor-support-matrix)
17. [Known Hardware Constraints](#known-hardware-constraints)

---

## Architecture Overview

V2 adopts a clean layered architecture to replace the tangled v1.5 MMAL handler spaghetti:

```
┌─────────────────────────────────────────────┐
│              UI Layer (Tkinter)             │
│  PiCamApp  ·  Panels  ·  Overlays  ·  Touch │
├─────────────────────────────────────────────┤
│            Application Layer                │
│  SettingsManager  ·  CaptureController      │
│  TimerController  ·  BufferManager          │
├─────────────────────────────────────────────┤
│             Camera Abstraction              │
│  CameraBackend (abstract)                   │
│    └─ Picamera2Backend  (Pi 4 & 5)          │
│    └─ DemoBackend       (dev/no-Pi)         │
├─────────────────────────────────────────────┤
│           Hardware / Platform               │
│  SensorRegistry  ·  ColourProfileManager    │
│  GPIOManager     ·  BatteryMonitor          │
│  ScreenManager   ·  TempMonitor             │
└─────────────────────────────────────────────┘
```

**Key design decisions carried forward from the PoC:**
- **Single-configuration model** — never reconfigure the camera at runtime; prevents the Pi 5 PiSP TDN crash.
- **Main-thread capture of Tkinter vars** — all `StringVar`/`DoubleVar/.get()` calls happen on the Tk main thread before handing off to worker threads.
- **Raw stream always on** — raw Bayer stream runs continuously alongside the RGB preview; capture is a grab-from-queue operation with no mode switch.

---

## Repository Structure

```
picam/
├── src/
│   ├── main.py                   # entry point
│   ├── app.py                    # PiCamApp (Tkinter root)
│   ├── camera/
│   │   ├── backend.py            # abstract CameraBackend
│   │   ├── picamera2_backend.py  # libcamera / picamera2 impl
│   │   ├── demo_backend.py       # headless demo / dev mode
│   │   ├── sensor_registry.py    # sensor detection & caps
│   │   └── colour_profiles.py    # profile loading & embedding
│   ├── ui/
│   │   ├── viewfinder.py         # live preview widget
│   │   ├── control_panel.py      # right-hand controls
│   │   ├── overlays.py           # zebra, focus peaking, histogram
│   │   ├── touch_handler.py      # pinch/zoom/drag for touchscreen
│   │   └── screen_manager.py     # HDMI / DSP / framebuffer
│   ├── storage/
│   │   ├── capture_controller.py # still + video save logic
│   │   ├── exif_writer.py        # EXIF/XMP metadata injection
│   │   ├── ramdrive.py           # /dev/shm in-memory buffer
│   │   └── samba.py              # smbd integration helpers
│   ├── hardware/
│   │   ├── gpio_manager.py       # dynamic GPIO button mapping
│   │   ├── battery_monitor.py    # I²C / GPIO voltage tracking
│   │   └── temp_monitor.py       # CPU/GPU temp via vcgencmd
│   └── settings/
│       ├── settings_manager.py   # load / save / defaults
│       └── defaults.py           # factory defaults per sensor
├── colour_profiles/              # git submodule → trex22/Colour_Profiles
├── case/                         # 3D models (STL / OpenSCAD)
├── docs/
├── tools/                        # CLI utilities (exif tool, intrinsics, etc.)
├── web/                          # future web-control interface
├── install.sh
├── requirements.txt
└── .plan/
```

---

## Phase 0 — PoC Fixes & Stabilisation

> Fix all issues identified in the proof-of-concept before building on top of it.

### P0.1 — Preview Aspect Ratio

- [ ] Compute viewfinder dimensions to exactly match the sensor's native aspect ratio (IMX477 = 4056:3040 = 4:3). Currently the preview window is 573×366 which is approximately 11:7 — slightly stretched.
- [ ] Add a helper `aspect_fit(sensor_w, sensor_h, container_w, container_h)` that returns the largest rect preserving ratio with letterbox/pillarbox padding.
- [ ] Pass `{"size": aspect_fit(...)}` to `create_preview_configuration` so the capture stream and display are pixel-consistent.

### P0.2 — Drop-down Text Visibility

- [ ] The combobox text is currently invisible (white-on-white or dark-on-dark depending on system theme). Force `foreground=TEXT_LIGHT` on the drop-down list widget, not just the field.
- [ ] Apply `ttk.Style` patch for `TCombobox` popdown background: `style.map("TCombobox", fieldbackground=[("readonly", BG_PANEL)], ...)`.
- [ ] Consider switching to a custom `tk.OptionMenu` for more reliable cross-theme styling.

### P0.3 — Proper Fullscreen / Display Mode

- [ ] Add `--fullscreen` CLI flag and corresponding `root.attributes("-fullscreen", True)`.
- [ ] Add `--geometry WxH` flag for fixed-resolution DSP screens (e.g. `800x480`).
- [ ] Hide the window manager title bar in fullscreen mode.
- [ ] Re-layout viewfinder to fill the full screen when in fullscreen mode, moving controls to a collapsible overlay panel.

### P0.4 — Capture Confirmation Feedback

- [ ] Flash a brief green border/overlay on the viewfinder for ~500 ms after a successful capture.
- [ ] Play a shutter sound (optional, configurable via settings).
- [ ] Show a thumbnail of the last captured image in the status bar or a small pop-up panel.
- [ ] Clear the "Saved ✓" status after 3 seconds; revert to "Ready".

### P0.5 — EXIF Data Improvements

- [ ] Use `piexif` or `exiftool` (subprocess) to inject:
  - Accurate `DateTimeOriginal` from `datetime.now()`.
  - `Make` = `"Raspberry Pi"`, `Model` = `"PiCam2 v{VERSION}"`.
  - `LensModel` from the sensor registry or user-configured string.
  - Connected sensor name in `UserComment`.
  - Shutter speed, ISO, aperture (from applied controls metadata).
- [ ] For DNG output: embed EXIF directly via `request.save_dng()` metadata overrides or post-process with `exiftool`.

### P0.6 — Settings File

- [ ] Implement `SettingsManager` that reads/writes `~/.config/picam2/settings.json`.
- [ ] On first boot, write defaults. On subsequent boots, restore last-used values.
- [ ] All UI control variables (`iso`, `shutter`, `awb`, `brightness`, etc.) persist to this file on change.
- [ ] Add a "Save as Default Boot State" button in the UI.

### P0.7 — White Balance Controls

- [ ] Expose `ColourGains` (red gain, blue gain) as two float sliders, visible when AWB is disabled.
- [ ] Add `AwbMode` combobox (Auto / Incandescent / Tungsten / Fluorescent / Indoor / Daylight / Cloudy / Custom).
- [ ] When `AwbEnable=False` and custom gains are set, pass `ColourGains=(r, b)` in the controls dict.

---

## Phase 1 — Core Foundation

### P1.1 — Abstract Camera Backend

- [ ] Define `CameraBackend` abstract base class with interface:
  ```python
  def start(self, config: CameraConfig) -> None
  def stop(self) -> None
  def capture_preview_frame(self) -> Image.Image | None
  def capture_still(self, controls: dict, path: Path, format: str) -> Path
  def apply_controls(self, controls: dict) -> None
  def get_metadata(self) -> dict
  def get_sensor_info(self) -> SensorInfo
  ```
- [ ] Implement `Picamera2Backend` wrapping the PoC's `Camera` class with the single-config design.
- [ ] Implement `DemoBackend` that generates synthetic frames (useful for dev on non-Pi hardware).

### P1.2 — Sensor Registry

- [ ] Auto-detect connected sensor(s) via `Picamera2().camera_properties`.
- [ ] Define a `SensorInfo` dataclass: `name`, `model_id`, `native_resolution`, `base_iso`, `max_gain`, `has_raw`, `supported_formats`, `default_colour_profile`.
- [ ] Ship built-in sensor definitions for:
  - IMX477 (HQ Camera, 12.3 MP)
  - IMX219 (V2 Camera, 8 MP)
  - IMX296 (Global Shutter)
  - OV9281 (Global Shutter mono)
  - ArduCam IMX519 (16 MP AF)
  - ArduCam 64 MP (Hawkeye)
- [ ] Sensor registry is extensible via a user JSON config.

### P1.3 — Colour Profile System *(highest priority)*

- [ ] Add `colour_profiles/` as a git submodule pointing to `https://github.com/trex22/Colour_Profiles.git`.
- [ ] Implement `ColourProfileManager`:
  - Discover `.json` profile files for the detected sensor.
  - Expose a combobox in the UI listing available profiles (e.g. "Lumariver Neutral 2860k-5960k", "Default", "None").
  - **Default for IMX477**: auto-select `Raspberry Pi High Quality Camera Lumariver 2860k-5960k Neutral Look.json` if present.
  - Pass the selected profile path to `Picamera2.set_tuning_file()` **before** `configure()` is called (this must happen at startup, not at capture time).
- [ ] Support runtime profile switching by restarting the camera with the new tuning file (since `set_tuning_file()` requires a restart).
- [ ] For DNG output: embed the profile name in `UserComment` EXIF. Optionally embed the ICC profile bytes via `exiftool -icc_profile=...`.
- [ ] Expose a "Embed colour profile in output" toggle in Settings.
- [ ] v1.5 reference: `config["colour_profile_path"]` already pointed at the Lumariver profile — preserve this default.

### P1.4 — Pi 4 / Pi 5 Compatibility Layer

- [ ] Detect hardware platform at startup (`/proc/device-tree/model`).
- [ ] On Pi 4 (BCM2711, non-PiSP): `NoiseReductionMode` can be set freely without TDN constraint.
- [ ] On Pi 5 (BCM2712, PiSP): enforce `NoiseReductionMode=0` when raw stream is active (as in the PoC).
- [ ] Abstract this into `CameraConfig.noise_reduction_mode` with platform-aware defaults.
- [ ] Test both `PISP_COMP1` (Pi 5) and `SRGGB10_CSI2P` (Pi 4) raw formats.

---

## Phase 2 — Camera Features

### P2.1 — AWB Manual Gains

- [ ] *(see P0.7 above)*

### P2.2 — Multi-Sensor Support

- [ ] On startup, enumerate cameras via `Picamera2.global_camera_info()`.
- [ ] Add a "Sensor" combobox at the top of the control panel.
- [ ] Switching sensors stops the current backend, reinitialises with new sensor's profile/config, and restarts the preview.
- [ ] Preserve per-sensor settings independently in `settings.json`.

### P2.3 — Dual Sensor Support

- [ ] When two sensors are detected, offer a "Dual" mode.
- [ ] Dual mode: two `Picamera2` instances, two preview windows (side-by-side or toggle).
- [ ] Dual capture: fire both simultaneously in separate threads; save with matching timestamps.
- [ ] Note: Pi 5 can handle two camera streams; Pi 4 is limited to one at a time.

### P2.4 — ArduCam Autofocus Support

- [ ] Detect ArduCam AF modules (IMX519, 64MP) via camera properties.
- [ ] Expose `AfMode` combobox: Manual / Continuous / Auto-on-capture.
- [ ] Expose `LensPosition` slider for manual focus (0.0 to 1.0, maps to dioptre).
- [ ] Trigger `AutoFocusCycle` on shutter-half-press (GPIO) or tap on the focus window.

### P2.5 — ISO Simulation in Preview

> Shutter Speed Simulation in Preview

- [ ] When a long shutter speed (>1/30s) is selected, the preview should darken proportionally to simulate the exposure visually (rather than always showing a full-brightness live feed).
- [ ] Implement by adjusting `AnalogueGain` inversely during preview when `ExposureTime` is fixed.

### P2.6 — Dead Pixel Correction Modes

- [ ] DPC is already in the PoC via `NoiseReductionMode`. Keep this.
- [ ] Add a note in the UI tooltip that on-sensor DPC (mapped/dynamic, modes 1–3) is separate from this ISP NR control.
- [ ] Long-term: allow tuning JSON DPC masks to be loaded for astrophotography (where mapped DPC is preferred over dynamic DPC).

### P2.7 — Metering Modes

- [ ] Add `AeMeteringMode` combobox: Centre-weighted / Spot / Matrix / Custom.
- [ ] Link to `libcamera` `AeMeteringModeEnum`.

### P2.8 — Exposure Compensation (EV)

- [ ] Add `ExposureValue` slider: −4 EV to +4 EV in 1/3-stop steps.
- [ ] Active only when `AeEnable=True`.

---

## Phase 3 — Storage & Output

### P3.1 — Save Format Options

- [ ] Replace the single "CAPTURE DNG" button with a configurable capture pipeline.
- [ ] Add format options in Settings:
  - `RAW only (DNG)`
  - `JPEG only`
  - `PNG only`
  - `RAW + JPEG (dual save)`
  - `RAW + PNG (dual save)`
- [ ] JPEG/PNG saved from the `main` (processed RGB) stream at full sensor resolution via `capture_array("main")` resized to sensor res, or via a dedicated high-res still config.
- [ ] JPEG quality slider (1–100, default 95).
- [ ] PNG compression slider (0–9, default 6).

### P3.2 — In-Memory Buffer (RAMDrive)

- [ ] Create a `/dev/shm/picam/` RAMDrive buffer (Pi 5 has 8 GB RAM; allocate up to 2 GB as a ring buffer).
- [ ] Write captures to RAMDrive first, then flush to persistent storage asynchronously in a background thread.
- [ ] Add a `BufferManager` that tracks pending flushes and shows a progress indicator.
- [ ] Burst mode: capture N frames in rapid succession to RAMDrive, flush afterwards.
- [ ] Configurable: RAMDrive size limit, flush-to-disk immediately vs. deferred.

### P3.3 — DCIM Directory Structure

- [ ] Adopt standard DCIM structure: `~/Pictures/DCIM/YYYYMMDD/IMG_YYYYMMDD_HHMMSS.dng`.
- [ ] Configurable DCIM root path in settings.
- [ ] Collision-safe naming (already in PoC — keep and extend to JPEG/PNG).

### P3.4 — Colour Profile Embedding

- [ ] For DNG: embed the active tuning profile name in EXIF `UserComment`; optionally inject ICC profile via `exiftool`.
- [ ] For JPEG/PNG: embed ICC profile bytes directly in the file (Pillow supports `save(..., icc_profile=bytes)`).
- [ ] For XMP sidecar: write a `.xmp` alongside each DNG noting the colour profile used.

### P3.5 — GPS EXIF Support

- [ ] Detect USB/serial GPS modules (e.g. GlobalSat, u-blox via `gpsd`).
- [ ] If `gpsd` is running, poll `gps.fix` at capture time and embed `GPSLatitude`, `GPSLongitude`, `GPSAltitude` in EXIF.
- [ ] GPS support is a toggle in Settings (off by default).
- [ ] Show GPS lock indicator (satellite icon) in the status bar when a fix is active.

### P3.6 — Samba / Network Share

- [ ] Add `samba.py` helper that writes a minimal `smb.conf` sharing the DCIM folder.
- [ ] Install script installs `samba` if not present.
- [ ] Settings toggle: "Share DCIM over Samba". Restarts `smbd` on change.
- [ ] Advertise share via mDNS (Avahi) so macOS Finder and Windows can discover it.

### P3.7 — PTP/MTP Mount (Image Capture / Darktable Import)

- [ ] Enable PTP over USB using `gphoto2`'s virtual camera daemon or `libgphoto2`.
- [ ] This allows macOS Image Capture and Darktable (via `gphoto2` input) to mount PiCam2 as a camera.
- [ ] Add install script step for `gphoto2`, `libgphoto2-dev`.
- [ ] Alternative: advertise DCIM via Samba and configure Darktable to watch a network folder.

### P3.8 — Darktable on Device

- [ ] Add optional install step in `install.sh` for `darktable` (ARM64 package available on Bookworm).
- [ ] Add a "Open in Darktable" context menu on last-captured image.

---

## Phase 4 — UI & Touchscreen

### P4.1 — Focus Window (Draggable / Resizable)

- [ ] Draw a semi-transparent rectangle overlay on the viewfinder.
- [ ] Bind mouse `<Button-1>`, `<B1-Motion>` for drag; resize handles at corners.
- [ ] Pass the normalised focus window rect as `AfWindows` (AF) and `AeExposureMode`/`ScalerCrop` (AE) to libcamera controls.
- [ ] Focus window doubles as digital zoom region (see P4.2).

### P4.2 — Touch Zoom (Pinch / Expand)

- [ ] Implement touch event handler for DSP touchscreen using `<ButtonPress>`, `<ButtonRelease>`, and multi-touch via `xinput` events or a custom touch driver shim.
- [ ] Pinch-to-zoom: map touch spread to `ScalerCrop` (digital zoom) in libcamera — narrows the crop window on the sensor, effectively zooming.
- [ ] Zoom level indicator overlay (e.g. "2.1×") on viewfinder.
- [ ] Long-press on viewfinder: set focus point (triggers `AutoFocusCycle` at that position).

### P4.3 — Collapsible Control Panel

- [ ] In fullscreen mode, collapse the right-hand panel to a thin tab with an expand arrow.
- [ ] Animate expand/collapse using `after()`-based geometry tweening.
- [ ] Swipe in from right edge of touchscreen to expand.

### P4.4 — Screen Brightness Control

- [ ] Write to `/sys/class/backlight/*/brightness` for DSP/HDMI screens that expose a sysfs backlight interface.
- [ ] Add a brightness slider in Settings → Display.
- [ ] Auto-dim after N seconds of inactivity (configurable).

### P4.5 — Overlay Indicators

**Focus Peaking (Zebra-style)**
- [ ] Every N frames (configurable, e.g. every 3rd), compute the Laplacian of the preview frame.
- [ ] Highlight high-frequency edges in a configurable colour (default: red) overlaid on the live view.
- [ ] Toggle button in the control panel.

**Histogram**
- [ ] Draw a live luminance/RGB histogram in a corner of the viewfinder.
- [ ] Computed using NumPy on the preview array; rendered as a small canvas widget.
- [ ] Toggle and corner position configurable.

**Zebra Stripes (Overexposure)**
- [ ] Pixels above a configurable threshold (e.g. 95% luminance) are striped with an alternating pattern.
- [ ] Toggle button; threshold slider.

**Grid Overlay**
- [ ] Rule-of-thirds / square grid drawn over the viewfinder.
- [ ] Toggle and grid type (thirds, square, diagonal, centre-cross) configurable.

### P4.6 — Timer Delay

- [ ] Add a timer delay selector: Off / 2s / 5s / 10s / Custom.
- [ ] Countdown overlay on viewfinder (large digits).
- [ ] Audible beeps at 3, 2, 1 (if audio enabled).

### P4.7 — Capture Confirmation Flash

- [ ] *(see P0.4 above)*

### P4.8 — Shutter Speed Simulation in Preview

- [ ] *(see P2.5 above)*

---

## Phase 5 — Advanced Imaging

### P5.1 — Auto Mode

- [ ] "Auto" mode: all controls (ISO, shutter, AWB) set to Auto. Single button to reset to fully automatic.
- [ ] "Programme" mode: user sets one value, camera auto-handles the others.

### P5.2 — Burst / Continuous Shot

- [ ] Hold the capture button to enter burst mode; release to stop.
- [ ] Burst frames go to RAMDrive buffer; flushed after burst ends.
- [ ] Configurable max burst length and inter-frame delay.

### P5.3 — Stop Motion Mode

- [ ] Capture N frames with configurable interval.
- [ ] Overlay the last captured frame at reduced opacity as an onion skin.
- [ ] Output: numbered sequence or an assembled GIF/MP4.

### P5.4 — Camera Intrinsics Tool

- [ ] CLI tool (`tools/intrinsics.py`) that captures a checkerboard sequence and runs OpenCV camera calibration.
- [ ] Outputs `K`, distortion coefficients, and reprojection error.
- [ ] Save to `~/.config/picam2/intrinsics_{sensor}.json` for use by downstream tools.

### P5.5 — Lens EXIF Data Tool

- [ ] CLI tool (`tools/lens_exif.py`) that prompts for lens metadata (name, focal length, aperture, serial) and writes a profile JSON.
- [ ] This profile is injected into EXIF `LensModel`, `FocalLength`, `MaxApertureValue` at capture time.
- [ ] Especially useful for adapted M42 lenses (e.g. Vivitar with teleconverter) that have no electronic contacts.

### P5.6 — Image Statistics Overlay

- [ ] Per-capture: log mean luminance, highlight/shadow clipping percentage, colour temperature estimate to a JSON stats file alongside each DNG.

### P5.7 — HDR / DOL-HDR

- [ ] Research DOL-HDR support on IMX477 via libcamera extensions.
- [ ] Short-term: software HDR merge via bracketed exposures (capture at −2EV, 0EV, +2EV; merge with OpenCV).
- [ ] Add "HDR Bracket" capture mode to UI.

---

## Phase 6 — Connectivity & Remote

### P6.1 — Web Control Interface

- [ ] Implement a lightweight Flask or FastAPI server (`web/server.py`).
- [ ] Serves a responsive web UI mirroring the desktop controls.
- [ ] Live MJPEG stream endpoint: `/stream`.
- [ ] Capture endpoint: `POST /capture`.
- [ ] Settings endpoint: `GET/PUT /settings`.
- [ ] Accessible from any device on the local network; Bonjour/Avahi advertises `picam2.local`.

### P6.2 — GPIO Button Mapping

- [ ] Implement `GPIOManager` using `gpiozero` (Pi 4 & 5 compatible).
- [ ] Settings: map each GPIO pin to an action: Capture, TimerCapture, ToggleAWB, ZoomIn, ZoomOut, ToggleOverlay, Shutdown, etc.
- [ ] Default mapping preserves the original v1.5 GPIO layout for backwards compatibility.
- [ ] GPIO config stored in `settings.json` under `"gpio_map": {pin: action}`.

### P6.3 — Remote Control Support

- [ ] Bluetooth shutter remote: detect HID button press events (e.g. from a phone remote or BT shutter button) and map to capture action.
- [ ] IR remote: via `lirc` — map IR codes to actions.
- [ ] Both optional and configurable.

---

## Phase 7 — Video & Audio

### P7.1 — Video Capture

- [ ] Add a "VIDEO" mode toggle in the UI (separate from still capture).
- [ ] Use `picamera2` encoder: `H264Encoder` with configurable bitrate.
- [ ] Record to `~/Videos/DCIM/VID_YYYYMMDD_HHMMSS.mp4` (wrapped with `FfmpegOutput`).
- [ ] Resolutions: 1080p30, 1080p60 (Pi 5 only), 720p60, 4K (Pi 5 only).
- [ ] FPS selector linked to resolution.
- [ ] Bitrate controls: slider from 1 Mbps to 50 Mbps.

### P7.2 — RAW Video

- [ ] Capture raw Bayer video to `.raw` binary or `.dng` sequence using `picamera2`'s `DngEncoder` or `MJPEGEncoder` on the raw stream.
- [ ] Note: raw video at full sensor resolution generates ~15 MB/frame; RAMDrive buffer is essential.
- [ ] Offer downsampled raw video (e.g. 2028×1520 @ 40fps) for more manageable file sizes.

### P7.3 — Audio Input

- [ ] Detect USB/3.5mm audio input via `arecord -l`.
- [ ] Record audio alongside video using `ffmpeg` as a subprocess muxer.
- [ ] Audio codec: AAC or PCM, configurable.
- [ ] VU meter overlay in video mode.

### P7.4 — Video Stabilisation

- [ ] Software: `libcamera` has an `Af` stabilisation hint; implement via `ScalerCrop` jitter correction using optical flow between frames.
- [ ] Hardware: note that Pi cameras don't have OIS; software-only.

---

## Phase 8 — Hardware & Platform

### P8.1 — Battery Monitor

- [ ] Detect common Pi battery HATs (PiJuice, Waveshare, Pimoroni LiPo SHIM) via I²C.
- [ ] `BatteryMonitor` polls charge level, voltage, and charging status every 30 seconds.
- [ ] Display battery percentage and icon in the status bar.
- [ ] Low-battery warning overlay at 15%; auto-shutdown at 5% (configurable).
- [ ] Battery percentage tracking persists to `settings.json` for boot display.

### P8.2 — Screen Support Matrix

| Display Type | Notes |
|---|---|
| DSP Touchscreen (800×480) | Primary target for v2 |
| HDMI (any resolution) | Fullscreen / windowed |
| Framebuffer (legacy) | For Pi 4 headless; v1.5 compatibility mode |

- [ ] Auto-detect display type at startup.
- [ ] `ScreenManager` selects rendering backend (Tkinter/X11 for desktop; direct framebuffer via `pygame` or `fbdev` for headless).

### P8.3 — Fast Boot

- [ ] Disable unnecessary services: `bluetooth`, `avahi-daemon` (unless Samba/mDNS needed), `triggerhappy`, `ModemManager`.
- [ ] Enable `systemd` service for PiCam2 with `After=graphical-session.target`.
- [ ] Target boot-to-live-view in < 10 seconds on Pi 5 with `raspi-config` optimisations.
- [ ] Consider `plymouth` splash screen showing the PiCam2 logo during boot.

### P8.4 — Auto Login & Auto-Run

- [ ] `install.sh` configures autologin via `raspi-config nonint do_boot_behaviour B4` (desktop autologin).
- [ ] `.config/autostart/picam2.desktop` entry launches the app on session start.
- [ ] Alternatively: `systemd --user` service with `After=graphical-session.target`.

### P8.5 — Power Optimisation

- [ ] Disable HDMI if running on DSP only (`tvservice -o`).
- [ ] Reduce CPU governor to `powersave` when idle; switch to `performance` during capture.
- [ ] Disable WiFi if not needed (configurable via settings).
- [ ] Screen auto-dim (see P4.4).

### P8.6 — Temperature Monitoring

- [ ] Poll `vcgencmd measure_temp` every 60 seconds.
- [ ] Display CPU temp in the status bar (shown in red above 80°C).
- [ ] Log temperature alongside each capture in the stats JSON.
- [ ] Throttle warning overlay if `vcgencmd get_throttled` returns non-zero.

### P8.7 — 3D Case Improvements

- [ ] Improved cage STL models with handles (ergonomic grip for handheld use).
- [ ] Mounting points for the battery pack (eliminate the "physical battery pack issues" from the Optimisation List).
- [ ] Cold shoe mount for external mic/monitor.
- [ ] Ventilation slots for thermal management.
- [ ] Source files in OpenSCAD in `case/` for parametric customisation.

---

## Phase 9 — Astrophotography & Science Modes

> From the legacy `todo.md` astrophotography items.

### P9.1 — Astrophotography Mode

- [ ] Long exposure presets: 10s, 30s, 60s, 120s, 300s, bulb (custom duration).
- [ ] Disable all ISP processing (NR off, sharpening off, contrast=1.0, saturation=1.0).
- [ ] Dark frame subtraction: capture a dark frame (lens cap on, same exposure settings) and subtract from the light frame in software.
- [ ] Star eater avoidance: confirm `MMAL_PARAMETER_DPC` is not aggressively removing faint point sources; test empirically.
- [ ] Integration with `mosaic_stitch.py` for stacking sequences.

### P9.2 — Motion Detection / Motion Vectors

- [ ] Use libcamera's motion vector output (available from the H.264 encoder) for motion detection.
- [ ] Trigger capture on motion (security camera / wildlife mode).
- [ ] Configurable sensitivity and region of interest.

### P9.3 — Face Detection Mode

- [ ] OpenCV `haarcascade_frontalface_default.xml` running on preview frames in a background thread.
- [ ] Draw bounding boxes on the viewfinder.
- [ ] Auto-focus and AE lock on detected face region.

### P9.4 — Edge Detection / Computer Vision Overlays

- [ ] Canny edge detection overlay (useful for focus confirmation at the pixel level).
- [ ] Toggle in the overlay panel.
- [ ] Runs on a downsampled copy of the preview frame to avoid blocking the main thread.

---

## Phase 10 — Polish & Distribution

### P10.1 — Install Script (`install.sh`)

- [ ] Update to handle Pi 4 and Pi 5 (detect via `/proc/device-tree/model`).
- [ ] Install Python dependencies: `python3-picamera2`, `python3-pil`, `python3-pil.imagetk`, `python3-piexif`, `python3-gps`, `python3-numpy`, `python3-opencv`.
- [ ] Clone/update `colour_profiles` submodule.
- [ ] Optionally install `darktable`, `samba`, `gphoto2`.
- [ ] Configure autologin and autostart.
- [ ] Write default `settings.json`.

### P10.2 — `requirements.txt`

```
picamera2>=0.3.12
Pillow>=10.0
piexif>=1.1.3
numpy>=1.24
gpsd-py3>=0.3.0
gpiozero>=2.0
```

### P10.3 — Logging

- [ ] Replace `print()` calls with `logging` module.
- [ ] Log levels: DEBUG / INFO / WARN / ERROR.
- [ ] Log file: `~/.local/share/picam2/picam2.log` with rotation (max 5 MB × 3 files).
- [ ] In-app log viewer (collapsible panel at the bottom, toggle with a key shortcut).

### P10.4 — Tests

- [ ] Unit tests for `SettingsManager`, `ColourProfileManager`, `SensorRegistry`, `ExifWriter`.
- [ ] Integration test using `DemoBackend` to exercise the full capture pipeline without hardware.
- [ ] CI: GitHub Actions workflow running tests on Ubuntu (no Pi required, using `DemoBackend`).

### P10.5 — README & Docs

- [ ] Update `README.md` for V2 with install instructions, supported hardware, screenshots.
- [ ] `docs/SENSORS.md` — sensor support matrix.
- [ ] `docs/COLOUR_PROFILES.md` — how to use and create colour profiles.
- [ ] `docs/GPIO.md` — button mapping reference.

### P10.6 — Versioning

- [ ] Adopt semantic versioning: `2.0.0`.
- [ ] `VERSION` constant in `main.py`; embedded in EXIF and window title.
- [ ] Git tags for releases.

---

## Deferred / Research Items

These items are noted for future consideration but are not on the critical path for V2.

- **DOL-HDR** — requires sensor-level support; research libcamera extensions when available.
- **Lens shading control** — via custom tuning JSON; complex to implement correctly.
- **Video stabilisation** — software only; lower priority given the fixed-mount use case.
- **Image watermark tool** — post-processing CLI tool; low urgency.
- **Photo viewer** — a standalone photo viewer within PiCam2; consider deferring to Darktable.
- **Black level / digital gain controls** — advanced; expose later as part of an "Expert" settings panel.
- **Flicker avoidance** — `AeFlickerMode` control; useful in fluorescent lighting.
- **Zero shutter lag** — investigate `ZeroShutterLag` mode in picamera2 for Pi 4.
- **Field of view / ScalerCrop tool** — already partially covered by zoom; full FOV selector later.
- **Python module packaging** — package PiCam2 as a pip-installable module.

---

## Colour Profile Implementation Notes

The v1.5 config already hard-coded the correct path:
```python
"colour_profile_path": "/home/pi/Colour_Profiles/imx477/Raspberry Pi High Quality Camera Lumariver 2860k-5960k Neutral Look.json"
```

In V2, the profile must be loaded **before** `Picamera2.configure()`:

```python
from picamera2 import Picamera2

tuning = Picamera2.load_tuning_file("Raspberry Pi High Quality Camera Lumariver 2860k-5960k Neutral Look.json")
cam = Picamera2(tuning=tuning)
cam.configure(config)
cam.start()
```

**Profile switching at runtime** requires a full camera restart:
1. Call `cam.stop()` and `cam.close()`.
2. Re-instantiate `Picamera2(tuning=new_tuning)`.
3. Reconfigure and restart.
4. Restore controls from the settings dict.

This should take < 2 seconds on Pi 5 and is acceptable for a deliberate settings change.

**Sensor detection → profile auto-selection:**

```python
SENSOR_PROFILE_DEFAULTS = {
    "imx477": "imx477/Raspberry Pi High Quality Camera Lumariver 2860k-5960k Neutral Look.json",
    "imx219": "imx219/default.json",
    # etc.
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
| IMX519 | ArduCam 16MP | 4656×3496 | SRGGB10 | ✅ | Built-in |
| AR0234 | ArduCam Global | 1920×1200 | SGRBG10 | No | Built-in |

---

## Known Hardware Constraints

| Constraint | Platform | Mitigation |
|---|---|---|
| PiSP TDN crash on mode switch | Pi 5 only | Single-config design (already in PoC) |
| One camera at a time | Pi 4 | Sequential sensor switching; no dual-sensor on Pi 4 |
| Raw stream memory (~15 MB/frame) | All | `buffer_count=2`; RAMDrive flush |
| `set_tuning_file()` requires restart | All | Accept 2 s delay on profile switch |
| GPIO access requires `gpiozero` or `RPi.GPIO` | All | Graceful fallback if not on Pi |
| DSP touchscreen multi-touch limited | Pi 5 DSP | Use `xinput` events for best pinch support |
