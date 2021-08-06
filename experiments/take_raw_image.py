import os
from io import BytesIO
import time
import glob
import json
import struct

import numpy as np

from picamerax import PiCamera

from pydng.core import RPICAM2DNG
from pydng.core import RAW2DNG, DNGTags, Tag

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
dcim_images_path = '/home/pi/DCIM/images'
dcim_videos_path = '/home/pi/DCIM/videos'

try:
  os.mkdir(dcim_images_path)
except OSError as error:
  print(error)

try:
  os.mkdir(dcim_videos_path)
except OSError as error:
  print(error)

# Used sample from: https://github.com/schoolpost/PyDNG/blob/master/examples/raw2dng.py
existing_files = glob.glob(f'{dcim_images_path}/*{filetype}')
filecount = len(existing_files)
frame_count = filecount

camera = PiCamera()
# camera.resolution = (w, h)
# camera.brightness = step

# 8MP pi camera v2.1
# w = 3280
# h = 2464

# 12MP Pi HQ camera
# RAW image specs
width = 4056
height = 3040
bpp = 12

# format = 'bgr'
# format = 'yuv'
format = 'jpeg'

# Calibrated colour matrix
# colour_profile_path = "/home/pi/DCIM/Colour_Profiles/imx477/PyDNG_profile.dcp"
# colour_profile_path = "/home/pi/DCIM/Colour_Profiles/imx477/Raspberry Pi High Quality Camera Lumariver 2860k-5960k Skin+Sky Look.dcp"
# colour_profile_path = "/home/pi/DCIM/Colour_Profiles/imx477/Raspberry Pi High Quality Camera Lumariver 2860k-5960k Neutral Look.dcp"
# colour_profile_path = "/home/pi/DCIM/Colour_Profiles/imx477/neutral.dcp"
# colour_profile_path = "/home/pi/dcp"

# python -m clairmeta.cli probe -type dcp "/home/pi/DCIM/Colour_Profiles/imx477/neutral.dcp" -format json > dcp.json
# python -m clairmeta.cli probe -type dcp "/home/pi/dcp" -format json > dcp.json

# JSON conversions
# colour_profile_path = "/home/pi/DCIM/Colour_Profiles/imx477/PyDNG_profile.json"
# colour_profile_path = "/home/pi/DCIM/Colour_Profiles/imx477/Raspberry Pi High Quality Camera Lumariver 2860k-5960k Skin+Sky Look.json"
colour_profile_path = "/home/pi/DCIM/Colour_Profiles/imx477/Raspberry Pi High Quality Camera Lumariver 2860k-5960k Neutral Look.json"
# colour_profile_path = "/home/pi/DCIM/Colour_Profiles/imx477/neutral.json"

raw_colour_profile = None
with open(colour_profile_path, "r") as file_stream:
  json_colour_profile = json.load(file_stream)

# TODO:
# t.set(Tag.FocalLength, )
# t.set(Tag.35mmFocalLength, 2)
# F-stop
# Exposure bias

stream = BytesIO()

camera.resolution = (width, height)

filename = f'{dcim_images_path}/{frame_count}{filetype}'
print(filename)

start_time = time.time()

camera.capture(stream, format, bayer=True)

output = RPICAM2DNG().convert(stream, json_camera_profile=json_colour_profile)

with open(filename, 'wb') as f:
  f.write(output)

print("--- %s seconds ---" % (time.time() - start_time))

# camera.stop_preview()
