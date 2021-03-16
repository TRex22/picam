import os
import shutil
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

# TODO: Convert to proper interface in src/

filetype = '.dng'
bpp = 12
format = 'jpeg'

fps = 60

dcim_images_path = '/home/pi/DCIM/images'
dcim_original_images_path = '/home/pi/DCIM/images/original'
dcim_hdr_images_path = '/home/pi/DCIM/images/hdr'
dcim_videos_path = '/home/pi/DCIM/videos'
dcim_tmp_path = '/home/pi/DCIM/tmp'

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

colour_profile_path = "/home/pi/Colour_Profiles/imx477/Raspberry Pi High Quality Camera Lumariver 2860k-5960k Neutral Look.json"

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

  screen_w = 320
  screen_h = 240

  # 12MP Pi HQ camera
  width = 4056
  height = 3040

# https://picamera.readthedocs.io/en/release-1.10/recipes1.html#overlaying-images-on-the-preview
def add_overlay(camera):
  overlay_w = 320
  overlay_h = 280

  # Create an array representing a 1280x720 image of
  # a cross through the center of the display. The shape of
  # the array must be of the form (height, width, color)
  a = np.zeros((overlay_h, overlay_w, 4), dtype=np.uint8)
  half_height = int(overlay_h/2)
  half_width = int(overlay_w/2)

  a[half_height, :, :] = 0xff
  a[:, half_width, :] = 0xff

  # Create image bytes
  # https://stackoverflow.com/questions/54891829/typeerror-memoryview-a-bytes-like-object-is-required-not-jpegimagefile
  # buf = BytesIO()
  img = Image.fromarray(a, 'RGBA')

  # img.save(buf, 'bmp')
  # buf.seek(0)
  image_bytes = img.tobytes()
  # image_bytes = np.getbuffer(a)
  # buf.close()

  # Broken docs ...
  # o = camera.add_overlay(a.tobytes(), layer=3, alpha=64)

  # Image.new("RGB", (320, 240))
  # o = camera.add_overlay(Image.fromarray(a, 'RGB'), size=(320,240), layer=3, alpha=64)
  o = camera.add_overlay(image_bytes, size=img.size, layer=3, alpha=64, format="rgba")
  camera.annotate_text = 'Photo mode' # TODO: Cleanup
  # camera.remove_overlay(o)
  return o

def remove_overlay(camera, overlay):
  camera.remove_overlay(overlay)
  camera.annotate_text = None

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
  global overlay
  # print(f"recording_state: {recording_state}")
  # recording_state = True

def button_callback_2(channel):
  print("Button 2: HDR")
  global overlay

  # TODO: Need to figure out high-speed capture (~11FPS)

  screen_w = 340
  screen_h = 240

  # 12MP Pi HQ camera
  width = 4056
  height = 3040

  remove_overlay(camera, overlay)
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

  existing_files = glob.glob(f'{dcim_hdr_images_path}/*{filetype}')
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
  overlay = add_overlay(camera)

  # for file in filenames:
  # shutil.copyfile(src, dst)

  print("--- %s seconds ---" % (time.time() - start_time))

def button_callback_3(channel):
  print("Button 3: Zoom")
  global overlay

  current_zoom = camera.zoom
  if (current_zoom == (0.4, 0.4, 0.2, 0.2)):
    camera.zoom = (0.0, 0.0, 1.0, 1.0)
  else:
    camera.zoom = (0.4, 0.4, 0.2, 0.2)

  overlay = add_overlay(camera)

def button_callback_4(channel):
  print("Button 4: Take shot")
  global overlay

  screen_w = 340
  screen_h = 240

  # 12MP Pi HQ camera
  width = 4056
  height = 3040

  # camera.stop_preview()
  remove_overlay(camera, overlay)

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
  overlay = overlay = add_overlay(camera)
  # camera.start_preview()

button_1 = 27
button_2 = 23
button_3 = 22
button_4 = 17

bouncetime = 300

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

camera.resolution = (screen_w, screen_h)
camera.start_preview()

# camera.framerate = fps
global overlay
overlay = add_overlay(camera)

message = input("Press enter to quit\n\n") # Run until someone presses enter
camera.stop_preview()
GPIO.cleanup() # Clean up
remove_overlay(camera, overlay)

# For fixing multi-press See: https://raspberrypi.stackexchange.com/questions/28955/unwanted-multiple-presses-when-using-gpio-button-press-detection