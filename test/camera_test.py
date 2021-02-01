import os
import time
import glob
import json

from io import BytesIO
from picamera import PiCamera
# from gpiozero import Button
import RPi.GPIO as GPIO

from pydng.core import RPICAM2DNG
from pydng.core import RAW2DNG, DNGTags, Tag

import numpy as np
from PIL import Image, ImageDraw, ImageFont

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

filetype = '.dng'
bpp = 12
format = 'jpeg'

fps = 60

dcim_images_path = '/home/pi/DCIM/images'
dcim_original_images_path = '/home/pi/DCIM/images/original'
dcim_hdr_images_path = '/home/pi/DCIM/images/hdr'
dcim_videos_path = '/home/pi/DCIM/videos'

try:
  os.mkdir(dcim_images_path)
except OSError as error:
  print(error)

try:
  os.mkdir(dcim_original_images_path)
except OSError as error:
  print(error)

try:
  os.mkdir(dcim_hdr_images_path)
except OSError as error:
  print(error)

try:
  os.mkdir(dcim_videos_path)
except OSError as error:
  print(error)

colour_profile_path = "/home/pi/DCIM/Colour_Profiles/imx477/Raspberry Pi High Quality Camera Lumariver 2860k-5960k Neutral Look.json"

raw_colour_profile = None
with open(colour_profile_path, "r") as file_stream:
  json_colour_profile = json.load(file_stream)

camera = PiCamera()

# 8MP pi camera v2.1
# w = 3280
# h = 2464

screen_w = 340
screen_h = 240

# 12MP Pi HQ camera
width = 4056
height = 3040

recording_state = False

default_zoom = camera.zoom

def defaults():
  filetype = '.dng'
  bpp = 12
  format = 'jpeg'

  fps = 60

  screen_w = 340
  screen_h = 240

  # 12MP Pi HQ camera
  width = 4056
  height = 3040

# https://picamera.readthedocs.io/en/release-1.10/recipes1.html#overlaying-images-on-the-preview
def add_crosshair():
  # Create an array representing a 1280x720 image of
  # a cross through the center of the display. The shape of
  # the array must be of the form (height, width, color)
  a = np.zeros((720, 1280, 3), dtype=np.uint8)
  a[360, :, :] = 0xff
  a[:, 640, :] = 0xff

  # Broken docs ...
  # o = camera.add_overlay(a.tobytes(), layer=3, alpha=64)

  # Image.new("RGB", (320, 240))
  o = camera.add_overlay(Image.fromarray(a, 'RGB').tostring(), size=(320,240), layer=3, alpha=64)

  # camera.remove_overlay(o)

# Preview
def preview(camera, zoom=False):
  if zoom == True:
    camera.zoom = (0.4, 0.4, 0.2, 0.2)

  camera.start_preview()
  time.sleep(10)
  # camera.capture(filename)
  camera.stop_preview()

def button_callback_1(channel):
  print("Button 1 was pushed!")
  # print(f"recording_state: {recording_state}")
  # recording_state = True

def button_callback_2(channel):
  print("Button 2: HDR")

  screen_w = 340
  screen_h = 240

  # 12MP Pi HQ camera
  width = 4056
  height = 3040

  camera.resolution = (width, height)

  start_time = time.time()
  available_exposure_compensations = [-25, -20, -15, -10, -5, 0, 5, 10, 15, 20, 25] # TODO
  # SEE: https://github.com/KEClaytor/pi-hdr-timelapse
  nimages = 10 #2160
  exposure_min = 10
  exposure_max = 90
  exp_step = 5

  exp_step = (exposure_max - exposure_min) / (nimages - 1.0)
  exposure_times = range(exposure_min, exposure_max + 1, int(exp_step))

  filenames = []

  existing_files = glob.glob(f'{dcim_hdr_images_path}/*{filetype}')
  filecount = len(existing_files)
  frame_count = filecount

  original_exposure_compensation = camera.exposure_compensation

  for step in available_exposure_compensations: #exposure_times:
    filename = f'{dcim_hdr_images_path}/{frame_count}_{step}_HDR.{format}'
    # camera.brightness = step
    camera.exposure_compensation = step
    camera.capture(filename, format, bayer=True)

  camera.exposure_compensation = original_exposure_compensation
  camera.resolution = (screen_w, screen_h)
  print("--- %s seconds ---" % (time.time() - start_time))

def button_callback_3(channel):
  print("Button 3: Zoom")

  current_zoom = camera.zoom
  if (current_zoom == (0.4, 0.4, 0.2, 0.2)):
    camera.zoom = (0.0, 0.0, 1.0, 1.0)
  else:
    camera.zoom = (0.4, 0.4, 0.2, 0.2)

def button_callback_4(channel):
  print("Button 4: Take shot")

  screen_w = 340
  screen_h = 240

  # 12MP Pi HQ camera
  width = 4056
  height = 3040

  # camera.stop_preview()

  existing_files = glob.glob(f'{dcim_images_path}/*{filetype}')
  filecount = len(existing_files)
  frame_count = filecount

  filename = f'{dcim_images_path}/{frame_count}{filetype}'
  print(filename)

  original_filename = f'{dcim_original_images_path}/{frame_count}.{format}'

  stream = BytesIO()

  camera.resolution = (width, height)
  start_time = time.time()

  camera.capture(stream, format, bayer=True)

  with open(original_filename, 'wb') as f:
    f.write(stream.getbuffer())

  # camera.stop_preview()

  output = RPICAM2DNG().convert(stream, json_camera_profile=json_colour_profile)

  with open(filename, 'wb') as f:
    f.write(output)

  print("--- %s seconds ---" % (time.time() - start_time))

  camera.resolution = (screen_w, screen_h)
  # camera.start_preview()

button_1 = 27
button_2 = 23
button_3 = 22
button_4 = 17

# GPIO.setwarnings(False) # Ignore warning for now
GPIO.setwarnings(True)
# GPIO.setmode(GPIO.BOARD) # Use physical pin numbering
GPIO.setmode(GPIO.BCM)

GPIO.setup(button_1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(button_2, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(button_3, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(button_4, GPIO.IN, pull_up_down=GPIO.PUD_UP)

GPIO.add_event_detect(button_1, GPIO.RISING, callback=button_callback_1)
GPIO.add_event_detect(button_2, GPIO.RISING, callback=button_callback_2)
GPIO.add_event_detect(button_3, GPIO.RISING, callback=button_callback_3)
GPIO.add_event_detect(button_4, GPIO.RISING, callback=button_callback_4)

camera.resolution = (screen_w, screen_h)
camera.start_preview()

# camera.framerate = fps
# add_crosshair()

message = input("Press enter to quit\n\n") # Run until someone presses enter
camera.stop_preview()
GPIO.cleanup() # Clean up
