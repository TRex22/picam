# Notes:
# For fixing multi-press See: https://raspberrypi.stackexchange.com/questions/28955/unwanted-multiple-presses-when-using-gpio-button-press-detection

# Supported file types: https://picamera.readthedocs.io/en/release-1.10/api_camera.html#picamera.camera.PiCamera.capture
# 'jpeg' - Write a JPEG file
# 'png' - Write a PNG file
# 'gif' - Write a GIF file
# 'bmp' - Write a Windows bitmap file
# 'yuv' - Write the raw image data to a file in YUV420 format
# 'rgb' - Write the raw image data to a file in 24-bit RGB format
# 'rgba' - Write the raw image data to a file in 32-bit RGBA format
# 'bgr' - Write the raw image data to a file in 24-bit BGR format
# 'bgra' - Write the raw image data to a file in 32-bit BGRA format
# 'raw' - Deprecated option for raw captures; the format is taken from the deprecated raw_format attribute

# available_exposure_compensations = [-25, -20, -15, -10, -5, 0, 5, 10, 15, 20, 25]

# 8MP pi camera v2.1
# width = 3280
# height = 2464

# 12MP Pi HQ camera
# width = 4056
# height = 3040

VERSION = "0.0.14"

import time
import glob

from picamerax import PiCamera

import RPi.GPIO as GPIO

# Modules
import document_handler
import overlay_handler
import camera_handler
import menu_handler

################################################################################
##                                    Config                                  ##
################################################################################
global config
config = {
  "colour_profile_path": "/home/pi/Colour_Profiles/imx477/Raspberry Pi High Quality Camera Lumariver 2860k-5960k Neutral Look.json",
  "convert_raw": False,
  "dcim_path": 'home/pi/DCIM',
  "dcim_images_path_raw": '/home/pi/DCIM/images',
  "dcim_original_images_path": '/home/pi/DCIM/images/original',
  "dcim_hdr_images_path": '/home/pi/DCIM/images/hdr',
  "dcim_videos_path": '/home/pi/DCIM/videos',
  "dcim_tmp_path": '/home/pi/DCIM/tmp',
  "filetype": '.dng',
  "bpp": 12,
  "format": 'jpeg',
  "video_format": 'h264', # mjpeg, h264 TODO: Make into an option
  "bayer": True,
  "fps": 40, # 60 # 10 fps max at full resolution
  "screen_fps": 40, # 120 fps at 1012x760
  "screen_w": 1024, # 1012 # 320 screen res # Needs to be 4:3
  "screen_h": 768, #760 # 240 screen res # Needs to be 4:3
  "overlay_w": 320,
  "overlay_h": 240,
  "width": 4056, # Image width
  "height": 3040, # Image height
  "video_width": 4056,
  "video_height": 3040,
  "exposure_mode": 'auto',
  "default_exposure_mode": 'auto',
  "default_zoom": (0.0, 0.0, 1.0, 1.0),
  "max_zoom": (0.4, 0.4, 0.2, 0.2),
  "max_zoom_2": (0.8, 0.8, 0.4, 0.4),
  "available_exposure_modes": [
    "auto", # default has to be first in the list
    "off",
    "night",
    "nightpreview",
    "backlight",
    "spotlight",
    "sports",
    "snow",
    "beach",
    "verylong",
    "fixedfps",
    "antishake",
    "fireworks"
  ],
  "available_isos": [0, 100, 200, 320, 400, 500, 640, 800, 1600], # 0 is auto / 3200, 6400
  "iso": 0, # 800 / should shift to 0 - auto
  "default_iso": 0,
  "available_shutter_speeds": [0, 100, 500, 1000, 2000, 4000, 8000, 16667, 33333, 66667, 125000, 250000, 500000, 1000000, 2000000, 5000000, 10000000, 15000000, 20000000, 25000000, 30000000, 35000000, 40000000],
  "shutter_speed": 0,
  "default_shutter_speed": 0,
  "available_awb_mode": ['auto', 'off', 'sunlight', 'cloudy', 'shade', 'tungsten', 'fluorescent', 'incandescent', 'flash', 'horizon'],
  "awb_mode": 'auto',
  "default_awb_mode": 'auto', # "awb_gains": 0.0 - 8.0 (),
  "available_menu_items": ["auto", "exposure_mode", "iso", "shutter_speed", "awb_mode", "hdr", "video", "resolution", "encoding"],
  "menu_item": "auto",
  "default_menu_item": "auto",
  "hdr": False,
  "preview": True,
  "preview_mode": "built-in", # "built-in" "continuous_shot"
  "default_preview_mode": 'built-in',
  "video": False,
  "recording": False,
  "encoding": False, # TODO
  "gpio": {
    "button_1": 27,
    "button_2": 23,
    "button_3": 22,
    "button_4": 17,
    "bouncetime": 300
  }
}

# filetype = config["filetype"]
# bpp = config["bpp"]
# format = config["format"]

fps = config["fps"]
screen_fps = config["screen_fps"]

# dcim_images_path_raw = config["dcim_images_path_raw"]
# dcim_original_images_path = config["dcim_original_images_path"]
# dcim_hdr_images_path = config["dcim_hdr_images_path"]
# dcim_videos_path = config["dcim_videos_path"]
# dcim_tmp_path = config["dcim_tmp_path"]

# colour_profile_path = config["colour_profile_path"]

screen_w = config["screen_w"]
screen_h = config["screen_h"]

width = config["width"]
height = config["height"]

# GPIO Config
button_1 = config["gpio"]["button_1"]
button_2 = config["gpio"]["button_2"]
button_3 = config["gpio"]["button_3"]
button_4 = config["gpio"]["button_4"]

bouncetime = config["gpio"]["bouncetime"]

document_handler.check_for_folders(config)

################################################################################
#                                  Callbacks                                   #
################################################################################

def button_callback_1(channel):
  print("Button 1: Menu")
  global camera
  global overlay
  global config

  menu_handler.select_menu_item(camera, config)

def button_callback_2(channel):
  print("Button 2: Option")
  global camera
  global overlay
  global config

  menu_handler.select_option(camera, config)

def button_callback_3(channel):
  print("Button 3: Zoom")
  global camera
  global overlay
  global config

  camera_handler.zoom(camera, config)
  overlay = overlay_handler.add_overlay(camera, overlay, config)

def button_callback_4(channel):
  print("Button 4: Take shot")
  global camera
  global overlay
  global config

  overlay_handler.remove_overlay(camera, overlay, config)
  overlay = None

  if config["video"]:
    camera_handler.trigger_video(camera, config)
  else:
    if config["hdr"]:
      camera_handler.take_hdr_shot(camera, config)
    else:
      camera_handler.take_single_shot(camera, config)

  overlay = overlay_handler.add_overlay(camera, overlay, config)

################################################################################
#                                  Main Loop                                   #
################################################################################

# Start PiCam
global camera

# Init Camera
# camera = PiCamera(framerate=config["fps"])
camera = PiCamera(framerate=config["fps"])
camera_handler.auto_mode(camera, config)

global overlay
overlay = None

# Set button callbacks
# GPIO.setwarnings(False) # Ignore warning for now
GPIO.setwarnings(True)
# GPIO.setmode(GPIO.BOARD) # Use physical pin numbering
GPIO.setmode(GPIO.BCM)

GPIO.setup(button_1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(button_2, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(button_3, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(button_4, GPIO.IN, pull_up_down=GPIO.PUD_UP)

GPIO.add_event_detect(button_1, GPIO.RISING, callback=button_callback_1, bouncetime=bouncetime)
GPIO.add_event_detect(button_2, GPIO.RISING, callback=button_callback_2, bouncetime=bouncetime)
GPIO.add_event_detect(button_3, GPIO.RISING, callback=button_callback_3, bouncetime=bouncetime)
GPIO.add_event_detect(button_4, GPIO.RISING, callback=button_callback_4, bouncetime=bouncetime)

# Begin Camera start-up
camera.resolution = (screen_w, screen_h)
camera.framerate = screen_fps # fps

overlay = overlay_handler.add_overlay(camera, overlay, config)
overlay_handler.display_text(camera, '', config)
print(f'screen: ({screen_w}, {screen_h}), res: ({width}, {height})')

camera_handler.start_preview(camera, config) # Runs main camera loop
camera_handler.stop_preview(camera, config)

GPIO.cleanup() # Clean up
overlay_handler.remove_overlay(camera, overlay, config)
camera.close()
