#!/usr/bin/env python3
"""
src/main.py — PiCam V2 entry point.

V2 of the Raspberry Pi HQ Camera GUI, built on picamera2/libcamera.
Run:
    python src/main.py [--fullscreen] [--geometry WxH] [--demo]
"""

from __future__ import annotations

import argparse
import logging
import os
import subprocess
import sys
import threading
import time
import traceback
from datetime import datetime
from pathlib import Path

import tkinter as tk
from tkinter import simpledialog, ttk, messagebox

from PIL import Image, ImageTk

# ── Add src/ to path so relative imports work when run as a script ────────────
_SRC = Path(__file__).resolve().parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from settings.defaults import DEFAULTS, VERSION
from settings.settings_manager import SettingsManager
from settings.profiles import ProfileManager, BUILTIN_PROFILES

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("picam2")

# ──────────────────────────────────────────────────────────────────────────────
# picamera2 import — graceful fallback so the file can be opened on non-Pi hosts
# ──────────────────────────────────────────────────────────────────────────────
try:
    from picamera2 import Picamera2
    PICAMERA2_AVAILABLE = True
except ImportError:
    PICAMERA2_AVAILABLE = False
    logger.warning("picamera2 not found — running in DEMO mode (no camera)")

# ═══════════════════════════════════════════════════════════════════════════════
# Constants / Defaults
# ═══════════════════════════════════════════════════════════════════════════════

APP_TITLE   = f"PiCam V{VERSION}"
WINDOW_W    = 800
WINDOW_H    = 480
OUTER_PAD   = 5
PANEL_W     = 205
VF_GAP      = 8
VF_CHROME_H = 78
VF_CHROME_W = 4
STATUS_H    = 26

# IMX477 HQ Camera native sensor resolution
SENSOR_W    = 4056
SENSOR_H    = 3040

PREVIEW_FPS   = 24
PREVIEW_DELAY = int(1000 / PREVIEW_FPS)

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
FLASH_GREEN     = "#00ff88"

# ── ISO → AnalogueGain ────────────────────────────────────────────────────────
ISO_OPTIONS: dict[str, float | None] = {
    "Auto":  None,
    "100":   1.0,
    "200":   2.0,
    "400":   4.0,
    "800":   8.0,
    "1600":  16.0,
    "3200":  32.0,
}

# ── Shutter speed → ExposureTime (µs) ─────────────────────────────────────────
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

# ── DPC (Dead Pixel Correction) → NoiseReductionMode ──────────────────────────
DPC_OPTIONS: dict[str, int] = {
    "Off":         0,
    "Fast":        1,
    "HighQuality": 2,
}

# ── Timer options → seconds (None = Off, -1 = Custom) ─────────────────────────
TIMER_OPTIONS: dict[str, int | None] = {
    "Off":    None,
    "2s":     2,
    "5s":     5,
    "10s":    10,
    "Custom": -1,
}


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _resolve_dcim_dir() -> Path:
    """Resolve ~/Pictures/DCIM, respecting SUDO_USER."""
    sudo_user = os.environ.get("SUDO_USER")
    if sudo_user:
        import pwd
        home = Path(pwd.getpwnam(sudo_user).pw_dir)
    else:
        home = Path.home()
    return home / "Pictures" / "DCIM"


DCIM_DIR = _resolve_dcim_dir()


def ensure_dcim_dir() -> Path:
    DCIM_DIR.mkdir(parents=True, exist_ok=True)
    return DCIM_DIR


def next_capture_path(fmt: str = "dng") -> Path:
    """Return next available capture path inside DCIM_DIR."""
    dcim = ensure_dcim_dir()
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    ext  = fmt.lower()
    path = dcim / f"IMG_{ts}.{ext}"
    n = 1
    while path.exists():
        path = dcim / f"IMG_{ts}_{n:03d}.{ext}"
        n += 1
    return path


def aspect_fit(sensor_w: int, sensor_h: int,
               container_w: int, container_h: int) -> tuple[int, int]:
    """
    Return (width, height) — the largest rectangle that fits inside
    (container_w × container_h) while preserving the sensor aspect ratio.
    """
    sensor_ratio    = sensor_w / sensor_h
    container_ratio = container_w / container_h
    if sensor_ratio > container_ratio:
        # Constrained by width
        w = container_w
        h = int(container_w / sensor_ratio)
    else:
        # Constrained by height
        h = container_h
        w = int(container_h * sensor_ratio)
    return w, h


def _inject_exif_dng(path: Path, metadata: dict, sensor_name: str = "") -> None:
    """
    Attempt to inject EXIF tags into a DNG file using exiftool.
    Silently skips if exiftool is not installed.
    """
    try:
        subprocess.run(["exiftool", "--version"],
                       capture_output=True, check=True, timeout=5)
    except (FileNotFoundError, subprocess.CalledProcessError, OSError):
        return

    now = datetime.now().strftime("%Y:%m:%d %H:%M:%S")
    args = [
        "exiftool", "-overwrite_original",
        f"-DateTimeOriginal={now}",
        "-Make=Raspberry Pi",
        f"-Model=PiCam2 v{VERSION}",
    ]
    if sensor_name:
        args.append(f"-UserComment=Sensor: {sensor_name}")
    if "ExposureTime" in metadata:
        exp_us = int(metadata["ExposureTime"])
        args.append(f"-ExposureTime={exp_us}/1000000")
    if "AnalogueGain" in metadata:
        iso = int(metadata["AnalogueGain"] * 100)
        args.append(f"-ISO={iso}")
    args.append(str(path))

    try:
        subprocess.run(args, capture_output=True, check=True, timeout=30)
    except subprocess.CalledProcessError as exc:
        logger.warning("exiftool failed: %s", exc.stderr.decode(errors="replace"))
    except subprocess.TimeoutExpired:
        logger.warning("exiftool timed out for %s", path)


# ═══════════════════════════════════════════════════════════════════════════════
# Camera wrapper
# ═══════════════════════════════════════════════════════════════════════════════

class Camera:
    """
    Thin wrapper around Picamera2 — single-configuration design.

    The Pi 5 PiSP backend crashes with "TDN output not enabled when TDN
    enabled" whenever you reconfigure from a non-raw mode to a raw-stream
    mode.  The only reliable fix is to NEVER RECONFIGURE at runtime.

    Strategy: configure ONE mode at startup that includes BOTH a small RGB
    preview stream and a full-resolution raw stream.  Captures simply grab
    the next completed request (which already contains the raw frame).
    """

    def __init__(self, preview_w: int, preview_h: int) -> None:
        self._preview_w = preview_w
        self._preview_h = preview_h
        self._last_metadata: dict = {}

        if not PICAMERA2_AVAILABLE:
            self._cam = None
            return

        self._cam = Picamera2()
        config = self._cam.create_preview_configuration(
            main={"size": (preview_w, preview_h), "format": "RGB888"},
            raw={"size": (SENSOR_W, SENSOR_H)},
            buffer_count=2,
            controls={"NoiseReductionMode": 0},
        )
        self._cam.configure(config)
        self._cam.start()
        time.sleep(1)   # let 3A settle
        self._cam.set_controls({
            "Brightness":  DEFAULTS["camera"]["brightness"],
            "Contrast":    DEFAULTS["camera"]["contrast"],
            "Saturation":  DEFAULTS["camera"]["saturation"],
            "Sharpness":   DEFAULTS["camera"]["sharpness"],
        })

    def get_sensor_name(self) -> str:
        if self._cam is None:
            return "Demo"
        try:
            props = self._cam.camera_properties
            return props.get("Model", "Unknown")
        except Exception:
            return "Unknown"

    def capture_preview_frame(self) -> Image.Image | None:
        if self._cam is None:
            return Image.new("RGB", (self._preview_w, self._preview_h), "#0a0a1a")
        try:
            arr = self._cam.capture_array("main")
            return Image.fromarray(arr, "RGB")
        except Exception:
            return None

    def capture_dng(self, controls: dict) -> tuple[Path, dict]:
        """
        Capture a DNG from the always-running raw stream.
        Returns (dng_path, metadata_dict).
        """
        dng_path = next_capture_path("dng")

        if self._cam is None:
            img  = Image.new("RGB", (100, 80), "#222244")
            fake = dng_path.with_suffix(".jpg")
            img.save(fake)
            return fake, {}

        cap_controls: dict = {
            "NoiseReductionMode": 0,
            "Brightness":  controls.get("Brightness",  DEFAULTS["camera"]["brightness"]),
            "Contrast":    controls.get("Contrast",    DEFAULTS["camera"]["contrast"]),
            "Saturation":  controls.get("Saturation",  DEFAULTS["camera"]["saturation"]),
            "Sharpness":   controls.get("Sharpness",   DEFAULTS["camera"]["sharpness"]),
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
        time.sleep(0.25)

        request = self._cam.capture_request()
        try:
            metadata = request.get_metadata()
            self._last_metadata = metadata
            request.save_dng(str(dng_path))
        finally:
            request.release()

        return dng_path, metadata

    def apply_controls(self, controls: dict) -> None:
        if self._cam is None:
            return
        try:
            safe = dict(controls)
            safe.setdefault("NoiseReductionMode", 0)
            self._cam.set_controls(safe)
        except Exception as exc:
            logger.warning("set_controls failed: %s", exc)

    def stop(self) -> None:
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
    """Tkinter GUI for the Raspberry Pi HQ Camera — V2."""

    STATUS_CLEAR_MS = 3000   # ms before status resets to "Ready"

    def __init__(self, root: tk.Tk, settings: SettingsManager,
                 profiles: ProfileManager, fullscreen: bool = False) -> None:
        self.root      = root
        self._settings = settings
        self._profiles = profiles
        self._running  = True
        self._busy     = False
        self._timer_id: str | None = None
        self._countdown: int = 0
        self._status_clear_id: str | None = None

        # ── Derive viewfinder size with correct aspect ratio ──────────────────
        container_w = WINDOW_W - (OUTER_PAD * 2) - PANEL_W - VF_GAP - VF_CHROME_W
        container_h = WINDOW_H - (OUTER_PAD * 2) - VF_CHROME_H - STATUS_H
        self._vf_w, self._vf_h = aspect_fit(SENSOR_W, SENSOR_H,
                                             container_w, container_h)

        root.title(APP_TITLE)
        root.configure(bg=BG_DARK)
        root.resizable(False, False)
        root.geometry(f"{WINDOW_W}x{WINDOW_H}")
        root.protocol("WM_DELETE_WINDOW", self._on_close)

        if fullscreen:
            root.attributes("-fullscreen", True)

        # ── Camera ────────────────────────────────────────────────────────────
        self._camera = Camera(self._vf_w, self._vf_h)
        self._sensor_name = self._camera.get_sensor_name()

        # ── Control variables (restored from settings) ────────────────────────
        boot = settings.get_boot_camera_state()
        self._iso_var        = tk.StringVar(value=boot.get("iso",        DEFAULTS["camera"]["iso"]))
        self._shutter_var    = tk.StringVar(value=boot.get("shutter",    DEFAULTS["camera"]["shutter"]))
        self._dpc_var        = tk.StringVar(value=boot.get("dpc",        DEFAULTS["camera"]["dpc"]))
        self._awb_var        = tk.BooleanVar(value=boot.get("awb",       DEFAULTS["camera"]["awb"]))
        self._brightness_var = tk.DoubleVar(value=boot.get("brightness", DEFAULTS["camera"]["brightness"]))
        self._contrast_var   = tk.DoubleVar(value=boot.get("contrast",   DEFAULTS["camera"]["contrast"]))
        self._saturation_var = tk.DoubleVar(value=boot.get("saturation", DEFAULTS["camera"]["saturation"]))
        self._sharpness_var  = tk.DoubleVar(value=boot.get("sharpness",  DEFAULTS["camera"]["sharpness"]))

        timer_val = settings.get("capture.timer", DEFAULTS["capture"]["timer"])
        self._timer_var      = tk.StringVar(value=timer_val)
        self._profile_var    = tk.StringVar(value="Default")

        self._status_var     = tk.StringVar(value="Ready")
        self._last_file_var  = tk.StringVar(value="—")
        self._metadata_var   = tk.StringVar(value="—")
        self._countdown_var  = tk.StringVar(value="")

        # ── Build UI ──────────────────────────────────────────────────────────
        self._build_ui()
        self._apply_combobox_style()

        # ── Persist control changes ───────────────────────────────────────────
        for key, var in [
            ("camera.iso",        self._iso_var),
            ("camera.shutter",    self._shutter_var),
            ("camera.dpc",        self._dpc_var),
            ("camera.awb",        self._awb_var),
            ("camera.brightness", self._brightness_var),
            ("camera.contrast",   self._contrast_var),
            ("camera.saturation", self._saturation_var),
            ("camera.sharpness",  self._sharpness_var),
            ("capture.timer",     self._timer_var),
        ]:
            var.trace_add("write", lambda *_, k=key, v=var: self._on_control_change(k, v))

        # ── Apply controls & start preview ────────────────────────────────────
        self._push_controls()
        self._schedule_preview()

    # ══════════════════════════════════════════════════════════════════════════
    # UI construction
    # ══════════════════════════════════════════════════════════════════════════

    def _build_ui(self) -> None:
        outer = tk.Frame(self.root, bg=BG_DARK, padx=OUTER_PAD, pady=OUTER_PAD)
        outer.pack(fill="both", expand=True)

        # ── Left: viewfinder ──────────────────────────────────────────────────
        self._vf_frame = tk.Frame(outer, bg="#000000",
                                  relief="solid", bd=2,
                                  highlightbackground=ACCENT,
                                  highlightthickness=0)
        self._vf_frame.grid(row=0, column=0, rowspan=2,
                             padx=(0, VF_GAP), sticky="nsew")

        # Title bar
        vf_title = tk.Frame(self._vf_frame, bg=BG_MID, pady=2)
        vf_title.pack(fill="x")
        tk.Label(vf_title, text="⬤  LIVE VIEW",
                 font=("Courier", 9, "bold"), fg=ACCENT, bg=BG_MID
                 ).pack(side="left", padx=8)
        tk.Label(vf_title, text=f"{self._vf_w}×{self._vf_h}",
                 font=("Courier", 8), fg=TEXT_DIM, bg=BG_MID
                 ).pack(side="right", padx=8)

        # Viewfinder label (sized to corrected aspect ratio)
        self._vf_label = tk.Label(self._vf_frame, bg="#000000",
                                  width=self._vf_w, height=self._vf_h)
        self._vf_label.pack()

        # Countdown overlay (placed over the viewfinder during timer countdown)
        self._countdown_label = tk.Label(
            self._vf_frame,
            textvariable=self._countdown_var,
            font=("Helvetica", 72, "bold"),
            fg=FLASH_GREEN, bg="#000000",
        )

        # Metadata bar
        meta_bar = tk.Frame(self._vf_frame, bg=BG_MID, pady=1)
        meta_bar.pack(fill="x")
        tk.Label(meta_bar, textvariable=self._metadata_var,
                 font=("Courier", 8), fg=TEXT_DIM, bg=BG_MID).pack()

        # Capture button
        cap_btn = tk.Button(
            self._vf_frame, text="◉  CAPTURE  DNG",
            font=("Helvetica", 13, "bold"),
            fg=TEXT_LIGHT, bg=BTN_CAPTURE,
            activeforeground=TEXT_LIGHT, activebackground=BTN_CAPTURE_HOV,
            relief="flat", cursor="hand2", padx=10, pady=6,
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

        tk.Label(panel, text="CAMERA CONTROLS",
                 font=("Courier", 9, "bold"), fg=ACCENT, bg=BG_MID
                 ).grid(row=0, column=0, columnspan=2, pady=(0, 4))

        row = 1

        # Profile selector
        tk.Label(panel, text="Profile:",
                 font=("Helvetica", 8), fg=TEXT_DIM, bg=BG_MID,
                 anchor="w").grid(row=row, column=0, sticky="w", pady=1)
        self._profile_cb = ttk.Combobox(
            panel, textvariable=self._profile_var,
            values=self._profiles.list_names(),
            state="readonly", width=11, style="Profile.TCombobox",
        )
        self._profile_cb.grid(row=row, column=1, sticky="ew", padx=(4, 0), pady=1)
        row += 1

        profile_btn_frame = tk.Frame(panel, bg=BG_MID)
        profile_btn_frame.grid(row=row, column=0, columnspan=2,
                                sticky="ew", pady=(0, 2))
        for text, cmd in [("Load", self._load_profile),
                           ("Save As", self._save_profile_as),
                           ("Delete", self._delete_profile)]:
            tk.Button(profile_btn_frame, text=text, font=("Helvetica", 7),
                      fg=TEXT_LIGHT if text != "Delete" else TEXT_DIM,
                      bg=BG_PANEL, relief="flat", cursor="hand2",
                      command=cmd,
                      ).pack(side="left", expand=True, fill="x", padx=(0, 1))
        row += 1

        self._add_separator(panel, row); row += 1

        row = self._add_combobox(panel, row, "ISO",      self._iso_var,
                                 list(ISO_OPTIONS.keys()))
        row = self._add_combobox(panel, row, "Shutter",  self._shutter_var,
                                 list(SHUTTER_OPTIONS.keys()))
        row = self._add_combobox(panel, row, "DPC",      self._dpc_var,
                                 list(DPC_OPTIONS.keys()))
        row = self._add_combobox(panel, row, "Timer",    self._timer_var,
                                 list(TIMER_OPTIONS.keys()))

        self._add_separator(panel, row); row += 1

        row = self._add_checkbutton(panel, row, "Auto White Balance", self._awb_var)

        self._add_separator(panel, row); row += 1

        row = self._add_scale(panel, row, "Brightness", self._brightness_var,
                              -1.0, 1.0, resolution=0.05)
        row = self._add_scale(panel, row, "Contrast",   self._contrast_var,
                               0.0, 8.0, resolution=0.1)
        row = self._add_scale(panel, row, "Saturation", self._saturation_var,
                               0.0, 4.0, resolution=0.1)
        row = self._add_scale(panel, row, "Sharpness",  self._sharpness_var,
                               0.0, 8.0, resolution=0.1)

        self._add_separator(panel, row); row += 1

        btn_frame = tk.Frame(panel, bg=BG_MID)
        btn_frame.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 2))
        tk.Button(btn_frame, text="Reset", font=("Helvetica", 8),
                  fg=TEXT_DIM, bg=BG_PANEL,
                  activeforeground=TEXT_LIGHT, activebackground=BG_PANEL,
                  relief="flat", cursor="hand2", pady=3,
                  command=self._reset_defaults,
                  ).pack(side="left", expand=True, fill="x", padx=(0, 1))
        tk.Button(btn_frame, text="Save Defaults", font=("Helvetica", 8),
                  fg=TEXT_DIM, bg=BG_PANEL,
                  activeforeground=TEXT_LIGHT, activebackground=BG_PANEL,
                  relief="flat", cursor="hand2", pady=3,
                  command=self._save_as_defaults,
                  ).pack(side="left", expand=True, fill="x")
        row += 1

        # ── Status bar ────────────────────────────────────────────────────────
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
            tk.Label(status_frame, text="  ⚠ DEMO MODE (no camera)",
                     font=("Courier", 8, "bold"), fg="#f39c12", bg=BG_PANEL
                     ).pack(side="right", padx=8)

    # ── Widget helpers ─────────────────────────────────────────────────────────

    def _apply_combobox_style(self) -> None:
        """Fix combobox dropdown colours so text is always visible."""
        style = ttk.Style()
        style.theme_use("clam")
        for name in ["Profile", "ISO", "Shutter", "DPC", "Timer"]:
            style.configure(
                f"{name}.TCombobox",
                fieldbackground=BG_PANEL,
                background=BG_PANEL,
                foreground=TEXT_LIGHT,
                selectbackground=ACCENT,
                selectforeground=TEXT_LIGHT,
                arrowcolor=TEXT_LIGHT,
            )
        # Force the popdown listbox colours
        self.root.option_add("*TCombobox*Listbox.background", BG_PANEL)
        self.root.option_add("*TCombobox*Listbox.foreground", TEXT_LIGHT)
        self.root.option_add("*TCombobox*Listbox.selectBackground", ACCENT)
        self.root.option_add("*TCombobox*Listbox.selectForeground", TEXT_LIGHT)

    def _add_combobox(self, parent: tk.Frame, row: int, label: str,
                      var: tk.StringVar, values: list) -> int:
        tk.Label(parent, text=label + ":",
                 font=("Helvetica", 8), fg=TEXT_DIM, bg=BG_MID,
                 anchor="w").grid(row=row, column=0, sticky="w", pady=1)
        cb = ttk.Combobox(parent, textvariable=var, values=values,
                          state="readonly", width=11,
                          style=f"{label}.TCombobox")
        cb.grid(row=row, column=1, sticky="ew", padx=(4, 0), pady=1)
        return row + 1

    def _add_checkbutton(self, parent: tk.Frame, row: int,
                         label: str, var: tk.BooleanVar) -> int:
        tk.Checkbutton(
            parent, text=label, variable=var,
            font=("Helvetica", 8), fg=TEXT_LIGHT, bg=BG_MID,
            selectcolor=BG_PANEL, activebackground=BG_MID,
            activeforeground=TEXT_LIGHT,
        ).grid(row=row, column=0, columnspan=2, sticky="w", pady=2)
        return row + 1

    def _add_scale(self, parent: tk.Frame, row: int, label: str,
                   var: tk.DoubleVar, from_: float, to: float,
                   resolution: float = 0.1) -> int:
        tk.Label(parent, text=label + ":",
                 font=("Helvetica", 8), fg=TEXT_DIM, bg=BG_MID,
                 anchor="w").grid(row=row, column=0, sticky="w")
        val_label = tk.Label(parent, font=("Courier", 8), fg=TEXT_LIGHT,
                             bg=BG_MID, width=5, anchor="e")
        val_label.grid(row=row, column=1, sticky="e")

        def _update(*_: object) -> None:
            val_label.config(text=f"{var.get():.2f}")

        var.trace_add("write", _update)
        _update()

        tk.Scale(
            parent, variable=var, from_=from_, to=to, resolution=resolution,
            orient="horizontal", showvalue=False,
            bg=BG_MID, fg=TEXT_LIGHT, troughcolor=BG_PANEL,
            activebackground=ACCENT, highlightthickness=0, length=175,
        ).grid(row=row + 1, column=0, columnspan=2, sticky="ew", pady=(0, 2))
        return row + 2

    def _add_separator(self, parent: tk.Frame, row: int) -> None:
        ttk.Separator(parent, orient="horizontal").grid(
            row=row, column=0, columnspan=2, sticky="ew", pady=4)

    # ══════════════════════════════════════════════════════════════════════════
    # Settings persistence
    # ══════════════════════════════════════════════════════════════════════════

    def _on_control_change(self, key: str, var: tk.Variable) -> None:
        try:
            self._settings.set(key, var.get())
            self._settings.save()
        except Exception as exc:
            logger.debug("Settings save failed for %s: %s", key, exc)
        self._push_controls()

    def _current_camera_state(self) -> dict:
        return {
            "iso":        self._iso_var.get(),
            "shutter":    self._shutter_var.get(),
            "dpc":        self._dpc_var.get(),
            "awb":        bool(self._awb_var.get()),
            "brightness": float(self._brightness_var.get()),
            "contrast":   float(self._contrast_var.get()),
            "saturation": float(self._saturation_var.get()),
            "sharpness":  float(self._sharpness_var.get()),
        }

    def _apply_camera_state(self, state: dict) -> None:
        self._iso_var.set(state.get("iso",        DEFAULTS["camera"]["iso"]))
        self._shutter_var.set(state.get("shutter",    DEFAULTS["camera"]["shutter"]))
        self._dpc_var.set(state.get("dpc",        DEFAULTS["camera"]["dpc"]))
        self._awb_var.set(state.get("awb",        DEFAULTS["camera"]["awb"]))
        self._brightness_var.set(state.get("brightness", DEFAULTS["camera"]["brightness"]))
        self._contrast_var.set(state.get("contrast",   DEFAULTS["camera"]["contrast"]))
        self._saturation_var.set(state.get("saturation", DEFAULTS["camera"]["saturation"]))
        self._sharpness_var.set(state.get("sharpness",  DEFAULTS["camera"]["sharpness"]))

    def _reset_defaults(self) -> None:
        """Restore controls to the saved user defaults (or factory defaults)."""
        boot = self._settings.get_boot_camera_state()
        self._apply_camera_state(boot)
        self._set_status("Defaults restored", auto_clear=True)

    def _save_as_defaults(self) -> None:
        """Snapshot current state as the new default boot state."""
        self._settings.save_user_defaults(self._current_camera_state())
        self._set_status("Default boot state saved ✓", auto_clear=True)

    # ══════════════════════════════════════════════════════════════════════════
    # Profile management
    # ══════════════════════════════════════════════════════════════════════════

    def _load_profile(self) -> None:
        name = self._profile_var.get()
        state = self._profiles.get_camera_state(name)
        if state is None:
            messagebox.showwarning("Profile", f"Profile '{name}' not found.")
            return
        self._apply_camera_state(state)
        self._set_status(f"Profile '{name}' loaded", auto_clear=True)

    def _save_profile_as(self) -> None:
        name = simpledialog.askstring(
            "Save Profile", "Profile name:", parent=self.root,
            initialvalue=self._profile_var.get(),
        )
        if not name:
            return
        if name in BUILTIN_PROFILES:
            messagebox.showerror("Profile",
                                 f"Cannot overwrite built-in profile '{name}'.")
            return
        self._profiles.save(name, self._current_camera_state())
        self._profile_cb.config(values=self._profiles.list_names())
        self._profile_var.set(name)
        self._set_status(f"Profile '{name}' saved ✓", auto_clear=True)

    def _delete_profile(self) -> None:
        name = self._profile_var.get()
        if name in BUILTIN_PROFILES:
            messagebox.showwarning("Profile",
                                   f"'{name}' is a built-in profile and cannot be deleted.")
            return
        if not messagebox.askyesno("Delete Profile", f"Delete profile '{name}'?"):
            return
        if self._profiles.delete(name):
            self._profile_cb.config(values=self._profiles.list_names())
            self._profile_var.set("Default")
            self._set_status(f"Profile '{name}' deleted", auto_clear=True)

    # ══════════════════════════════════════════════════════════════════════════
    # Camera control logic
    # ══════════════════════════════════════════════════════════════════════════

    def _build_controls_dict(self) -> dict:
        """Translate current UI state → picamera2 controls dict."""
        controls: dict = {}

        iso_label     = self._iso_var.get()
        analogue_gain = ISO_OPTIONS.get(iso_label)

        shutter_label = self._shutter_var.get()
        exposure_us   = SHUTTER_OPTIONS.get(shutter_label)

        ae_enable = (analogue_gain is None and exposure_us is None)
        controls["AeEnable"] = ae_enable
        if not ae_enable:
            if analogue_gain is not None:
                controls["AnalogueGain"] = float(analogue_gain)
            if exposure_us is not None:
                controls["ExposureTime"] = int(exposure_us)

        controls["AwbEnable"]          = bool(self._awb_var.get())
        controls["Brightness"]         = float(self._brightness_var.get())
        controls["Contrast"]           = float(self._contrast_var.get())
        controls["Saturation"]         = float(self._saturation_var.get())
        controls["Sharpness"]          = float(self._sharpness_var.get())
        controls["NoiseReductionMode"] = DPC_OPTIONS.get(self._dpc_var.get(), 2)
        return controls

    def _push_controls(self) -> None:
        controls = self._build_controls_dict()
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

    def _schedule_preview(self) -> None:
        if self._running:
            self.root.after(PREVIEW_DELAY, self._update_preview)

    def _update_preview(self) -> None:
        if not self._running:
            return
        if not self._busy and self._countdown == 0:
            frame = self._camera.capture_preview_frame()
            if frame is not None:
                try:
                    photo = ImageTk.PhotoImage(frame)
                    self._vf_label.config(image=photo)
                    self._vf_label.image = photo
                except Exception:
                    pass
        self._schedule_preview()

    # ══════════════════════════════════════════════════════════════════════════
    # Capture + timer
    # ══════════════════════════════════════════════════════════════════════════

    def _on_capture(self) -> None:
        if self._busy:
            self._set_status("Busy — please wait…")
            return

        # Second press cancels a running countdown
        if self._countdown > 0:
            self._cancel_timer()
            return

        timer_label = self._timer_var.get()
        delay_s = TIMER_OPTIONS.get(timer_label)

        if delay_s == -1:   # Custom
            delay_s = self._settings.get("capture.timer_custom_s",
                                          DEFAULTS["capture"]["timer_custom_s"])

        if delay_s:
            self._start_countdown(int(delay_s))
        else:
            self._fire_capture()

    def _start_countdown(self, seconds: int) -> None:
        self._countdown = seconds
        self._countdown_label.place(relx=0.5, rely=0.5, anchor="center")
        self._countdown_var.set(str(seconds))
        self._set_status(f"Starting in {seconds}s — press Capture to cancel")
        self._tick_countdown()

    def _tick_countdown(self) -> None:
        if self._countdown <= 0:
            self._countdown_label.place_forget()
            self._countdown_var.set("")
            self._fire_capture()
            return
        self._countdown_var.set(str(self._countdown))
        self._countdown -= 1
        self._timer_id = self.root.after(1000, self._tick_countdown)

    def _cancel_timer(self) -> None:
        if self._timer_id is not None:
            self.root.after_cancel(self._timer_id)
            self._timer_id = None
        self._countdown = 0
        self._countdown_label.place_forget()
        self._countdown_var.set("")
        self._set_status("Timer cancelled", auto_clear=True)

    def _fire_capture(self) -> None:
        try:
            controls = self._build_controls_dict()
        except Exception:
            self._set_status("Control error")
            messagebox.showerror("Control Error", traceback.format_exc())
            return
        self._busy = True
        self._set_status("Capturing…")
        threading.Thread(
            target=self._do_capture, args=(controls,), daemon=True
        ).start()

    def _do_capture(self, controls: dict) -> None:
        try:
            time.sleep(PREVIEW_DELAY / 500.0)
            dng_path, metadata = self._camera.capture_dng(controls)
            _inject_exif_dng(dng_path, metadata, self._sensor_name)
            short_name = dng_path.name
            self.root.after(0, self._capture_done, str(dng_path), short_name, None)
        except Exception:
            tb = traceback.format_exc()
            logger.error("Capture failed:\n%s", tb)
            self.root.after(0, self._capture_done, None, None, tb)

    def _capture_done(self, full_path: str | None, name: str | None,
                      error: str | None) -> None:
        self._busy = False
        if error:
            self._set_status("Error — see console")
            messagebox.showerror("Capture Error", error)
        else:
            self._last_file_var.set(name or "—")
            logger.info("Saved: %s", full_path)
            self._flash_viewfinder()
            self._set_status("Saved ✓", auto_clear=True)

    # ── Viewfinder flash on successful capture ─────────────────────────────────

    def _flash_viewfinder(self, duration_ms: int = 500) -> None:
        self._vf_frame.config(highlightthickness=4,
                              highlightbackground=FLASH_GREEN)
        self.root.after(duration_ms, self._unflash_viewfinder)

    def _unflash_viewfinder(self) -> None:
        self._vf_frame.config(highlightthickness=0)

    # ── Status helpers ─────────────────────────────────────────────────────────

    def _set_status(self, msg: str, auto_clear: bool = False) -> None:
        if self._status_clear_id is not None:
            self.root.after_cancel(self._status_clear_id)
            self._status_clear_id = None
        self._status_var.set(msg)
        if auto_clear:
            self._status_clear_id = self.root.after(
                self.STATUS_CLEAR_MS, self._clear_status
            )

    def _clear_status(self) -> None:
        self._status_var.set("Ready")
        self._status_clear_id = None

    # ══════════════════════════════════════════════════════════════════════════
    # Close
    # ══════════════════════════════════════════════════════════════════════════

    def _on_close(self) -> None:
        self._running = False
        if self._timer_id is not None:
            self.root.after_cancel(self._timer_id)
        self.root.after(100, self._shutdown)

    def _shutdown(self) -> None:
        self._camera.stop()
        self.root.destroy()


# ═══════════════════════════════════════════════════════════════════════════════
# Entry point
# ═══════════════════════════════════════════════════════════════════════════════

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=f"PiCam V{VERSION}")
    parser.add_argument("--fullscreen", action="store_true",
                        help="Start in fullscreen mode")
    parser.add_argument("--geometry", default=f"{WINDOW_W}x{WINDOW_H}",
                        metavar="WxH",
                        help="Window geometry (default: 800x480)")
    parser.add_argument("--demo", action="store_true",
                        help="Force demo mode (no camera required)")
    return parser.parse_args()


def main() -> None:
    global PICAMERA2_AVAILABLE  # noqa: PLW0603

    args = _parse_args()

    if args.demo:
        PICAMERA2_AVAILABLE = False
        logger.info("Demo mode forced via --demo flag.")

    if not PICAMERA2_AVAILABLE:
        print("=" * 60)
        print("  picamera2 not installed — running in UI demo mode.")
        print("  Install with:  sudo apt install python3-picamera2")
        print("=" * 60)

    ensure_dcim_dir()
    logger.info("Photos will be saved to: %s", DCIM_DIR)

    settings = SettingsManager()
    profiles = ProfileManager()

    root = tk.Tk()

    if not args.fullscreen:
        try:
            w, h = (int(x) for x in args.geometry.lower().split("x"))
            root.geometry(f"{w}x{h}")
        except ValueError:
            logger.warning("Invalid --geometry '%s'; using default.", args.geometry)

    app = PiCamApp(root, settings, profiles, fullscreen=args.fullscreen)  # noqa: F841
    root.mainloop()


if __name__ == "__main__":
    main()
