import sys
sys.path.insert(1, '../src/')
sys.path.insert(1, 'src/')

import glob

import cv2
import numpy as np

# Modules
import document_handler

# TODO: Need to figure out highspeed capture (~11FPS)
# TODO: Handle commandline parameters
# For now look at a static folder
dcim_hdr_images_path = '/home/pi/DCIM/images/hdr'
# dcim_hdr_images_path = '/mnt/i/tmp/hdr'
dcim_hdr_images_path = '/mnt/g/tmp/hdr'

filetype = '.png'

document_handler.detect_or_create_folder(dcim_hdr_images_path)

# SEE: https://github.com/KEClaytor/pi-hdr-timelapse
def compute_exposure_times(nimages):
  exposure_min = 10
  exposure_max = 90
  exp_step = 5

  exp_step = (exposure_max - exposure_min) / (nimages - 1.0)
  exposure_times = range(exposure_min, exposure_max + 1, int(exp_step))

  return exposure_times

files = glob.glob(f'{dcim_hdr_images_path}/*.*')
print(files)

filenames = files # TODO: automate
nimages = 9 #3 #10 #2160 # TODO: Automate
frame_count = 0 # TODO: automate

exposure_times = compute_exposure_times(nimages)

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

# res_robertson = merge_robertson(hdr_robertson.copy())

# Exposure fusion using Mertens
merge_mertens = cv2.createMergeMertens()
res_mertens = merge_mertens.process(img_list)

# Convert datatype to 8-bit and save
res_debevec_8bit = np.clip(res_debevec*255, 0, 255).astype('uint8')
res_robertson_8bit = np.clip(hdr_robertson*255, 0, 255).astype('uint8')
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
