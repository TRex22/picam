#!/usr/bin/env python3
"""
picam2.py — Raspberry Pi HQ Camera GUI
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Modern libcamera / picamera2 based desktop app using Tkinter.
Replaces the legacy PiCamera stack used in the original picam project.

Tested with:
  • Raspberry Pi 5
  • Raspberry Pi HQ Camera (IMX477, 12.3 MP, 4056×3040)
  • Raspberry Pi OS Bookworm (64-bit)
  • picamera2 >= 0.3.12

Install dependencies:
  sudo apt install python3-picamera2 python3-pil python3-pil.imagetk

Output:  ~/Pictures/DCIM/  (DNG format, full-sensor resolution)

Controls:
  ISO          → maps to AnalogueGain  (ISO ≈ gain × 100, sensor-limited)
  Shutter      → ExposureTime in µs    (disables AE when set)
  DPC Mode     → Dead Pixel Correction via NoiseReductionMode
                 (Off / Fast / HighQuality)
  AWB          → Auto White Balance on/off
  Brightness   → ISP brightness offset (-1.0 … +1.0)
  Contrast     → ISP contrast multiplier (0.0 … 32.0)
  Saturation   → ISP colour saturation  (0.0 …  32.0)
  Sharpness    → ISP sharpness level    (0.0 …  16.0)
"""

import os
import sys
import time
import threading
import traceback
from datetime import datetime
from pathlib import Path

import tkinter as tk
from tkinter import ttk, messagebox

from PIL import Image, ImageTk

# ──────────────────────────────────────────────────────────────────────────────
# picamera2 import — graceful fallback so the file can be opened on non-Pi hosts
# ──────────────────────────────────────────────────────────────────────────────
try:
    from picamera2 import Picamera2, Preview
    PICAMERA2_AVAILABLE = True
except ImportError:
    PICAMERA2_AVAILABLE = False
    print("[WARN] picamera2 not found — UI opens in DEMO mode (no camera)")

# ═══════════════════════════════════════════════════════════════════════════════
# Constants / Defaults  (mirroring the original picam defaults)
# ═══════════════════════════════════════════════════════════════════════════════

APP_TITLE       = "PiCam2 — HQ Camera"
WINDOW_W        = 800          # total window width  (px)
WINDOW_H        = 480          # total window height (px)
# Viewfinder occupies the left portion; right panel is PANEL_W wide.
# Outer frame padding (each side): OUTER_PAD px.
OUTER_PAD       = 5
PANEL_W         = 205          # width of the right-hand control panel
VF_GAP          = 8            # gap between viewfinder and panel
# Viewfinder chrome: title-bar ≈22, metadata-bar ≈18, capture-btn ≈34, border ≈4 → ~78
VF_CHROME_H     = 78
VF_CHROME_W     = 4            # left/right border pixels on the vf frame
STATUS_H        = 26           # height of the bottom status bar incl. padding
VIEWFINDER_W    = WINDOW_W - (OUTER_PAD * 2) - PANEL_W - VF_GAP - VF_CHROME_W  # ≈ 557
VIEWFINDER_H    = WINDOW_H - (OUTER_PAD * 2) - VF_CHROME_H - STATUS_H           # ≈ 366
PREVIEW_FPS     = 24           # target frames per second in live view
PREVIEW_DELAY   = int(1000 / PREVIEW_FPS)   # ms between tkinter.after() calls

# IMX477 HQ Camera native sensor resolution
SENSOR_W        = 4056
SENSOR_H        = 3040

# Where photos are saved — resolve to the real user's home even when
# launched via sudo (SUDO_USER env var holds the original username).
def _resolve_dcim_dir() -> Path:
    sudo_user = os.environ.get("SUDO_USER")
    if sudo_user:
        import pwd
        home = Path(pwd.getpwnam(sudo_user).pw_dir)
    else:
        home = Path.home()
    return home / "Pictures" / "DCIM"

DCIM_DIR = _resolve_dcim_dir()

# Colour scheme
BG_DARK         = "#1a1a2e"
BG_MID          = "#16213e"
BG_PANEL        = "#0f3460"
ACCENT          = "#e94560"
TEXT_LIGHT      = "#eaeaea"
TEXT_DIM        = "#888899"
BTN_CAPTURE     = "#c0392b"
BTN_CAPTURE_HOV = "#e74c3c"
BTN_OK          = "#27ae60"

# ── ISO → AnalogueGain ────────────────────────────────────────────────────────
# The IMX477 has a native base ISO of ≈100 (gain=1.0).
# picamera2 accepts a float AnalogueGain; ISO ≈ gain × 100.
ISO_OPTIONS: dict[str, float | None] = {
    "Auto":  None,
    "100":   1.0,
    "200":   2.0,
    "400":   4.0,
    "800":   8.0,
    "1600":  16.0,
    "3200":  32.0,
}
ISO_DEFAULT = "Auto"

# ── Shutter speed → ExposureTime (µs) ────────────────────────────────────────
SHUTTER_OPTIONS: dict[str, int | None] = {
    "Auto":     None,
    "1/4000":    250,
    "1/2000":    500,
    "1/1000":   1_000,
    "1/500":    2_000,
    "1/250":    4_000,
    "1/125":    8_000,
    "1/60":    16_667,
    "1/30":    33_333,
    "1/15":    66_667,
    "1/8":    125_000,
    "1/4":    250_000,
    "1/2":    500_000,
    "1s":   1_000_000,
    "2s":   2_000_000,
    "4s":   4_000_000,
    "8s":   8_000_000,
    "15s": 15_000_000,
    "30s": 30_000_000,
}
SHUTTER_DEFAULT = "Auto"

# ── DPC (Dead Pixel Correction) → NoiseReductionMode ─────────────────────────
# libcamera's runtime-accessible DPC proxy.  True per-pixel DPC lives in the
# tuning JSON; NoiseReductionMode is the closest controllable knob that
# encompasses defect-pixel masking in the Raspberry Pi ISP pipeline.
DPC_OPTIONS: dict[str, int] = {
    "Off":          0,   # libcamera controls.draft.NoiseReductionModeEnum.Off
    "Fast":         1,   # …Fast
    "HighQuality":  2,   # …HighQuality  (default)
}
DPC_DEFAULT = "HighQuality"

# ── Other ISP defaults ────────────────────────────────────────────────────────
DEFAULT_BRIGHTNESS  =  0.0    # range −1.0 … +1.0
DEFAULT_CONTRAST    =  1.0    # range  0.0 … 32.0
DEFAULT_SATURATION  =  1.0    # range  0.0 … 32.0
DEFAULT_SHARPNESS   =  1.0    # range  0.0 … 16.0
DEFAULT_AWB         = True    # auto white balance on by default


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def ensure_dcim_dir() -> Path:
    """Create ~/Pictures/DCIM if it does not exist and return the path."""
    DCIM_DIR.mkdir(parents=True, exist_ok=True)
    return DCIM_DIR


def next_dng_path() -> Path:
    """Return the next available DNG path inside DCIM_DIR."""
    dcim = ensure_dcim_dir()
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = dcim / f"IMG_{ts}.dng"
    # avoid collision if burst-firing within the same second
    n = 1
    while path.exists():
        path = dcim / f"IMG_{ts}_{n:03d}.dng"
        n += 1
    return path


# ═══════════════════════════════════════════════════════════════════════════════
# Camera wrapper
# ═══════════════════════════════════════════════════════════════════════════════

class Camera:
    """
    Thin wrapper around Picamera2 — single-configuration design.

    The Pi 5 PiSP backend crashes with "TDN output not enabled when TDN
    enabled" whenever you reconfigure from a non-raw mode to a raw-stream
    mode, regardless of NoiseReductionMode settings.  The only reliable fix
    is to NEVER RECONFIGURE at all.

    Strategy: configure ONE mode at startup that includes BOTH a small RGB
    preview stream and a full-resolution raw stream.  The raw stream runs
    continuously alongside the preview.  DNG capture simply grabs the next
    completed request (which already contains the raw frame) and saves it —
    zero mode switching, zero TDN interaction.

    Memory: raw stream in PISP_COMP1 (Pi 5 compressed format) is ~15 MB/frame.
    With buffer_count=2 that's ~30 MB for raw + ~2 MB for preview = ~32 MB
    total, well within the Pi 5 DMA heap.
    """

    def __init__(self):
        if not PICAMERA2_AVAILABLE:
            self._cam = None
            return

        self._cam = Picamera2()

        # Single config: small RGB preview + full-res raw stream, always on.
        # NoiseReductionMode=0 (TDN off) — required when a raw stream is
        # present on PiSP; NR in the processed output is irrelevant since
        # we save the raw Bayer data and post-process externally.
        config = self._cam.create_preview_configuration(
            main={"size": (VIEWFINDER_W, VIEWFINDER_H), "format": "RGB888"},
            raw={"size": (SENSOR_W, SENSOR_H)},
            buffer_count=2,
            controls={
                "NoiseReductionMode": 0,
            },
        )
        self._cam.configure(config)
        self._cam.start()
        time.sleep(1)  # let 3A settle
        self._cam.set_controls({
            "Brightness":  DEFAULT_BRIGHTNESS,
            "Contrast":    DEFAULT_CONTRAST,
            "Saturation":  DEFAULT_SATURATION,
            "Sharpness":   DEFAULT_SHARPNESS,
        })

    # ── Preview frame ─────────────────────────────────────────────────────────

    def capture_preview_frame(self) -> Image.Image | None:
        """Return the current preview frame as a PIL Image (RGB)."""
        if self._cam is None:
            return Image.new("RGB", (VIEWFINDER_W, VIEWFINDER_H), "#0a0a1a")
        try:
            arr = self._cam.capture_array("main")
            return Image.fromarray(arr, "RGB")
        except Exception:
            return None

    # ── DNG capture ───────────────────────────────────────────────────────────

    def capture_dng(self, controls: dict) -> Path:
        """
        Capture a DNG from the always-running raw stream.

        Because the raw stream is configured at startup alongside the preview,
        we never need to stop/reconfigure the camera.  We simply apply the
        requested controls, wait a few frames for them to take effect, then
        capture a request and save its raw buffer as a DNG.

        No mode switch → no TDN state transition → no crash.
        """
        dng_path = next_dng_path()

        if self._cam is None:
            img  = Image.new("RGB", (100, 80), "#222244")
            fake = dng_path.with_suffix(".jpg")
            img.save(fake)
            return fake

        # Apply exposure/gain controls for the capture
        cap_controls: dict = {
            "NoiseReductionMode": 0,
            "Brightness":  controls.get("Brightness",  DEFAULT_BRIGHTNESS),
            "Contrast":    controls.get("Contrast",    DEFAULT_CONTRAST),
            "Saturation":  controls.get("Saturation",  DEFAULT_SATURATION),
            "Sharpness":   controls.get("Sharpness",   DEFAULT_SHARPNESS),
            "AwbEnable":   controls.get("AwbEnable",   True),
        }

        ae_enable = controls.get("AeEnable", True)
        cap_controls["AeEnable"] = ae_enable
        if not ae_enable:
            if "ExposureTime" in controls:
                cap_controls["ExposureTime"] = int(controls["ExposureTime"])
            if "AnalogueGain" in controls:
                cap_controls["AnalogueGain"] = float(controls["AnalogueGain"])

        self._cam.set_controls(cap_controls)

        # Wait for the controls to propagate through the pipeline.
        # At 24 fps one frame is ~42 ms; 5 frames gives plenty of settling
        # time for AE/AGC to converge on the new values.
        time.sleep(0.25)

        # Grab a single completed request — contains both "main" (RGB) and
        # "raw" (Bayer) buffers from the same sensor frame.
        request = self._cam.capture_request()
        try:
            request.save_dng(str(dng_path))
        finally:
            request.release()

        return dng_path

    # ── Runtime control update ────────────────────────────────────────────────

    def apply_controls(self, controls: dict):
        """Push a dict of libcamera controls to the running camera."""
        if self._cam is None:
            return
        try:
            safe = dict(controls)
            safe["NoiseReductionMode"] = 0  # always keep TDN off
            self._cam.set_controls(safe)
        except Exception as exc:
            print(f"[WARN] set_controls failed: {exc}")

    # ── Teardown ──────────────────────────────────────────────────────────────

    def stop(self):
        if self._cam is not None:
            try:
                self._cam.stop()
                self._cam.close()
            except Exception:
                pass


# ═══════════════════════════════════════════════════════════════════════════════
# Main Application
# ═══════════════════════════════════════════════════════════════════════════════

class PiCamApp:
    """Tkinter GUI for the Raspberry Pi HQ Camera."""

    def __init__(self, root: tk.Tk):
        self.root     = root
        self._running = True
        self._busy    = False          # True while DNG capture is in progress

        root.title(APP_TITLE)
        root.configure(bg=BG_DARK)
        root.resizable(False, False)
        root.geometry(f"{WINDOW_W}x{WINDOW_H}")
        root.protocol("WM_DELETE_WINDOW", self._on_close)

        # ── Camera ────────────────────────────────────────────────────────────
        self._camera = Camera()

        # ── Control variables ─────────────────────────────────────────────────
        self._iso_var        = tk.StringVar(value=ISO_DEFAULT)
        self._shutter_var    = tk.StringVar(value=SHUTTER_DEFAULT)
        self._dpc_var        = tk.StringVar(value=DPC_DEFAULT)
        self._awb_var        = tk.BooleanVar(value=DEFAULT_AWB)
        self._brightness_var = tk.DoubleVar(value=DEFAULT_BRIGHTNESS)
        self._contrast_var   = tk.DoubleVar(value=DEFAULT_CONTRAST)
        self._saturation_var = tk.DoubleVar(value=DEFAULT_SATURATION)
        self._sharpness_var  = tk.DoubleVar(value=DEFAULT_SHARPNESS)

        self._status_var     = tk.StringVar(value="Ready")
        self._last_file_var  = tk.StringVar(value="—")
        self._metadata_var   = tk.StringVar(value="—")

        # ── Layout ────────────────────────────────────────────────────────────
        self._build_ui()

        # ── Bind control changes → camera ─────────────────────────────────────
        for var in (self._iso_var, self._shutter_var, self._dpc_var,
                    self._awb_var, self._brightness_var, self._contrast_var,
                    self._saturation_var, self._sharpness_var):
            var.trace_add("write", lambda *_: self._push_controls())

        # ── Start live-view loop ──────────────────────────────────────────────
        self._push_controls()           # apply defaults immediately
        self._schedule_preview()

    # ══════════════════════════════════════════════════════════════════════════
    # UI construction
    # ══════════════════════════════════════════════════════════════════════════

    def _build_ui(self):
        """Assemble the complete UI layout."""
        outer = tk.Frame(self.root, bg=BG_DARK, padx=OUTER_PAD, pady=OUTER_PAD)
        outer.pack(fill="both", expand=True)

        # ── Left: viewfinder ──────────────────────────────────────────────────
        vf_frame = tk.Frame(outer, bg="#000000",
                            relief="solid", bd=2,
                            highlightbackground=ACCENT, highlightthickness=0)
        vf_frame.grid(row=0, column=0, rowspan=2, padx=(0, VF_GAP), sticky="nsew")

        # Title bar above viewfinder
        vf_title = tk.Frame(vf_frame, bg=BG_MID, pady=2)
        vf_title.pack(fill="x")
        tk.Label(vf_title, text="⬤  LIVE VIEW", font=("Courier", 9, "bold"),
                 fg=ACCENT, bg=BG_MID).pack(side="left", padx=8)
        self._res_label = tk.Label(vf_title, text=f"{VIEWFINDER_W}×{VIEWFINDER_H}",
                                   font=("Courier", 8), fg=TEXT_DIM, bg=BG_MID)
        self._res_label.pack(side="right", padx=8)

        self._vf_label = tk.Label(vf_frame, bg="#000000",
                                  width=VIEWFINDER_W, height=VIEWFINDER_H)
        self._vf_label.pack()

        # Metadata overlay under viewfinder
        meta_bar = tk.Frame(vf_frame, bg=BG_MID, pady=1)
        meta_bar.pack(fill="x")
        tk.Label(meta_bar, textvariable=self._metadata_var,
                 font=("Courier", 8), fg=TEXT_DIM, bg=BG_MID).pack()

        # Capture button (big, under viewfinder)
        cap_btn = tk.Button(
            vf_frame, text="◉  CAPTURE  DNG",
            font=("Helvetica", 13, "bold"),
            fg=TEXT_LIGHT, bg=BTN_CAPTURE,
            activeforeground=TEXT_LIGHT, activebackground=BTN_CAPTURE_HOV,
            relief="flat", cursor="hand2",
            padx=10, pady=6,
            command=self._on_capture,
        )
        cap_btn.pack(fill="x", padx=2, pady=(2, 2))
        cap_btn.bind("<Enter>", lambda e: cap_btn.config(bg=BTN_CAPTURE_HOV))
        cap_btn.bind("<Leave>", lambda e: cap_btn.config(bg=BTN_CAPTURE))

        # ── Right: control panel ───────────────────────────────────────────────
        panel = tk.Frame(outer, bg=BG_MID, relief="flat",
                         padx=8, pady=6, width=PANEL_W)
        panel.grid(row=0, column=1, sticky="nsew")
        panel.grid_propagate(False)

        # Panel header
        tk.Label(panel, text="CAMERA CONTROLS",
                 font=("Courier", 9, "bold"),
                 fg=ACCENT, bg=BG_MID).grid(row=0, column=0, columnspan=2,
                                             pady=(0, 6))

        row = 1
        row = self._add_combobox(panel, row, "ISO",       self._iso_var,
                                 list(ISO_OPTIONS.keys()))
        row = self._add_combobox(panel, row, "Shutter",   self._shutter_var,
                                 list(SHUTTER_OPTIONS.keys()))
        row = self._add_combobox(panel, row, "DPC Mode",  self._dpc_var,
                                 list(DPC_OPTIONS.keys()))

        self._add_separator(panel, row); row += 1

        row = self._add_checkbutton(panel, row, "Auto White Balance", self._awb_var)

        self._add_separator(panel, row); row += 1

        row = self._add_scale(panel, row, "Brightness",  self._brightness_var,
                              -1.0, 1.0, resolution=0.05)
        row = self._add_scale(panel, row, "Contrast",    self._contrast_var,
                               0.0, 8.0, resolution=0.1)
        row = self._add_scale(panel, row, "Saturation",  self._saturation_var,
                               0.0, 4.0, resolution=0.1)
        row = self._add_scale(panel, row, "Sharpness",   self._sharpness_var,
                               0.0, 8.0, resolution=0.1)

        self._add_separator(panel, row); row += 1

        # Reset to defaults button
        tk.Button(
            panel, text="Reset Defaults",
            font=("Helvetica", 8), fg=TEXT_DIM, bg=BG_PANEL,
            activeforeground=TEXT_LIGHT, activebackground=BG_PANEL,
            relief="flat", cursor="hand2", pady=3,
            command=self._reset_defaults,
        ).grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 2))
        row += 1

        # ── Status bar (bottom, full width) ───────────────────────────────────
        status_frame = tk.Frame(outer, bg=BG_PANEL, pady=3)
        status_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(4, 0))

        tk.Label(status_frame, text="Status:",
                 font=("Courier", 8, "bold"), fg=TEXT_DIM, bg=BG_PANEL
                 ).pack(side="left", padx=(8, 2))
        tk.Label(status_frame, textvariable=self._status_var,
                 font=("Courier", 8), fg=TEXT_LIGHT, bg=BG_PANEL
                 ).pack(side="left")

        tk.Label(status_frame, text="Last:",
                 font=("Courier", 8, "bold"), fg=TEXT_DIM, bg=BG_PANEL
                 ).pack(side="left", padx=(16, 2))
        tk.Label(status_frame, textvariable=self._last_file_var,
                 font=("Courier", 8), fg=BTN_OK, bg=BG_PANEL
                 ).pack(side="left")

        if not PICAMERA2_AVAILABLE:
            demo_lbl = tk.Label(status_frame, text="  ⚠ DEMO MODE (no camera)",
                                font=("Courier", 8, "bold"), fg="#f39c12",
                                bg=BG_PANEL)
            demo_lbl.pack(side="right", padx=8)

    # ── Widget helpers ────────────────────────────────────────────────────────

    def _add_combobox(self, parent, row: int, label: str,
                      var: tk.StringVar, values: list) -> int:
        tk.Label(parent, text=label + ":",
                 font=("Helvetica", 8), fg=TEXT_DIM, bg=BG_MID,
                 anchor="w").grid(row=row, column=0, sticky="w", pady=1)
        style_name = f"{label}.TCombobox"
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(style_name,
                        fieldbackground=BG_PANEL, background=BG_PANEL,
                        foreground=TEXT_LIGHT, selectbackground=ACCENT,
                        arrowcolor=TEXT_LIGHT)
        cb = ttk.Combobox(parent, textvariable=var, values=values,
                          state="readonly", width=11, style=style_name)
        cb.grid(row=row, column=1, sticky="ew", padx=(4, 0), pady=1)
        return row + 1

    def _add_checkbutton(self, parent, row: int,
                         label: str, var: tk.BooleanVar) -> int:
        tk.Checkbutton(
            parent, text=label, variable=var,
            font=("Helvetica", 8), fg=TEXT_LIGHT, bg=BG_MID,
            selectcolor=BG_PANEL, activebackground=BG_MID,
            activeforeground=TEXT_LIGHT,
        ).grid(row=row, column=0, columnspan=2, sticky="w", pady=2)
        return row + 1

    def _add_scale(self, parent, row: int, label: str,
                   var: tk.DoubleVar, from_: float, to: float,
                   resolution: float = 0.1) -> int:
        tk.Label(parent, text=label + ":",
                 font=("Helvetica", 8), fg=TEXT_DIM, bg=BG_MID,
                 anchor="w").grid(row=row, column=0, sticky="w")
        val_label = tk.Label(parent,
                             font=("Courier", 8), fg=TEXT_LIGHT, bg=BG_MID,
                             width=5, anchor="e")
        val_label.grid(row=row, column=1, sticky="e")

        def _update_label(*_):
            val_label.config(text=f"{var.get():.2f}")

        var.trace_add("write", _update_label)
        _update_label()

        scale = tk.Scale(
            parent, variable=var,
            from_=from_, to=to, resolution=resolution,
            orient="horizontal", showvalue=False,
            bg=BG_MID, fg=TEXT_LIGHT, troughcolor=BG_PANEL,
            activebackground=ACCENT, highlightthickness=0,
            length=175,
        )
        scale.grid(row=row + 1, column=0, columnspan=2, sticky="ew", pady=(0, 2))
        return row + 2

    def _add_separator(self, parent, row: int):
        ttk.Separator(parent, orient="horizontal").grid(
            row=row, column=0, columnspan=2, sticky="ew", pady=6)

    # ══════════════════════════════════════════════════════════════════════════
    # Camera control logic
    # ══════════════════════════════════════════════════════════════════════════

    def _build_controls_dict(self) -> dict:
        """
        Translate current UI state into a picamera2 controls dict.
        Also embeds logical flags (AeEnable, AwbEnable) for use in
        both apply_controls() and capture_dng().

        NOTE: FrameDurationLimits is intentionally excluded here.
        For preview, picamera2 manages frame timing automatically.
        For still capture, embedding it in the still config's controls
        conflicts with the mode switch and can cause OOM / stalls.
        """
        controls: dict = {}

        # ── ISO / Gain ────────────────────────────────────────────────────────
        iso_label     = self._iso_var.get()
        analogue_gain = ISO_OPTIONS.get(iso_label)

        # ── Shutter / Exposure ────────────────────────────────────────────────
        shutter_label = self._shutter_var.get()
        exposure_us   = SHUTTER_OPTIONS.get(shutter_label)

        # Auto-Exposure: disable only when at least one of ISO/shutter is fixed
        ae_enable = (analogue_gain is None and exposure_us is None)
        controls["AeEnable"] = ae_enable

        if not ae_enable:
            if analogue_gain is not None:
                controls["AnalogueGain"] = float(analogue_gain)
            if exposure_us is not None:
                controls["ExposureTime"] = int(exposure_us)
            # FrameDurationLimits is set separately in apply_controls only
            # (not passed to capture_dng) to avoid conflicting with the
            # still-mode reconfiguration inside switch_mode_and_capture_file.

        # ── AWB ───────────────────────────────────────────────────────────────
        controls["AwbEnable"] = bool(self._awb_var.get())

        # ── ISP adjustments ───────────────────────────────────────────────────
        controls["Brightness"]         = float(self._brightness_var.get())
        controls["Contrast"]           = float(self._contrast_var.get())
        controls["Saturation"]         = float(self._saturation_var.get())
        controls["Sharpness"]          = float(self._sharpness_var.get())

        # ── DPC (Dead Pixel Correction) via NoiseReductionMode ────────────────
        dpc_label = self._dpc_var.get()
        controls["NoiseReductionMode"] = DPC_OPTIONS.get(dpc_label, 2)

        return controls

    def _push_controls(self):
        """Apply current UI settings to the running preview camera."""
        controls = self._build_controls_dict()

        # FrameDurationLimits is preview-only: it keeps the sensor from dropping
        # below the chosen shutter speed during live view.  We never pass it to
        # capture_dng() because switch_mode_and_capture_file manages timing itself.
        preview_controls = dict(controls)
        exposure_us = controls.get("ExposureTime")
        if exposure_us is not None:
            preview_controls["FrameDurationLimits"] = (
                int(exposure_us),
                int(exposure_us) + 10_000,
            )

        self._camera.apply_controls(preview_controls)

    # ══════════════════════════════════════════════════════════════════════════
    # Live viewfinder loop
    # ══════════════════════════════════════════════════════════════════════════

    def _schedule_preview(self):
        """Schedule the next frame update."""
        if self._running:
            self.root.after(PREVIEW_DELAY, self._update_preview)

    def _update_preview(self):
        """Grab a frame and push it to the viewfinder label."""
        if not self._running:
            return

        if not self._busy:
            frame = self._camera.capture_preview_frame()
            if frame is not None:
                try:
                    photo = ImageTk.PhotoImage(frame)
                    self._vf_label.config(image=photo)
                    self._vf_label.image = photo   # keep reference alive
                except Exception:
                    pass

        self._schedule_preview()

    # ══════════════════════════════════════════════════════════════════════════
    # Capture
    # ══════════════════════════════════════════════════════════════════════════

    def _on_capture(self):
        """
        Triggered by the Capture button (main thread).

        _build_controls_dict() reads tkinter StringVar/DoubleVar/BooleanVar
        objects which are NOT thread-safe — calling .get() from a worker
        thread raises a silent internal exception producing an empty error
        dialog with nothing in the console.  Snapshot the controls dict
        HERE on the main thread before handing off to the worker.
        """
        if self._busy:
            self._status_var.set("Busy — please wait…")
            return

        try:
            controls = self._build_controls_dict()
        except Exception:
            self._status_var.set("Control error")
            messagebox.showerror("Control Error", traceback.format_exc())
            return

        self._busy = True
        self._status_var.set("Capturing…")
        threading.Thread(target=self._do_capture, args=(controls,), daemon=True).start()

    def _do_capture(self, controls: dict):
        """
        Background thread: captures a full-resolution DNG.

        Receives the already-built controls dict from the main thread so
        no tkinter variables are touched here.  Sleeps briefly so any
        capture_array() call already in flight on the main thread completes
        before switch_mode_and_capture_file() reconfigures the hardware.
        """
        try:
            time.sleep(PREVIEW_DELAY / 500.0)   # ≈ 2 frame periods in seconds
            dng_path   = self._camera.capture_dng(controls)
            short_name = dng_path.name
            self.root.after(0, self._capture_done, str(dng_path), short_name, None)
        except Exception:
            tb = traceback.format_exc()
            print(f"[ERROR] Capture failed:\n{tb}", flush=True)
            self.root.after(0, self._capture_done, None, None, tb)

    def _capture_done(self, full_path: str | None, name: str | None, error: str | None):
        """Called on the main thread after capture completes."""
        self._busy = False
        if error:
            self._status_var.set("Error — see console")
            messagebox.showerror("Capture Error", error)

        else:
            self._status_var.set("Saved ✓")
            self._last_file_var.set(name)
            print(f"[INFO] Saved: {full_path}")

    # ══════════════════════════════════════════════════════════════════════════
    # Reset / close
    # ══════════════════════════════════════════════════════════════════════════

    def _reset_defaults(self):
        self._iso_var.set(ISO_DEFAULT)
        self._shutter_var.set(SHUTTER_DEFAULT)
        self._dpc_var.set(DPC_DEFAULT)
        self._awb_var.set(DEFAULT_AWB)
        self._brightness_var.set(DEFAULT_BRIGHTNESS)
        self._contrast_var.set(DEFAULT_CONTRAST)
        self._saturation_var.set(DEFAULT_SATURATION)
        self._sharpness_var.set(DEFAULT_SHARPNESS)
        self._status_var.set("Defaults restored")

    def _on_close(self):
        self._running = False
        self.root.after(100, self._shutdown)

    def _shutdown(self):
        self._camera.stop()
        self.root.destroy()


# ═══════════════════════════════════════════════════════════════════════════════
# Entry point
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    if not PICAMERA2_AVAILABLE:
        print("=" * 60)
        print("  picamera2 not installed — running in UI demo mode.")
        print("  Install with:  sudo apt install python3-picamera2")
        print("=" * 60)

    ensure_dcim_dir()
    print(f"[INFO] Photos will be saved to: {DCIM_DIR}")

    root = tk.Tk()
    app  = PiCamApp(root)  # noqa: F841
    root.mainloop()


if __name__ == "__main__":
    main()
