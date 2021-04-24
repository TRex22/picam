# TODO List:
# - histograms
# - profiles
# - logging
# - Focus assist
# - Contrast Hist
# - Edge detect algo
# - Camera Intrinsics tool
# - Web control
# - Motion vectors
# - Improve tools
# - Cleanup test
# - Write actual tests
# - Histogram and analysis tools
# - RAW sensor capture: https://raspberrypi.stackexchange.com/questions/51191/how-can-i-stop-the-overlay-of-images-between-my-pi-camera-and-flir-camera
# - ISO
# - Shutter Speed
# - Resolution (FPS as label)
# - FPS option (wrt resolution)
# - Menus
# - Proper overlay
# - Audio?
# - sharpness
# - Contrast
# - brightness
# - saturation
# - ev compression
# - exposure mode
# - awb - auto white balance
# - image effect
# - colour effect
# - metering mode?
# - roi
# - dynamic range compression
# - image statistics
# - awb gains
# - sensor input mode??? / video
# - bitrate
# - video stabilisation
# - other video options
# - Add zoom to config
# - Lens shading control https://github.com/waveform80/picamera/pull/470

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

# 8MP pi camera v2.1
# width = 3280
# height = 2464

# 12MP Pi HQ camera
# width = 4056
# height = 3040

VERSION = "0.0.8"

import os
import shutil
import time
import glob
import json

from io import BytesIO
from picamerax import PiCamera

import RPi.GPIO as GPIO

from pydng.core import RPICAM2DNG
from pydng.core import RAW2DNG, DNGTags, Tag

import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Modules
import document_handler
import overlay_handler
import camera_handler

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
  "bayer": True,
  "fps": 60, # 10 fps max at full resolution
  "screen_fps": 60, #120, # 120 fps at 1012x760
  "screen_w": 1024, # 1012 # 320 screen res # Needs to be 4:3
  "screen_h": 768, #760 # 240 screen res # Needs to be 4:3
  "overlay_w": 320,
  "overlay_h": 240,
  "width": 4056, # Image width
  "height": 3040, # Image height
  "gpio": {
    "button_1": 27,
    "button_2": 23,
    "button_3": 22,
    "button_4": 17,
    "bouncetime": 300
  }
}

filetype = config["filetype"]
bpp = config["bpp"]
# format = config["format"]

fps = config["fps"]
screen_fps = config["screen_fps"]

dcim_images_path_raw = config["dcim_images_path_raw"]
dcim_original_images_path = config["dcim_original_images_path"]
dcim_hdr_images_path = config["dcim_hdr_images_path"]
dcim_videos_path = config["dcim_videos_path"]
dcim_tmp_path = config["dcim_tmp_path"]

colour_profile_path = config["colour_profile_path"]

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

################################################################################

document_handler.check_for_folders(config)

################################################################################
#                                  Callbacks                                   #
################################################################################

def button_callback_1(channel):
  print("Button 1 was pushed!")
  global camera
  global overlay
  global config

def button_callback_2(channel):
  print("Button 2: HDR")
  global camera
  global overlay
  global config

  screen_w = config["screen_w"]
  screen_h = config["screen_h"]

  width = config["width"]
  height = config["height"]

  dcim_path = config["dcim_path"]
  dcim_images_path_raw = config["dcim_images_path_raw"]
  dcim_original_images_path = config["dcim_original_images_path"]
  dcim_hdr_images_path = config["dcim_hdr_images_path"]
  dcim_videos_path = config["dcim_videos_path"]
  dcim_tmp_path = config["dcim_tmp_path"]

  overlay_handler.remove_overlay(camera, overlay)
  overlay = None

  camera.resolution = (width, height)

  start_time = time.time()
  available_exposure_compensations = [-25, -20, -15, -10, -5, 0, 5, 10, 15, 20, 25] # TODO

  # SEE: https://github.com/KEClaytor/pi-hdr-timelapse
  nimages = 5 #10 #2160
  exposure_min = 10
  exposure_max = 80 #90
  exp_step = 5

  exp_step = (exposure_max - exposure_min) / (nimages - 1.0)
  exposure_times = range(exposure_min, exposure_max + 1, int(exp_step))

  filenames = []

  existing_files = glob.glob(f'{dcim_hdr_images_path}/*.{format}')
  filecount = len(existing_files)
  frame_count = filecount

  original_brightness = camera.brightness
  # original_exposure_compensation = camera.exposure_compensation

  for step in exposure_times: # available_exposure_compensations:
    filename = f'{dcim_hdr_images_path}/{frame_count}_{step}_HDR.{format}'
    # filename = f'{dcim_tmp_path}/{frame_count}_{step}_HDR.{format}'

    camera.brightness = step
    # camera.exposure_compensation = step

    camera.capture(filename, format, bayer=True)

  camera.brightness = original_brightness
  # camera.exposure_compensation = original_exposure_compensation

  camera.resolution = (screen_w, screen_h)
  overlay = overlay_handler.add_overlay(camera, overlay, config)

  # for file in filenames:
  # shutil.copyfile(src, dst)

  print("--- %s seconds ---" % (time.time() - start_time))

def button_callback_3(channel):
  print("Button 3: Zoom")
  global camera
  global overlay
  global config

  current_zoom = camera.zoom
  if (current_zoom == (0.4, 0.4, 0.2, 0.2)):
    camera.zoom = (0.0, 0.0, 1.0, 1.0)
  else:
    camera.zoom = (0.4, 0.4, 0.2, 0.2)

  overlay = overlay_handler.add_overlay(camera, overlay, config)

def button_callback_4(channel):
  print("Button 4: Take shot")
  global camera
  global overlay
  global config

  camera_handler.take_single_shot(camera, overlay, config)

################################################################################
#                                  Main Loop                                   #
################################################################################

# Start PiCam
global camera

# Init Camera
camera = PiCamera()

global overlay
overlay = None

# Begin Camera start-up
camera.resolution = (screen_w, screen_h)
camera.framerate = screen_fps # fps

camera.start_preview()
overlay = overlay_handler.add_overlay(camera, overlay, config)

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

print(f'screen: ({screen_w}, {screen_h}), res: ({width}, {height})')
message = input("Press enter to quit\n\n") # Run until someone presses enter
camera.stop_preview()
GPIO.cleanup() # Clean up
overlay_handler.remove_overlay(camera, overlay)
