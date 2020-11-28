import time
import glob

from picamera import PiCamera

from io import BytesIO
import numpy as np
from pydng.core import RPICAM2DNG

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
w = 4056
h = 3040

# format = 'bgr'
# format = 'yuv'
format = 'jpeg'

stream = BytesIO()

camera.resolution = (w, h)

filename = f'{dcim_images_path}/{frame_count}{filetype}'
print(filename)

# camera.start_preview()
# time.sleep(10)
# camera.capture(filename, format=format)
camera.capture(stream, format, bayer=True)

start_time = time.time()

d = RPICAM2DNG()
output = d.convert(stream)

with open(filename, 'wb') as f:
  f.write(output)

print("--- %s seconds ---" % (time.time() - start_time))

# camera.stop_preview()
