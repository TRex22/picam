import os
import time
import glob

import cv2
import numpy as np

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

hdr_dir = f'{dcim_hdr_images_path}/{filecount}'
os.mkdir(hdr_dir)

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
exposure_times = range(exposure_min, exposure_max + 1, int(exp_step))

# Must be jpg for exif data
reference_filename = f'{hdr_dir}/{frame_count}_REFERENCE.jpg'
print(reference_filename)
camera.capture(reference_filename)

filenames = []
for step in exposure_times:
  # Set filename based on exposure
  filename = f'{hdr_dir}/{frame_count}_{step}_HDR_{filetype}' # 'e%d.jpg' % (step)
  print(filename)

  filenames.append(filename)
  # Set camera properties and capture
  camera.brightness = step
  camera.capture(filename)

# https://docs.opencv.org/3.4/d2/df0/tutorial_py_hdr.html
exposure_times = np.array(exposure_times, dtype=np.float32)
img_list = [cv2.imread(filename) for filename in filenames]

# Merge exposures to HDR image
merge_debevec = cv2.createMergeDebevec()
hdr_debevec = merge_debevec.process(img_list, times=exposure_times.copy())
merge_robertson = cv2.createMergeRobertson()
hdr_robertson = merge_robertson.process(img_list, times=exposure_times.copy())

# Tonemap HDR image
tonemap1 = cv2.createTonemap(gamma=2.2)
res_debevec = tonemap1.process(hdr_debevec.copy())

# Exposure fusion using Mertens
merge_mertens = cv2.createMergeMertens()
res_mertens = merge_mertens.process(img_list)

# Convert datatype to 8-bit and save
res_debevec_8bit = np.clip(res_debevec*255, 0, 255).astype('uint8')
res_robertson_8bit = np.clip(res_robertson*255, 0, 255).astype('uint8')
res_mertens_8bit = np.clip(res_mertens*255, 0, 255).astype('uint8')

cv2.imwrite(f'{dcim_hdr_images_path}/{frame_count}_ldr_debevec_HDR_{filetype}', res_debevec_8bit)
cv2.imwrite(f'{dcim_hdr_images_path}/{frame_count}_ldr_robertson_HDR_{filetype}', res_robertson_8bit)
cv2.imwrite(f'{dcim_hdr_images_path}/{frame_count}_fusion_mertens_{filetype}', res_mertens_8bit)

# Estimate camera response function (CRF)
# cal_debevec = cv2.createCalibrateDebevec()
# crf_debevec = cal_debevec.process(img_list, times=exposure_times)
# hdr_debevec = merge_debevec.process(img_list, times=exposure_times.copy(), response=crf_debevec.copy())
# cal_robertson = cv2.createCalibrateRobertson()
# crf_robertson = cal_robertson.process(img_list, times=exposure_times)
# hdr_robertson = merge_robertson.process(img_list, times=exposure_times.copy(), response=crf_robertson.copy())

