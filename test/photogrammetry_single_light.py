import sys
import os
import time
import glob

from picamera import PiCamera

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

if len(sys.argv) > 1:
  sub_folder = sys.argv[1]
else:
  sub_folder = ""

filetype = '.jpg'

dcim_images_path = f'/home/pi/DCIM/images_photogrammetry/'

try:
  os.mkdir(dcim_images_path)
except OSError as error:
  print(error)

dcim_images_path = f'/home/pi/DCIM/images_photogrammetry/{sub_folder}'

try:
  os.mkdir(dcim_images_path)
except OSError as error:
  print(error)

existing_files = glob.glob(f'{dcim_images_path}/*{filetype}')
filecount = len(existing_files)
frame_count = filecount

camera = PiCamera()
# camera.resolution = (w, h)
# camera.brightness = step

w = 3280
h = 2464

camera.resolution = (w, h)

camera.iso = 1600
camera.shutter_speed = 1000000000
camera.exposure_compensation = 10
camera.exposure_mode = 'off' #'auto'
camera.image_denoise = True
camera.image_effect = 'none'
camera.drc_strength = 'off'
camera.contrast = 10
camera.brightness = 50
camera.hflip = False
camera.vflip = False
camera.rotation = 270

filename = f'{dcim_images_path}/{frame_count}{filetype}'
print(filename)

camera.capture(filename)

available_exposure_compensations = [-25, -20, -15, -10, -5, 0, 5, 10, 15, 20, 25]

for exposure_compensation in available_exposure_compensations:
  try:
    os.mkdir(f'{dcim_images_path}/exposure_compensation_{frame_count}')
  except OSError as error:
    print(error)

  filename = f'{dcim_images_path}/exposure_compensation_{frame_count}/{exposure_compensation}{filetype}'
  print(filename)

  camera.exposure_compensation = exposure_compensation
  camera.capture(filename, format=format)

nimages = 10 #2160
exposure_min = 10
exposure_max = 90
exp_step = 5

exp_step = (exposure_max - exposure_min) / (nimages - 1.0)
brightness_steps = range(exposure_min, exposure_max + 1, int(exp_step))

for brightness_step in brightness_steps:
  try:
    os.mkdir(f'{dcim_images_path}/brightness_compensation_{frame_count}')
  except OSError as error:
    print(error)

  filename = f'{dcim_images_path}/brightness_compensation_{frame_count}/{exposure_compensation}{filetype}'
  print(filename)

  camera.exposure_compensation = exposure_compensation
  camera.capture(filename, format=format)

print('Much Success!')