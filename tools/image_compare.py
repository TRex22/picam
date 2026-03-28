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

raw_file_path = '/mnt/g/tmp/812 Waxing Gibbons/raw/812.dng'
save_path = '/mnt/g/tmp/812 Waxing Gibbons/raw/'
frames_save_path = f'{save_path}/frames'

print(save_path)
document_handler.detect_or_create_folder(frames_save_path)

output_filetype = '.jpg'

save_frames = True
sharpen = False
normalise = True
denoise = False

gamma = 2.4
bit_depth = 24
