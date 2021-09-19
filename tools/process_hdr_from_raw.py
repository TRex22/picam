import sys
sys.path.insert(1, '../src/')
sys.path.insert(1, 'src/')

import os
import glob
import math

import cv2
import numpy as np

import rawpy
from PIL import Image

# Modules
import document_handler

# TODO:
# Blur Combine
# Contrast equalisation / compensation
# Progress bar
# EXIF Copy

# raw_file_path = 'G:\\tmp\\725 Half Moon\\raw\\725.dng'
# raw_file_path = '/mnt/g/tmp/725 Half Moon/raw/725.dng'
# raw_file_path = '/mnt/g/tmp/749 Waning Gibbons/raw/749.dng'
# raw_file_path = '/mnt/g/tmp/761 Waning Gibbons/raw/761.dng'
# raw_file_path = '/mnt/g/tmp/773 Waxing Gibbons/raw/773.dng'
raw_file_path = '/mnt/g/tmp/784 Waxing Gibbons/raw/784.dng'
# save_path = '/mnt/g/tmp/725 Half Moon/raw/output'
# save_path = '/mnt/g/tmp/749 Waning Gibbons/raw/'
# save_path = '/mnt/g/tmp/761 Waning Gibbons/raw/'
# save_path = '/mnt/g/tmp/773 Waxing Gibbons/raw/'
save_path = '/mnt/g/tmp/784 Waxing Gibbons/raw/'
frames_save_path = f'{save_path}/frames'

print(save_path)
document_handler.detect_or_create_folder(frames_save_path)

output_filetype = '.jpg'

save_frames = True
sharpen = False
normalise = True
denoise = False

# Requires Darktable because Im not recreating their filters
# Also you need to save frames first
scotopic_vision = False # Low-light compensation

gamma = 2.4 #2.2
bit_depth = 24 #12

nimages = 6# 8 #5 #10 # 3 #10 #2160 # TODO: Automate

exposure_min = 20 #5 # 20 # 25
exposure_max = 60 #20 #33 #32 #40 # 60

exposure_shift_min = 0
exposure_shift_max = 8

# exp_step = nimages
exp_step = 5
exp_shift_step = 1

# SEE: https://github.com/KEClaytor/pi-hdr-timelapse
def compute_exposure_times(nimages, exposure_min, exposure_max, exp_step):
  exp_step = (exposure_max - exposure_min) / (nimages - 1.0)
  exposure_times = range(exposure_min, exposure_max, int(exp_step))

  # https://docs.opencv.org/3.4/d2/df0/tutorial_py_hdr.html
  arr_exposure_times = np.array(exposure_times, dtype=np.float32)
  return np.append(arr_exposure_times, float(exposure_max))

exposure_times = compute_exposure_times(nimages, exposure_min, exposure_max, exp_step)
print(exposure_times)

exposure_shift_times = compute_exposure_times(nimages, exposure_shift_min, exposure_shift_max, exp_shift_step)
print(exposure_shift_times)

# Open DNG
raw = rawpy.imread(raw_file_path)

def usharp_filer(frame):
  new_frame = cv2.GaussianBlur(frame, (0, 0), 3)
  return cv2.addWeighted(new_frame, 1.5, frame, -0.5, 0, frame)

def kernel_sharpen(frame):
  kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
  return cv2.filter2D(frame, -1, kernel)

# https://stackoverflow.com/questions/54272236/adjust-exposure-of-raw-image-based-on-ev-value
def generate_exposure_from_raw(raw, exposure):
  # black_level = raw.black_level_per_channel[0] # assume they're all the same
  black_level = (raw.black_level_per_channel[0] + raw.black_level_per_channel[1] + raw.black_level_per_channel[2]) / 3

  im = raw.raw_image
  im = np.maximum(im, black_level) - black_level # changed order of computation
  im *= 2**int(exposure)
  im = im + black_level
  im = np.minimum(im, 2**12 - 1)

  raw.raw_image[:,:] = im

  im = raw.postprocess(use_camera_wb=True, no_auto_bright=True)

  img = Image.fromarray(im, 'RGB')
  # img.show()

  return np.array(img) # convert for cv2

img_list = []

for exposure in exposure_shift_times:
  # shifted_exposure = math.floor((exposure - exposure_min)/exp_step)
  frame = generate_exposure_from_raw(raw, exposure/exp_step)

  if normalise == True:
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    lhist = cv2.equalizeHist(l)
    ahist = cv2.equalizeHist(a)
    bhist = cv2.equalizeHist(b)

    lab_img = cv2.merge((l,a,b))

    frame = cv2.cvtColor(lab_img, cv2.COLOR_LAB2BGR)

  if denoise == True:
    frame = cv2.fastNlMeansDenoisingColored(frame, None, 5, 5, 7, 21)

  if sharpen == True:
    # frame = usharp_filer(frame)
    frame = kernel_sharpen(frame)

  if save_frames == True:
    save_frame_path = f'{frames_save_path}/{exposure}{output_filetype}'
    cv2.imwrite(save_frame_path, frame)

    # https://docs.darktable.org/usermanual/3.6/module-reference/processing-modules/lowlight-vision/
    # https://en.wikipedia.org/wiki/Scotopic_vision
    if scotopic_vision == True:
      # --style chromatic-aberrations
      # --style lowlight-vision
      os.system(f'darktable-cli {save_frame_path} l_{save_frame_path} --style lowlight-vision')

  img_list.append(frame)

# HDR Part
# files = glob.glob(f'{dcim_hdr_images_path}/*{filetype}')
# print(files)
# filenames = files # TODO: automate
# img_list = [cv2.imread(filename) for filename in filenames]

# Merge exposures to HDR image
# merge_debevec = cv2.createMergeDebevec()
# hdr_debevec = merge_debevec.process(img_list, times=exposure_times.copy())
# merge_robertson = cv2.createMergeRobertson()
# hdr_robertson = merge_robertson.process(img_list, times=exposure_times.copy())

# Tonemap HDR image
# tonemap1 = cv2.createTonemap(gamma=gamma)
# res_debevec = tonemap1.process(hdr_debevec.copy())

# res_robertson = merge_robertson(hdr_robertson.copy())

# Exposure fusion using Mertens
merge_mertens = cv2.createMergeMertens()
res_mertens = merge_mertens.process(img_list)

# Convert datatype to 8-bit and save
# res_debevec_8bit = np.clip(res_debevec*255, 0, 255).astype('uint8')
# res_robertson_8bit = np.clip(hdr_robertson*255, 0, 255).astype('uint8')
res_mertens_8bit = np.clip(res_mertens*255, 0, 255).astype('uint8')

# cv2.imwrite(f'{save_path}/ldr_debevec_HDR_{output_filetype}', res_debevec_8bit)
# cv2.imwrite(f'{save_path}/ldr_robertson_HDR_{output_filetype}', res_robertson_8bit)
cv2.imwrite(f'{save_path}/fusion_mertens_{output_filetype}', res_mertens_8bit)

# Estimate camera response function (CRF)
# cal_debevec = cv2.createCalibrateDebevec()
# crf_debevec = cal_debevec.process(img_list, times=exposure_times)
# hdr_debevec = merge_debevec.process(img_list, times=exposure_times.copy(), response=crf_debevec.copy())
# cal_robertson = cv2.createCalibrateRobertson()
# crf_robertson = cal_robertson.process(img_list, times=exposure_times)
# hdr_robertson = merge_robertson.process(img_list, times=exposure_times.copy(), response=crf_robertson.copy())
