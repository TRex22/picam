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

filetype = '.jpg'

dcim_hdr_images_path = '/home/pi/DCIM/hdr_images'
dcim_images_path = '/home/pi/DCIM/images'
dcim_videos_path = '/home/pi/DCIM/videos'

existing_files = glob.glob(f'{dcim_hdr_images_path}/*{filetype}')
filecount = len(existing_files)
frame_count = filecount + 1

camera = PiCamera()
# camera.resolution = (w, h)
# camera.brightness = step

w = 3280
h = 2464

camera.resolution = (w, h)

# SEE: https://github.com/KEClaytor/pi-hdr-timelapse
nimages = 10 #2160
exposure_min = 10
exposure_max = 90
exp_step = 5

exp_step = (exposure_max - exposure_min) / (nimages - 1.0)
exposures = range(exposure_min, exposure_max + 1, int(exp_step))

filenames = []
for step in exposures:
  # Set filename based on exposure
  filename = f'{dcim_hdr_images_path}/{frame_count}_{step}_HDR_{filetype}' # 'e%d.jpg' % (step)
  print(filename)

  filenames.append(filename)
  # Set camera properties and capture
  camera.brightness = step
  camera.capture(filename)

