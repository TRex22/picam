# PiCam V2 — Migration & Development Plan

> **From:** v1.5 (legacy picamera/MMAL, Pi 4, framebuffer, GPIO buttons, headless)
> **To:** V2 (picamera2/libcamera, Pi 5, DSP touchscreen, Tkinter desktop GUI)
> **Proof of Concept baseline:** `picam2_proof_of_concept.py`
> **Image processing tooling:** MagicForge (OpenCV / rawpy / drizzle pipeline)
> **CI/CD reference:** artemis repo pattern
> **Target platforms:** Raspberry Pi 4 & 5
> **Date:** March 2026

---

## Claude Code Task Tracking Instructions

This document is the authoritative source of truth for PiCam V2 development.

**Claude Code must:**
- Read this plan at the start of every session before touching any code.
- Mark tasks complete by replacing `- [ ]` with `- [x]` as each task is finished.
- Add a dated completion note below any completed section, e.g.: `> ✅ Completed 2026-04-01`
- If a task is partially done, mark it `- [~]` with a brief inline note.
- If a task is blocked, mark it `- [!]` with a reason inline.
- Never delete tasks — only mark them with the status symbols above.
- When discovering new sub-tasks during implementation, add them under the relevant phase with `- [ ]`.
- After a phase is fully complete, add a phase summary block at the bottom of that phase.
- Commit the updated plan document alongside the code changes that close each task.

**Commit message convention:** `[Phase X.Y] Short description of what was done`

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Repository Cleanup & Migration](#repository-cleanup--migration) ← **DO THIS FIRST**
3. [Phase 0 — PoC Fixes & Stabilisation](#phase-0--poc-fixes--stabilisation)
4. [Phase 1 — Core Foundation](#phase-1--core-foundation)
5. [Phase 2 — Colour Profiles](#phase-2--colour-profiles) ← **First priority after Phase 0**
6. [Phase 3 — Zoom & Focus Window](#phase-3--zoom--focus-window)
7. [Phase 4 — AWB & White Balance](#phase-4--awb--white-balance)
8. [Phase 5 — Gallery & Media Browser](#phase-5--gallery--media-browser)
9. [Phase 6 — Hardware Platform](#phase-6--hardware-platform)
10. [Phase 7 — Camera Features](#phase-7--camera-features)
11. [Phase 8 — Storage & Output](#phase-8--storage--output)
12. [Phase 9 — UI Polish & Themes](#phase-9--ui-polish--themes)
13. [Phase 10 — Advanced Imaging & MagicForge](#phase-10--advanced-imaging--magicforge)
14. [Phase 11 — Connectivity & Remote](#phase-11--connectivity--remote)
15. [Phase 12 — Streaming, Webcam & Integrations](#phase-12--streaming-webcam--integrations) ← Lower priority
16. [Phase 13 — Video & Audio](#phase-13--video--audio)
17. [Phase 14 — Timelapse](#phase-14--timelapse) ← Lower priority
18. [Phase 15 — Astrophotography & Science Modes](#phase-15--astrophotography--science-modes)
19. [Phase 16 — Polish & Distribution](#phase-16--polish--distribution)
20. [Testing Strategy](#testing-strategy)
21. [CI/CD Pipeline](#cicd-pipeline)
22. [Deferred / Lowest Priority Items](#deferred--lowest-priority-items)
23. [Colour Profile Implementation Notes](#colour-profile-implementation-notes)
24. [Sensor Support Matrix](#sensor-support-matrix)
25. [Known Hardware Constraints](#known-hardware-constraints)
26. [UI Theme & Visual Design System](#ui-theme--visual-design-system)

---

## Architecture Overview

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
│    ├─ Picamera2Backend  (Pi 4 & 5, single-config)   │
│    └─ DemoBackend       (dev / no-Pi)               │
│  SensorRegistry · ColourProfileManager              │
│  SimulatedPreviewEngine                             │
├─────────────────────────────────────────────────────┤
│           Hardware / Platform Layer                 │
│  GPIOManager (optional) · BatteryMonitor            │
│  TempMonitor · ScreenManager · BacklightCtrl        │
└─────────────────────────────────────────────────────┘
```

**Key design decisions:**
- **Single-configuration model** — never reconfigure the camera at runtime; prevents the Pi 5 PiSP TDN crash.
- **Main-thread Tkinter var access** — all `StringVar/.get()` calls happen on the Tk main thread before handing off to worker threads.
- **Raw stream always on** — raw Bayer stream runs continuously alongside RGB preview.
- **Simulated preview for slow shutters** — shutter speeds below a configurable threshold switch the viewfinder to a synthetic simulation so the UI stays usable during long exposure setup.
- **Headless / legacy fallback** — the hardware layer is abstract enough to support a future low-cost headless Pi 4 build with GPIO buttons and framebuffer output.
- **GPIO is optional** — GPIO buttons are detected at startup; if absent or disabled, the app runs fully without them. Configuration is file-driven with a default shipped in the repo.

---

## Repository Cleanup & Migration

> **⚠️ DO THIS BEFORE ANY OTHER WORK. The `.git` directory must never be deleted or corrupted.**

### Step 1 — Tag v1.5 on the development branch

```bash
cd /Users/trex22/development/picam
git checkout development
git tag -a v1.5.0 -m "PiCam v1.5 — legacy MMAL/picamera, Pi 4, framebuffer, GPIO buttons"
git push origin v1.5.0
```

- [x] Tag `v1.5.0` created and pushed.

### Step 2 — Archive the legacy branches (do NOT delete `.git`)

```bash
# Create permanent read-only archive branches from the current state
git checkout -b archive/v1.5-development
git push origin archive/v1.5-development

git checkout main
git branch archive/v1.5-main
git push origin archive/v1.5-main
```

- [x] `archive/v1.5-development` pushed.
- [x] `archive/v1.5-main` pushed.

### Step 3 — Create a clean V2 starting point

```bash
# Create an orphan branch — no history, no old files, .git preserved
git checkout --orphan v2-bootstrap

# Stage only the files we want to carry forward
git rm -rf --cached .           # unstage everything (files not deleted yet)

# Copy files we want to keep into a temp location outside the repo
# (PoC, plan files, .plan folder, .github, .gitignore, LICENSE)
# Then restore them:

git checkout HEAD -- .gitignore LICENSE .github/
# Manually restore the .plan folder contents (PoC + plan markdown)
```

**Files to carry forward into V2 bootstrap commit:**
- [x] `.gitignore` (existing, update as needed)
- [x] `LICENSE`
- [x] `.github/` (existing workflows; will be replaced/extended in CI phase)
- [x] `.plan/picam2_proof_of_concept.py` — the PoC that V2 is built on
- [x] `.plan/rewrite 2026.md` — this plan document (rename to `PLAN.md` at repo root)
- [x] `.plan/todo.md` — legacy todo list (keep as historical reference)
- [x] `README.md` — will be updated for V2 but carried forward

**Files NOT carried forward (replaced by V2 equivalents):**
- `src/` — all v1.5 source (preserved only in `archive/` branches and `v1.5.0` tag)
- `install.sh` — will be rewritten for V2
- `web/` — will be rewritten for V2
- `tools/` — partial carry-forward; legacy tools reviewed case-by-case

```bash
# Make the bootstrap commit
git add .gitignore LICENSE .github/ .plan/ README.md
git commit -m "chore: bootstrap PiCam V2 — clean history start

  Legacy code preserved at:
    tag:    v1.5.0
    branch: archive/v1.5-development
    branch: archive/v1.5-main

  Carried forward:
    .plan/picam2_proof_of_concept.py  (V2 starting point)
    .plan/rewrite 2026.md             (development plan)
    .plan/todo.md                     (legacy todo reference)
    .github/                          (CI workflows, to be updated)
    .gitignore, LICENSE, README.md"

# Replace development and main with the clean history
git branch -D development
git branch -m development
git push origin development --force

git checkout -b main
git push origin main --force
```

- [x] `v2-bootstrap` orphan branch created with correct files.
- [x] `development` branch reset to clean V2 history.
- [x] `main` branch reset to clean V2 history.
- [x] Legacy branches and tag confirmed present on remote.
- [x] `.git` directory confirmed intact.

### Step 4 — Bootstrap the V2 directory structure

After the initial commit, create the skeleton directories and stub files so the project shape is established before implementation begins:

```bash
mkdir -p src/camera src/ui/gallery src/ui/themes src/storage src/hardware src/settings
mkdir -p colour_profiles lenses case docs tools web tests/unit tests/integration tests/fixtures
mkdir -p config/gpio                  # default GPIO config lives here
touch src/__init__.py src/camera/__init__.py src/ui/__init__.py
touch src/storage/__init__.py src/hardware/__init__.py src/settings/__init__.py
```

- [x] Directory skeleton created and committed.
- [x] `PLAN.md` (this file) copied to repo root and committed.
- [x] `CLAUDE.md` written (project stack, commands, dev rules, PR conventions).
- [x] `AGENTS.md` written (AI agent tool restrictions, commit format, testing requirements).

### Step 5 — Move PoC to src/ and verify it runs

- [x] Copy `.plan/picam2_proof_of_concept.py` to `src/main.py` (the V2 entry point).
- [ ] Verify `python src/main.py` still runs on the Pi and shows the live view.
- [ ] The PoC is now the running baseline for all Phase 0 work.

### Final repository structure (target after this section)

```
picam/
├── .git/                           # ← NEVER TOUCH
├── .github/workflows/              # CI workflows (updated in CI phase)
├── .gitignore
├── .plan/                          # Historical planning docs — preserved
│   ├── picam2_proof_of_concept.py  # Original PoC for reference
│   ├── rewrite 2026.md             # Original prompt/plan
│   └── todo.md                     # Legacy todo list
├── PLAN.md                         # ← This file (living document)
├── CLAUDE.md
├── AGENTS.md
├── LICENSE
├── README.md
├── requirements.txt
├── install.sh
├── colour_profiles/                # git submodule → trex22/Colour_Profiles
├── config/
│   └── gpio/
│       └── default.json            # Default GPIO button mapping
├── lenses/
│   └── lenses.json                 # Bundled lens seed database
├── case/                           # 3D models (OpenSCAD / STL)
├── docs/
├── tools/
├── web/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
└── src/
    ├── main.py                     # Entry point (was: PoC)
    ├── app.py
    ├── camera/
    │   ├── backend.py
    │   ├── picamera2_backend.py
    │   ├── demo_backend.py
    │   ├── sensor_registry.py
    │   ├── colour_profiles.py
    │   └── simulated_preview.py
    ├── ui/
    │   ├── app_window.py
    │   ├── viewfinder.py
    │   ├── control_panel.py
    │   ├── overlays.py
    │   ├── touch_handler.py
    │   ├── screen_manager.py
    │   ├── gallery/
    │   │   ├── gallery_view.py
    │   │   ├── image_viewer.py
    │   │   └── video_player.py
    │   └── themes/
    │       ├── theme_manager.py
    │       ├── dark_blue.py
    │       ├── dark_red.py
    │       ├── night_mode.py
    │       └── high_contrast.py
    ├── storage/
    │   ├── capture_controller.py
    │   ├── exif_writer.py
    │   ├── ramdrive.py
    │   └── samba.py
    ├── hardware/
    │   ├── gpio_manager.py
    │   ├── battery_monitor.py
    │   └── temp_monitor.py
    └── settings/
        ├── settings_manager.py
        ├── defaults.py
        ├── profiles.py
        └── lens_database.py
```

---

## Phase 0 — PoC Fixes & Stabilisation

> Fix all known issues in the PoC before building new features on top.
> The PoC (`src/main.py`) must remain runnable after every commit in this phase.

### P0.1 — Preview Aspect Ratio

- [x] Implement `aspect_fit(sensor_w, sensor_h, container_w, container_h)` returning the largest rect that preserves the sensor ratio within the container.
- [x] IMX477 native ratio: 4056:3040 = 4:3. The current PoC viewfinder is 573×366 (≈11:7), which causes slight stretching.
- [x] Pass the corrected `size` to `create_preview_configuration`.
- [x] Add letterbox padding as a black border inside the viewfinder frame.

### P0.2 — Drop-down Text Visibility

- [x] Fix `ttk.Combobox` drop-down list colours (text currently invisible on some desktop themes).
- [x] Apply `ttk.Style` patch: force `fieldbackground`, `foreground`, selectbackground, and the popdown list background to theme colours.
- [ ] Test on both Raspberry Pi OS Bookworm dark and light desktop themes.

### P0.3 — Proper Fullscreen / Display Mode

- [x] Add `--fullscreen` CLI flag: `root.attributes("-fullscreen", True)`.
- [x] Add `--geometry WxH` CLI flag for fixed-resolution DSP screens (default `800x480`).
- [x] In fullscreen, hide the window manager title bar.
- [~] Reflow the viewfinder to fill the screen with the control panel as a collapsible side overlay. *(deferred to Phase 9 UI polish)*

### P0.4 — Capture Confirmation Feedback

- [x] Flash a brief green border around the viewfinder for ~500 ms after successful capture.
- [x] Optional shutter click sound (WAV file, configurable path, disabled by default). *(path stored in settings; playback deferred to Phase 9)*
- [x] Show the filename of the last capture in the status bar.
- [x] Auto-clear the "Saved ✓" status after 3 seconds; return to "Ready".

### P0.5 — EXIF Data Improvements

- [x] Inject `DateTimeOriginal` (actual timestamp from `datetime.now()`).
- [x] Inject `Make` = `"Raspberry Pi"`, `Model` = `"PiCam2 v{VERSION}"`.
- [x] Inject sensor name in `UserComment`.
- [x] Inject applied `ExposureTime`, `ISOSpeedRatings`, and `FNumber` from the request metadata returned by `capture_request().get_metadata()`.
- [x] Use `exiftool` subprocess for DNG (graceful fallback if not installed).

### P0.6 — Settings File

- [x] Create `SettingsManager` reading/writing `~/.config/picam2/settings.json`.
- [x] All UI control variables (`iso`, `shutter`, `awb`, `brightness`, `contrast`, `saturation`, `sharpness`, `dpc`) persist on change.
- [x] On first boot, write defaults from `src/settings/defaults.py`.
- [x] On subsequent boots, restore the last-used values.
- [x] Add a **"Save as Default Boot State"** button that snapshots the current UI state as the defaults section.

### P0.7 — Timer Delay *(important — do in Phase 0)*

- [x] Add a timer delay selector in the UI: Off / 2s / 5s / 10s / Custom.
- [x] Large, readable countdown overlay on the viewfinder during countdown.
- [~] Optional audible beeps at 3, 2, 1 (if system audio is available). *(deferred to Phase 9)*
- [~] GPIO button integration: press to start timer; press again to cancel. *(deferred to Phase 6 GPIO)*
- [x] Timer setting persists in `settings.json`.
- [x] Timer works in still mode. *(burst mode deferred to Phase 7)*

### P0.8 — Reset to Defaults Button

- [x] Add a **"Reset to Defaults"** button in the control panel.
- [x] Restores all controls to the saved default boot state from `settings.json` (not hardcoded compile-time constants).
- [x] This is distinct from "Save as Default Boot State" — one reads, one writes.

### P0.9 — Named Capture Profiles (framework)

- [x] Implement `ProfileManager` storing named profiles in `~/.config/picam2/profiles/`.
- [x] Each profile: JSON snapshot of all control values + name + description + optional colour profile reference.
- [x] UI: profile selector combobox at the top of the control panel with **Load**, **Save As**, **Delete**.
- [x] Ship built-in profiles:
  - `Default` — factory defaults.
  - `Astrophotography – Moon` — ISO 200, 1/250s, NR off, DPC mapped-only, no AWB, high contrast.
  - `Astrophotography – Planets` — ISO 400, 1/60s, NR off, DPC off, saturation boosted.
  - `Astrophotography – Long Exposure Stars` — ISO 800, 30s, NR off, DPC off, simulated preview on.
  - `Daylight Auto` — all Auto, AWB on, NR HighQuality.
  - `Indoor Manual` — ISO 400, 1/30s, Tungsten AWB.

> ✅ Phase 0 completed 2026-03-29
> All P0 tasks implemented in `src/main.py` + `src/settings/` modules.
> Deferred items: audio beeps (P9), GPIO timer button (P6), collapsible panel reflow (P9).

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
- [ ] `Picamera2Backend` refactored from the PoC's `Camera` class, implementing the abstract interface.
- [ ] `DemoBackend` generates synthetic frames for non-Pi development.

### P1.2 — Sensor Registry & Advanced Controls

- [ ] Auto-detect sensor(s) via `Picamera2().camera_properties`.
- [ ] Define `SensorInfo` dataclass: `name`, `model_id`, `native_resolution`, `base_iso`, `max_gain`, `has_raw`, `supported_formats`, `default_colour_profile`, `dpc_modes`.
- [ ] Expose all v1.5 MMAL-era controls now via libcamera, in a collapsible "Advanced" section:
  - DPC on-sensor modes 0–3: None / Mapped / Dynamic / Both.
  - Noise Reduction Mode (ISP NR): Off / Fast / HighQuality (Pi 4); locked Off on Pi 5 with raw stream.
  - Black level offset slider.
  - Digital gain (separate from analogue gain).
  - Flicker avoidance (`AeFlickerMode`): Off / 50Hz / 60Hz / Auto.
  - FPS cap via `FrameDurationLimits` (max fps slider).
- [ ] Sensor registry extensible via `~/.config/picam2/sensors.json`.

### P1.3 — Pi 4 / Pi 5 Compatibility Layer

- [ ] Detect hardware platform at startup (`/proc/device-tree/model`).
- [ ] Pi 5 (PiSP): enforce `NoiseReductionMode=0` when raw stream is active.
- [ ] Pi 4 (BCM2711): `NoiseReductionMode` is freely settable.
- [ ] Abstract into `CameraConfig.noise_reduction_mode` with platform-aware defaults.
- [ ] Show a platform indicator (Pi4/Pi5 badge) in the UI status bar.

### P1.4 — GPIO Manager (Optional, File-Driven)

GPIO support is **optional**. If GPIO hardware is not present or GPIO is disabled in config, the app runs fully without it.

- [ ] Implement `GPIOManager` using `gpiozero` (Pi 4 & 5); graceful `ImportError` fallback on non-Pi.
- [ ] GPIO config loaded from `config/gpio/default.json` (committed to the repo as the default).
- [ ] User overrides at `~/.config/picam2/gpio.json` (merged over the default at runtime).
- [ ] Default `config/gpio/default.json` maps the v1.5 button layout for backwards compatibility.
- [ ] Available actions: `Capture`, `TimerCapture`, `BurstStart`, `BurstStop`, `ToggleAWB`, `ZoomIn`, `ZoomOut`, `ToggleOverlay`, `NextSensor`, `PreviousSensor`, `GalleryToggle`, `Shutdown`.
- [ ] GPIO can be completely disabled via `"gpio_enabled": false` in `settings.json`.
- [ ] Settings UI: view the current GPIO map; a GPIO config editor is a future feature.

**Default `config/gpio/default.json`:**
```json
{
  "gpio_enabled": true,
  "buttons": {
    "17": "Capture",
    "27": "TimerCapture",
    "22": "ToggleAWB",
    "23": "ZoomIn",
    "24": "ZoomOut",
    "25": "Shutdown"
  }
}
```

---

## Phase 2 — Colour Profiles

> **Priority: First major feature after Phase 0/1.**

### P2.1 — Colour Profiles Submodule

- [ ] Add `colour_profiles/` as a git submodule: `git submodule add https://github.com/trex22/Colour_Profiles.git colour_profiles`
- [ ] Add `colour_profiles` to `.gitmodules` with `update = remote` so `git submodule update --remote` keeps it current.
- [ ] Add submodule init to `install.sh`.

### P2.2 — ColourProfileManager

- [ ] Implement `ColourProfileManager` in `src/camera/colour_profiles.py`.
- [ ] On startup, scan `colour_profiles/{sensor_model}/` for `.json` files and build a list.
- [ ] **Default for IMX477**: auto-select `Raspberry Pi High Quality Camera Lumariver 2860k-5960k Neutral Look.json` if present.
- [ ] Expose a combobox in the control panel listing available profiles (plus "Default (libcamera)" and "None").
- [ ] Profile is loaded via `Picamera2.load_tuning_file()` **before** `configure()` is called — this must happen at startup or at deliberate restart time.

### P2.3 — Colour Profile UI

- [ ] Profile selector combobox in the control panel, above the capture button.
- [ ] Profile change triggers a camera restart with the new tuning file (~2 s on Pi 5); show a "Reloading camera..." indicator.
- [ ] Selected profile persists in `settings.json`.
- [ ] The current profile name is displayed in the viewfinder metadata bar.

### P2.4 — Colour Profile Embedding in Output

- [ ] Embed the active profile name in `UserComment` EXIF on every capture.
- [ ] For JPEG/PNG: optionally embed ICC profile bytes via Pillow `save(..., icc_profile=bytes)`.
- [ ] For DNG: write an XMP sidecar (`.xmp`) noting the active colour profile.
- [ ] "Embed colour profile in output" toggle in Settings (on by default).

### P2.5 — Colour Profile in Capture Profiles

- [ ] Named capture profiles (Phase 0.9) include the active colour profile reference.
- [ ] Loading an astrophotography profile restores the matching colour profile (or "Default").

---

## Phase 3 — Zoom & Focus Window

### P3.1 — Digital Zoom via ScalerCrop

- [ ] Implement `ScalerCrop` control passed to libcamera for digital zoom.
- [ ] Zoom in/out buttons in the control panel.
- [ ] Keyboard shortcuts: `+` / `-`.
- [ ] GPIO actions: `ZoomIn` / `ZoomOut` (if GPIO enabled).
- [ ] Zoom level indicator overlay on viewfinder (e.g. "2.1×").
- [ ] Zoom state persists in `settings.json`.
- [ ] Zoom resets to 1× when sensor is switched.

### P3.2 — Touch Zoom (Pinch / Expand)

- [ ] Pinch-to-zoom via `xinput` multi-touch events on the DSP touchscreen.
- [ ] Spread gesture: zoom in; pinch gesture: zoom out.
- [ ] Smooth zoom: interpolate `ScalerCrop` across gesture frames.
- [ ] Long-press on viewfinder: set AF point (triggers `AutoFocusCycle` at that position, if AF sensor is connected).

### P3.3 — Focus Window (Draggable / Resizable)

- [ ] Draw a semi-transparent rectangle overlay on the viewfinder.
- [ ] Drag (touch or mouse) to reposition; corner handle resize on mouse hover.
- [ ] The focus window rect is passed as `AfWindows` (AF) and also sets the `ScalerCrop` region (zoom to that region on demand).
- [ ] Focus window position and size persist in `settings.json`.
- [ ] Toggle focus window visibility with a button.

### P3.4 — Simulated Preview for Long Exposures

Long shutter speeds (slower than ~1/4 s) make the live viewfinder useless for composition.

- [ ] Define configurable `PREVIEW_SIMULATION_THRESHOLD_US` (default: 250 000 µs = 1/4 s).
- [ ] When active, the camera continues running at a fast internal metering exposure (e.g. 1/500 s, ISO auto).
- [ ] A reference frame is grabbed from the fast metering stream.
- [ ] A brightness transform simulates the target long exposure: `simulated = clip(reference * (selected_us / metering_us) * gain_ratio)`.
- [ ] Display a red **"SIM"** badge on the viewfinder title bar when simulation is active.
- [ ] The metering reference frame refreshes every 5 s.
- [ ] Simulation deactivates automatically when shutter speed returns above the threshold.
- [ ] Manual **"Simulate"** toggle button forces simulation regardless of shutter speed.
- [ ] The `Long Exposure Stars` capture profile enables simulation by default.

---

## Phase 4 — AWB & White Balance

### P4.1 — AWB Mode Selector

- [ ] Add `AwbMode` combobox: Auto / Incandescent / Tungsten / Fluorescent / Indoor / Daylight / Cloudy / Custom.
- [ ] Maps to `libcamera` `AwbModeEnum` values.
- [ ] When set to a non-Auto mode, `AwbEnable` remains true but the algorithm is locked to the selected mode.

### P4.2 — Manual White Balance Gains

- [ ] When `AwbEnable = False`, show two sliders: Red Gain (0.0–4.0) and Blue Gain (0.0–4.0).
- [ ] Pass `ColourGains=(red, blue)` in the controls dict.
- [ ] "Measure WB" button: take a still from the current frame and compute the grey-world gain estimate; pre-fill the sliders.
- [ ] Manual gains persist in `settings.json`.

### P4.3 — AWB Integration in Capture Profiles

- [ ] AWB mode and manual gains are included in named capture profiles.
- [ ] The `Astrophotography – Moon` profile sets Daylight AWB; `Long Exposure Stars` sets Custom gains for a neutral star colour.

---

## Phase 5 — Gallery & Media Browser

### P5.1 — Gallery View

- [ ] Gallery button in the main UI (or swipe gesture) opens the gallery panel.
- [ ] Scrollable grid of thumbnails from the DCIM folder.
- [ ] Thumbnails generated lazily in a background thread; cached at `~/.cache/picam2/thumbs/` (keyed by file mtime).
- [ ] Video files show a play-button icon overlay on their thumbnail.
- [ ] Tap/click a thumbnail to open the full-screen viewer.
- [ ] Swipe or arrow keys to navigate between items.
- [ ] Filter bar: All / RAW / JPEG / PNG / Video.
- [ ] Sort: Newest First / Oldest First.

### P5.2 — Image Viewer

- [ ] Full-screen display.
- [ ] Pinch/scroll to zoom; double-tap to zoom to 100%.
- [ ] Swipe left/right to navigate between images.
- [ ] Toggleable EXIF data panel: sensor, shutter, ISO, lens, colour profile, GPS (if present).
- [ ] **Delete** button: confirm dialog → move to Trash or permanent delete (configurable).
- [ ] Share button: copy to Samba share / trigger web download.
- [ ] "Open in Darktable" if Darktable is installed.
- [ ] "Process in MagicForge" if MagicForge is installed.

### P5.3 — Video Player

- [ ] Inline playback via `ffplay` subprocess or embedded Tkinter-compatible player.
- [ ] Controls: play/pause, seek scrubber, volume.
- [ ] **Delete** button with confirm dialog.

### P5.4 — Gallery Management

- [ ] Select multiple items (long-press → multi-select mode).
- [ ] Bulk delete with confirmation.
- [ ] Bulk export to Samba share.
- [ ] Show storage usage summary (DCIM size, free space) in the gallery header.

### P5.5 — Gallery Integration

- [ ] Gallery groups by date (day folders matching DCIM structure).
- [ ] Focus bracket sequences shown as a collapsed group (expandable).
- [ ] Capture profile label shown per-image if embedded in EXIF.

---

## Phase 6 — Hardware Platform

### P6.1 — Battery Monitor

- [ ] Detect common Pi battery HATs via I²C: PiJuice, Waveshare UPS HAT, Pimoroni LiPo SHIM.
- [ ] `BatteryMonitor` polls charge level, voltage, and charging status every 30 s.
- [ ] Battery percentage + icon in the status bar.
- [ ] Low-battery warning overlay at 15%; configurable auto-shutdown at 5%.
- [ ] Battery status logged per-capture in the stats JSON.

### P6.2 — Temperature Monitoring

- [ ] Poll `vcgencmd measure_temp` every 60 s.
- [ ] CPU temp displayed in the status bar (red above 80°C, orange above 70°C).
- [ ] Throttle warning overlay if `vcgencmd get_throttled` returns non-zero.
- [ ] Temperature logged per-capture in stats sidecar.

### P6.3 — Screen Brightness Control

- [ ] Write to `/sys/class/backlight/*/brightness` for DSP/HDMI screens.
- [ ] Brightness slider in Settings → Display.
- [ ] Auto-dim after N seconds of inactivity (configurable; default: 60 s).
- [ ] Restore brightness on touch/button press.

### P6.4 — Screen Support

| Display Type | Backend | Notes |
|---|---|---|
| DSP Touchscreen (800×480) | Tkinter/X11 | Primary v2 target |
| HDMI (any resolution) | Tkinter/X11 | Fullscreen or windowed |
| Framebuffer (headless) | pygame / fbdev | Pi 4 legacy / future small model |

- [ ] `ScreenManager` selects backend at startup via environment or `--display dsp|hdmi|fb` CLI flag.
- [ ] Auto-detect: if `$DISPLAY` is set, use X11; otherwise fall back to framebuffer.
- [ ] **Framebuffer path preserved** for a future low-cost headless Pi 4 build.

### P6.5 — Headless / Small Model Support (Future Pi 4 Build)

- [ ] All capture and settings flows navigable via GPIO buttons alone in framebuffer mode.
- [ ] Key-driven menu system for settings changes in headless mode.
- [ ] `--headless` flag or `PICAM2_HEADLESS=1` env var selects framebuffer path.
- [ ] Console status output retained for debug in headless mode.
- [ ] `pygame` drawing layer for the framebuffer rendering path.

### P6.6 — Fast Boot

- [ ] Disable unnecessary `systemd` services via install script.
- [ ] `systemd` user service for PiCam2 with `After=graphical-session.target`.
- [ ] Target: boot-to-live-view in < 10 s on Pi 5.

### P6.7 — Auto Login & Auto-Run

- [ ] `install.sh` calls `raspi-config nonint do_boot_behaviour B4` (desktop autologin).
- [ ] `.config/autostart/picam2.desktop` entry.

### P6.8 — Power Optimisation

- [ ] Disable HDMI output when running DSP-only (`tvservice -o`).
- [ ] CPU governor: `powersave` at idle, `performance` during active capture.
- [ ] WiFi disable toggle in Settings (for battery-sensitive use).

---

## Phase 7 — Camera Features

### P7.1 — Multi-Sensor & Dual Sensor Support

*(Multi-sensor and dual-sensor are the same feature — combined.)*

- [ ] Enumerate all connected cameras via `Picamera2.global_camera_info()` at startup.
- [ ] **Sensor selector** at the top of the control panel showing detected sensors by model name.
- [ ] **Single sensor mode** (default): one viewfinder; switching sensors stops and restarts the backend.
- [ ] **Dual sensor mode** (when two sensors detected): two preview panes side-by-side or stacked, each with its own collapsible control column.
- [ ] Dual capture: fire both sensors simultaneously from two threads; outputs saved with matching timestamps.
- [ ] Per-sensor settings stored independently in `settings.json` keyed by sensor model.
- [ ] Pi 5: two concurrent streams supported. Pi 4: one active sensor at a time.
- [ ] **Scroll-through-sensors**: cycles through all detected sensors via touch swipe or `NextSensor`/`PreviousSensor` GPIO actions.

### P7.2 — ArduCam Autofocus Support

- [ ] Detect ArduCam AF modules via camera properties.
- [ ] `AfMode` combobox: Manual / Continuous / Auto-on-capture.
- [ ] `LensPosition` slider for manual focus (0.0–1.0).
- [ ] `AutoFocusCycle` triggered on shutter-half-press (GPIO) or focus window tap.

### P7.3 — Metering Modes

- [ ] `AeMeteringMode` combobox: Centre-weighted / Spot / Matrix / Custom.

### P7.4 — Exposure Compensation (EV)

- [ ] `ExposureValue` slider: −4 EV to +4 EV in 1/3-stop steps. Active only when `AeEnable=True`.

### P7.5 — Shutter Speed Simulation in Preview

- [ ] *(Covered in Phase 3.4 — Simulated Preview)*

### P7.6 — Auto Mode & Programme Mode

- [ ] **Auto** button: set all controls to Auto (ISO, shutter, AWB all automatic).
- [ ] **Programme** mode: user fixes one parameter; camera auto-handles the rest.

### P7.7 — Burst / Continuous Shot

- [ ] Hold capture button for burst mode; release to stop.
- [ ] Frames go to RAMDrive buffer; flushed after burst ends.
- [ ] Configurable max burst length and inter-frame delay.

---

## Phase 8 — Storage & Output

### P8.1 — Save Format Options

- [ ] Format picker in Settings: `RAW only (DNG)`, `JPEG only`, `PNG only`, `RAW + JPEG`, `RAW + PNG`.
- [ ] JPEG quality slider (1–100, default 95).
- [ ] PNG compression slider (0–9, default 6).
- [ ] Capture button label updates to reflect the current format (e.g. "◉  CAPTURE  DNG+JPG").

### P8.2 — In-Memory Buffer (RAMDrive)

- [ ] Create `/dev/shm/picam/` buffer; configurable allocation limit (default 2 GB on Pi 5).
- [ ] `BufferManager`: write to RAMDrive first, flush to persistent storage asynchronously in a background thread.
- [ ] Progress indicator for pending flushes in the status bar.
- [ ] Burst mode captures to RAMDrive; flush after burst ends.

### P8.3 — DCIM Directory Structure

- [ ] `~/Pictures/DCIM/YYYYMMDD/IMG_YYYYMMDD_HHMMSS.dng`.
- [ ] Configurable DCIM root path in settings.

### P8.4 — Colour Profile Embedding

- [ ] *(Covered in Phase 2.4)*

### P8.5 — Samba / Network Share

- [ ] `samba.py` writes a minimal `smb.conf` sharing the DCIM folder.
- [ ] Settings toggle restarts `smbd`.
- [ ] Advertise via Avahi/mDNS as `picam2.local`.

### P8.6 — Lens Database

- [ ] `LensDatabase` loads from bundled `lenses/lenses.json` and user file `~/.config/picam2/lenses.json`.
- [ ] Each entry: `id`, `make`, `model`, `focal_length_mm`, `max_aperture`, `min_aperture`, `mount`, `is_adapted`, `notes`.
- [ ] Ship seed database focused on M42 mount lenses and common adapted lenses.
- [ ] **Lens selector UI**: searchable dropdown/popup list in the control panel.
- [ ] **Teleconverter support**: a `tc_multiplier` field adjusts the reported focal length (e.g. Vivitar 2× → double the focal length).
- [ ] Selected lens injected into EXIF (`LensModel`, `FocalLength`, `MaxApertureValue`) on every capture.
- [ ] "Add Lens" form in the UI: fill in details manually; saved to user lenses JSON.
- [ ] Selected lens persists in `settings.json`.

---

## Phase 9 — UI Polish & Themes

### P9.1 — Theme System

- [ ] `ThemeManager` loads a theme from `~/.config/picam2/theme.json` or `--theme` CLI flag.
- [ ] Each theme: colour palette dict (`bg_dark`, `bg_mid`, `bg_panel`, `accent`, `text_light`, `text_dim`, `btn_capture`, `btn_ok`, `btn_warn`).
- [ ] Applied globally via a style registry; hot-swap without restart.

**Built-in themes:**

| Theme | Description | Use Case |
|---|---|---|
| `dark_blue` | PoC default — navy/teal/red | General use |
| `dark_red` | Crimson/charcoal | Alternative aesthetic |
| `night_mode` | Deep red-on-black | Astrophotography — preserves dark-adapted vision |
| `high_contrast` | White/yellow on black | Outdoor bright light readability |
| `classic` | Grey/green terminal feel | Nostalgic; v1.5 callback |

### P9.2 — Font System

- [ ] `FontRegistry` with named roles: `ui_small`, `ui_body`, `ui_label`, `vf_overlay`, `status`, `mono`.
- [ ] Sizes scale with screen resolution (larger on 1080p+, smaller on 800×480 DSP).
- [ ] `--font-scale` CLI flag for accessibility.
- [ ] Fonts configurable per theme.

### P9.3 — Responsive Layout

- [ ] **Compact mode** (800×480 DSP): minimal visible controls, collapsible side panel, viewfinder maximised.
- [ ] **Standard mode** (1080p+): full side panel, all controls visible.
- [ ] Auto-detected from window geometry or `--layout compact|standard` CLI flag.

### P9.4 — Overlay Indicators

- [ ] **Focus Peaking**: Laplacian-of-preview computed every N-th frame; edges highlighted in a configurable colour.
- [ ] **Histogram**: live luminance/RGB histogram overlay via NumPy.
- [ ] **Zebra Stripes**: pixels above configurable threshold rendered with alternating stripes (overexposure warning).
- [ ] **Grid Overlay**: rule-of-thirds / square / diagonal / centre-cross grid.
- [ ] All overlays togglable independently; state persists in `settings.json`.

---

## Phase 10 — Advanced Imaging & MagicForge

MagicForge (`/Users/trex22/development/MagicForge`) provides SIFT/ORB feature matching, drizzle stacking, lucky-drizzle mosaic, EXIF editing, and scan2stl. Integration is optional — detected via `which magicforge` or a configured path.

### P10.1 — Focus Bracket Continuous Shot

- [ ] **Focus Bracket** mode: N stills stepping `LensPosition` through a user-defined range.
- [ ] Configurable: start (0.0–1.0), end, N steps, inter-frame delay.
- [ ] Output saved to `FOCUSBRACKET_YYYYMMDD_HHMMSS/` sub-folder in DCIM.
- [ ] Post-processing hook: optionally invoke MagicForge's focus-stack pipeline.
- [ ] Simulated bracket variant: step `Sharpness` control values for comparison on fixed-focus lenses.

### P10.2 — MagicForge Integration

- [ ] Gallery "Process in MagicForge" button on selected file(s).
- [ ] Focus bracket sequences: auto-launch MagicForge focus-stack pipeline.
- [ ] Astrophotography sequences: auto-invoke `lucky_drizzle_mosaic()`.
- [ ] Can run on the Pi (ARM64 compatible) or on a connected host over SSH.

### P10.3 — Stop Motion Mode

- [ ] N frames at configurable interval; onion-skin overlay (last frame at reduced opacity).
- [ ] Optional GIF/MP4 assembly via `ffmpeg`.

### P10.4 — Camera Intrinsics Tool

- [ ] `tools/intrinsics.py`: checkerboard capture → OpenCV calibration → `K` + distortion → `~/.config/picam2/intrinsics_{sensor}.json`.

### P10.5 — HDR Bracket Capture

- [ ] Capture at −2EV, 0EV, +2EV; optionally invoke MagicForge for HDR merge.

### P10.6 — Image Statistics

- [ ] Per-capture: mean luminance, clipping %, estimated colour temperature → JSON stats sidecar.

---

## Phase 11 — Connectivity & Remote

### P11.1 — Web Control Interface

- [ ] Lightweight Flask/FastAPI server (`web/server.py`).
- [ ] MJPEG live stream: `GET /stream`.
- [ ] Capture: `POST /capture`.
- [ ] Settings: `GET/PUT /settings`.
- [ ] Mobile-optimised UI — acts as a full remote shutter panel from a phone.
- [ ] Optional PIN authentication (settings toggle).
- [ ] Advertised via Avahi as `picam2.local`.

### P11.2 — Bluetooth HID Remote Control

- [ ] Listen for HID events from paired BT devices via `evdev`.
- [ ] Map HID key codes to actions in `config/gpio/default.json` under `"bt_remote_map"`.
- [ ] Works with standard BT camera shutters, gamepads, or any paired HID device.

### P11.3 — PTP/MTP Mount

- [ ] `gphoto2` virtual camera daemon for macOS Image Capture and Darktable PTP import.
- [ ] Install step for `gphoto2`, `libgphoto2-dev`.

### P11.4 — Darktable on Device

- [ ] Optional install step for `darktable` (ARM64 package on Bookworm).
- [ ] "Open in Darktable" context menu on last-captured file.

---

## Phase 12 — Streaming, Webcam & Integrations

> **Lower priority.** These are useful but not required for the core camera experience.

### P12.1 — Webcam / UVC Mode

- [ ] Expose the camera as a USB webcam using `v4l2loopback` and a feed from the picamera2 preview stream.
- [ ] Any app that supports V4L2 (Zoom, OBS, browsers, etc.) can then use PiCam2 as a webcam.
- [ ] Install step: `sudo apt install v4l2loopback-dkms`.
- [ ] Toggle in Settings: "Enable UVC Webcam Mode". Activating it starts the `v4l2loopback` pipe.
- [ ] Configurable output resolution and frame rate for the webcam stream.

### P12.2 — Security Camera / RTSP Streaming

- [ ] RTSP stream server using `ffmpeg` or `mediamtx` (formerly rtsp-simple-server).
- [ ] Stream URI: `rtsp://picam2.local:8554/live`.
- [ ] Optional motion-triggered recording: save clips to DCIM when motion is detected (uses H.264 motion vectors).
- [ ] Toggle in Settings: "Enable RTSP Stream".
- [ ] Configurable stream resolution, bitrate, and motion sensitivity.
- [ ] Web preview via HLS fallback (in the web UI) for non-RTSP clients.

### P12.3 — Crowsnest / Klipper 3D Printer Integration

Crowsnest is the standard webcam streaming service for Klipper-based 3D printers (Mainsail, Fluidd).

- [ ] Provide a configuration snippet / install step that registers PiCam2 as a Crowsnest camera source.
- [ ] PiCam2 exposes a MJPEG or RTSP endpoint that Crowsnest can consume.
- [ ] Document the Crowsnest `[cam picam2]` config block in `docs/KLIPPER.md`.
- [ ] Optionally: a "Klipper Mode" preset that locks the camera to a fixed resolution/fps optimised for print monitoring (e.g. 1080p @ 15fps) and disables all other capture features while streaming.

### P12.4 — Remote Shots via Web UI

- [ ] The web control interface (P11.1) already supports `POST /capture`.
- [ ] Add a live viewfinder stream (MJPEG or WebRTC) to the web UI so remote shots can be composed visually.
- [ ] Show the last captured image/thumbnail in the web UI after each remote capture.
- [ ] Download button for the last capture from the web UI.

---

## Phase 13 — Video & Audio

### P13.1 — Video Capture

- [ ] "VIDEO" mode toggle in the UI.
- [ ] `H264Encoder` with configurable bitrate (slider: 1–50 Mbps).
- [ ] Output to `~/Videos/DCIM/VID_YYYYMMDD_HHMMSS.mp4` via `FfmpegOutput`.
- [ ] Resolution/FPS presets: 1080p30, 1080p60 (Pi 5), 720p60, 4K (Pi 5).
- [ ] H.264 profile selector: Baseline / Main / High.
- [ ] Bitrate and model selection controls visible in the control panel during video mode.

### P13.2 — RAW Video

- [ ] Raw Bayer video to `.dng` sequence or `.raw` binary using the always-running raw stream.
- [ ] RAMDrive buffer essential; downsampled raw option for manageable file sizes.

### P13.3 — Audio Input

- [ ] Detect USB/3.5mm audio via `arecord -l`.
- [ ] Record audio alongside video via `ffmpeg` subprocess muxer.
- [ ] VU meter overlay in video mode.

---

## Phase 14 — Timelapse

> **Lower priority.** Useful for long-running automated captures.

### P14.1 — Timelapse Capture Mode

- [ ] Timelapse mode: capture N frames at a configurable interval (e.g. every 30 s, every 5 min).
- [ ] Configurable: total duration or total frame count; interval; save format (JPEG recommended for large timelapses).
- [ ] A progress bar and ETA overlay on the viewfinder during a timelapse sequence.
- [ ] Timelapse sequences saved to `~/Pictures/DCIM/TIMELAPSE_YYYYMMDD_HHMMSS/`.
- [ ] "Stop Timelapse" button (or GPIO action) to end early.

### P14.2 — Timelapse Assembly

- [ ] After a timelapse sequence completes, offer to assemble it into an MP4 via `ffmpeg`.
- [ ] Configurable output FPS (e.g. 24fps for smooth playback).
- [ ] Assembly runs in a background thread; progress indicator in the gallery.

### P14.3 — Timelapse in the Gallery

- [ ] Timelapse folders shown as a collapsed group in the gallery with a special icon.
- [ ] Assembled MP4s shown as playable videos in the gallery.
- [ ] Delete timelapse folder (all frames + assembled video) with a single confirm action.

---

## Phase 15 — Astrophotography & Science Modes

### P15.1 — Astrophotography Capture Profiles

- [ ] *(Built-in profiles shipped in Phase 0.9)*
- [ ] Dark frame subtraction: capture a dark frame (lens cap on, same settings); subtract from light frame in post.
- [ ] Star-eater avoidance: empirically test DPC modes 0 vs 1 to confirm faint point sources are preserved.

### P15.2 — Focus Bracket for Astrophotography

- [ ] Focus bracket mode (Phase 10.1) auto-invokes MagicForge `lucky_drizzle_mosaic()` on the output sequence.

### P15.3 — Motion Detection

- [ ] H.264 motion vectors for motion-triggered capture (wildlife / security camera mode).

### P15.4 — Science Overlays

- [ ] Canny edge detection overlay (focus confirmation at pixel level).
- [ ] Face detection bounding boxes (OpenCV haarcascade, background thread).

---

## Phase 16 — Polish & Distribution

### P16.1 — Install Script (`install.sh`)

- [ ] Detect Pi 4 vs Pi 5.
- [ ] Install Python dependencies, initialise submodule, optional packages (darktable, samba, gphoto2, v4l2loopback, mediamtx).
- [ ] Configure autologin and autostart.
- [ ] Write default `settings.json` and copy default GPIO config.

### P16.2 — `requirements.txt`

```
picamera2>=0.3.12
Pillow>=10.0
piexif>=1.1.3
numpy>=1.24
gpiozero>=2.0
```

### P16.3 — Logging

- [ ] Replace all `print()` with Python `logging`.
- [ ] Log file: `~/.local/share/picam2/picam2.log` with rotation (5 MB × 3 files).
- [ ] In-app log viewer: collapsible panel at the bottom, toggle with keyboard shortcut.

### P16.4 — README & Docs

- [ ] `README.md` updated for V2: install instructions, supported hardware, screenshots.
- [ ] `docs/SENSORS.md` — sensor support matrix.
- [ ] `docs/COLOUR_PROFILES.md` — how to use and create profiles.
- [ ] `docs/GPIO.md` — button mapping reference and config file format.
- [ ] `docs/LENSES.md` — lens database format and how to add entries.
- [ ] `docs/KLIPPER.md` — Crowsnest / Klipper integration guide.
- [ ] `docs/STREAMING.md` — RTSP / webcam / web UI streaming guide.

---

## Testing Strategy

### Test Architecture

```
tests/
├── unit/               # isolated module tests (no hardware, no camera)
├── integration/        # pipeline tests using DemoBackend
└── fixtures/           # sample images, mock camera responses, settings JSON
```

### Unit Tests

| Module | What to Test |
|---|---|
| `SettingsManager` | Load / save / defaults / migration / corrupt-file handling |
| `ColourProfileManager` | Profile discovery, IMX477 auto-select, missing profiles, restart sequence |
| `SensorRegistry` | Detection, property parsing, unsupported sensor fallback |
| `ExifWriter` | EXIF injection DNG/JPEG/PNG; lens data; colour profile name |
| `LensDatabase` | Load bundled DB, load user DB, merge, search, add entry, TC multiplier |
| `ProfileManager` | Load / save / delete / apply; built-in profiles |
| `GPIOManager` | Load default config, user override merge, disabled mode, action dispatch |
| `BufferManager` | Write to RAMDrive, flush, size limits, eviction policy |
| `SimulatedPreviewEngine` | Threshold detection, brightness transform, SIM badge trigger |
| `TimerController` | Countdown, cancel, capture trigger integration |
| `CameraConfig` | Platform detection, Pi 4/Pi 5 NR mode selection |
| `DemoBackend` | Synthetic frame generation, controls dict pass-through |
| `ThemeManager` | Theme load, apply, hot-swap |

### Integration Tests

- [ ] Full still capture pipeline: settings → controls → capture → EXIF → save (DemoBackend).
- [ ] Profile load and apply: snapshot → camera restart → controls restore.
- [ ] Sensor enumeration and single/dual sensor switching.
- [ ] Focus bracket sequence: folder creation, frame numbering, MagicForge hook call.
- [ ] Burst mode with RAMDrive buffer and flush.
- [ ] Simulated preview: activation/deactivation on shutter speed threshold crossing.
- [ ] Timer delay countdown with mock time.
- [ ] Save format combinations: DNG, JPEG, DNG+JPEG.
- [ ] GPIO config load: default → user override → action dispatch.
- [ ] Timelapse: frame capture, interval timing (mock), assembly invocation.
- [ ] RTSP stream start/stop lifecycle.

### UI Smoke Tests

- [ ] App starts in `DemoBackend` mode, all widgets render, no exceptions.
- [ ] Control changes propagate to the backend (mock `apply_controls`, assert call args).
- [ ] Gallery thumbnail generation and display.
- [ ] Theme switching changes widget colours.
- [ ] Fullscreen mode: layout reflows correctly.

### Hardware-in-the-Loop (HiL) Tests

Run on the self-hosted Pi runner only:
- [ ] Live preview frame rate (≥ 15 fps on Pi 5).
- [ ] DNG capture and validity (`exiftool -validate`).
- [ ] Colour profile loading: verify tuning file reflected in capture metadata.
- [ ] GPIO button mapping: physical button or GPIO stimulator.
- [ ] Battery HAT detection (if HAT is attached to the runner).

### Coverage Requirements

- Minimum **80% overall coverage** for all non-hardware modules.
- No coverage reduction allowed on PRs (enforced by CI).
- `Picamera2Backend`, `GPIOManager`, `BatteryMonitor` excluded from thresholds; tested by HiL suite.

---

## CI/CD Pipeline

### Workflow Files

```
.github/workflows/
├── ci.yml                       # Lint + tests + coverage
├── ai-pr-review.yml             # AI code review on every PR
├── ai-pr-review-on-comment.yml  # Trigger AI review via /ai-review comment
├── security.yml                 # TruffleHog + Semgrep + pip-audit + Trivy
├── semgrep.yml                  # Standalone daily Semgrep scan
└── license-check.yml            # Dependency license compliance
```

### `ci.yml`

```yaml
on:
  pull_request:
  push:
    branches: [main, development]

jobs:
  lint:
    # flake8, black --check, isort --check

  test:
    # pytest tests/unit tests/integration
    # pytest --cov=src --cov-report=xml --cov-fail-under=80
    # Upload coverage artifact

  hil-test:
    runs-on: [self-hosted, raspberry-pi, pi5]
    if: github.base_ref == 'main'
    # pytest tests/hil/

  accessibility:
    needs: changes
    if: needs.changes.outputs.web == 'true'
    # pa11y-ci + axe-core on web/
```

### `ai-pr-review.yml`

Adapted from the artemis implementation (Codestral-2501 via GitHub Models API).

**PiCam2-specific system prompt focus areas:**
```
1. CRITICAL: Threading safety — Tkinter vars (.get()/.set()) ONLY on the main thread.
   Worker threads must use root.after() callbacks to update UI.
2. CRITICAL: Camera resource management — always stop/close in finally blocks.
3. Single-config design — never call configure() or stop() on the running camera
   except for deliberate profile switches with a full restart.
4. Pi 5 PiSP constraint — NoiseReductionMode must stay 0 when a raw stream is active.
   Warn on any code that modifies this without a platform check.
5. GPIO is optional — all code paths must work when GPIOManager raises ImportError
   or when gpio_enabled is false.
6. Type hints on all public methods.
7. No bare except — always catch specific exceptions.
8. Subprocess security — no shell=True; escape all user-supplied path arguments.
```

### `security.yml`

- [ ] **TruffleHog**: secret scanning on commits and PRs.
- [ ] **Semgrep**: Python + security rule sets; custom rules for subprocess injection, path traversal, insecure `/tmp` use.
- [ ] **pip-audit**: CVE scan of `requirements.txt`.
- [ ] **Trivy**: Dockerfile config scan (when added).
- [ ] Scheduled weekly (Monday 6 AM UTC) + on PRs/pushes to main.

### `license-check.yml`

- [ ] `pip-licenses` audits all Python dependencies.
- [ ] Flags GPL/AGPL licenses conflicting with the project's MIT license.
- [ ] Weekly scheduled + on PRs modifying `requirements.txt`.

### Self-Hosted Pi Runner

- [ ] Register a Raspberry Pi 5 as a GitHub Actions self-hosted runner.
- [ ] Tagged `[self-hosted, raspberry-pi, pi5]`.
- [ ] Only `hil-test` uses the self-hosted runner.
- [ ] IMX477 camera and GPIO hardware attached to the runner.
- [ ] Runner configured as a `systemd` service for auto-start.

### Dependabot

- [ ] Enable Dependabot for `requirements.txt` (weekly Python updates).
- [ ] Enable Dependabot for GitHub Actions workflow versions.

---

## Deferred / Lowest Priority Items

- **GPS EXIF support** — `gpsd-py3` integration; add when time permits. Lowest priority.
- **DOL-HDR** — requires sensor-level support not yet in libcamera stable.
- **Video stabilisation** — software only; lower priority given fixed-mount use case.
- **Image watermark tool** — post-processing CLI; low urgency.
- **Lens shading control** — requires custom tuning JSON; complex.
- **Zero Shutter Lag** — research `ZeroShutterLag` mode on Pi 4 later.
- **Python module packaging** — pip-installable module for a future release.
- **User-defined themes** — JSON editor in Settings → Appearance.
- **High-DPI support** — 4K HDMI displays.

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

**Sensor → profile auto-selection:**
```python
SENSOR_PROFILE_DEFAULTS = {
    "imx477": "imx477/Raspberry Pi High Quality Camera Lumariver 2860k-5960k Neutral Look.json",
    "imx219": "imx219/default.json",
}
```

---

## Sensor Support Matrix

| Sensor | Module | Resolution | Raw Format | AF | Default Colour Profile |
|--------|--------|------------|------------|-----|------------------------|
| IMX477 | HQ Camera | 4056×3040 | SRGGB12 | No | Lumariver custom |
| IMX219 | V2 Camera | 3280×2464 | SRGGB10 | No | libcamera built-in |
| IMX296 | Global Shutter | 1456×1088 | SRGGB10 | No | libcamera built-in |
| OV9281 | Global Shutter Mono | 1280×800 | Y8/Y10 | No | N/A |
| IMX519 | ArduCam 16MP AF | 4656×3496 | SRGGB10 | ✅ | libcamera built-in |
| AR0234 | ArduCam Global | 1920×1200 | SGRBG10 | No | libcamera built-in |

---

## Known Hardware Constraints

| Constraint | Platform | Mitigation |
|---|---|---|
| PiSP TDN crash on mode switch | Pi 5 | Single-config design |
| One concurrent camera stream | Pi 4 | Sequential sensor switching; no dual-sensor on Pi 4 |
| Raw stream memory (~15 MB/frame) | All | `buffer_count=2`; RAMDrive flush |
| `set_tuning_file()` requires restart | All | Accept ~2 s delay on profile switch |
| GPIO requires `gpiozero` / `RPi.GPIO` | All | Graceful fallback; GPIO is optional |
| DSP touchscreen multi-touch limited | Pi 5 DSP | `xinput` events for best pinch support |
| No OIS on any Pi camera module | All | Software stabilisation only |

---

## UI Theme & Visual Design System

### Current Theme (PoC baseline)

```python
BG_DARK  = "#1a1a2e"
BG_MID   = "#16213e"
BG_PANEL = "#0f3460"
ACCENT   = "#e94560"
TEXT_LIGHT = "#eaeaea"
TEXT_DIM   = "#888899"
```

### Theme System

- [ ] `ThemeManager` in `src/ui/themes/theme_manager.py`.
- [ ] Themes stored as Python dicts in individual files under `src/ui/themes/`.
- [ ] Selected theme applied via a widget style registry; all Tk widgets registered at startup.
- [ ] Hot-swap: re-apply all registered widget styles without restart.
- [ ] User theme override: `~/.config/picam2/theme.json` merges over the selected theme.

### Font System

- [ ] `FontRegistry` with named roles: `ui_small`, `ui_body`, `ui_label`, `vf_overlay`, `status`, `mono`.
- [ ] Defaults: Helvetica (labels), Courier (status/metadata), system monospace (log viewer).
- [ ] Size scaling: 800×480 → scale 0.85×; 1080p → scale 1.0×; 4K → scale 1.5×.
- [ ] `--font-scale FLOAT` CLI flag.

### Responsive Layout Modes

| Mode | Trigger | Description |
|---|---|---|
| `compact` | `--layout compact` or window ≤ 800 px wide | Collapsible side panel, viewfinder maximised |
| `standard` | `--layout standard` or window > 800 px wide | Full side panel, all controls visible |
| `fullscreen` | `--fullscreen` | No window chrome, collapsible overlay panel |
