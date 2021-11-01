# https://docs.opencv.org/4.5.3/de/dbc/tutorial_py_fourier_transform.html
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

stacked_file_paths = [
  "/mnt/g/tmp/continious_shot/3/885_continuous.jpeg",
  "/mnt/g/tmp/continious_shot/3/886_continuous.jpeg",
  "/mnt/g/tmp/continious_shot/3/887_continuous.jpeg",
  "/mnt/g/tmp/continious_shot/3/888_continuous.jpeg",
  "/mnt/g/tmp/continious_shot/3/889_continuous.jpeg",
  "/mnt/g/tmp/continious_shot/3/890_continuous.jpeg",
  "/mnt/g/tmp/continious_shot/3/891_continuous.jpeg",
  "/mnt/g/tmp/continious_shot/3/892_continuous.jpeg",
  "/mnt/g/tmp/continious_shot/3/893_continuous.jpeg",
  "/mnt/g/tmp/continious_shot/3/894_continuous.jpeg"
]

# raw_file_path = '/mnt/g/tmp/812 Waxing Gibbons/raw/812.dng'

save_path = '/mnt/g/tmp/continious_shot/3/output/'
frames_save_path = f'{save_path}/frames'

print('Compute fft avg from a stack of images')
print(f'Save path: {save_path}')
# document_handler.detect_or_create_folder(frames_save_path)

output_filetype = '.png'

save_frames = True
sharpen = False
normalise = True
denoise = False

gamma = 2.4
bit_depth = 24

def to_fft(frame):
  f_ishift = np.fft.ifftshift(frame)
  return f_ishift

def from_fft(f_ishift):
  img_back = np.fft.ifft2(f_ishift)
  return img_back

def avg_tensor(tensor_stack):
  return np.mean(tensor_stack, axis=0)

def save(frame, name):
  cv2.imwrite(f'{save_path}{name}{output_filetype}', frame)

def save_stack(stack, name):
  index = 0
  for frame in stack:
    save(frame, f'{name}_{index}')
    index += 1

def generate_fft_stack(images):
  fft_stack = []

  for image in images:
    fft_stack.append(to_fft(image))

  return np.array(fft_stack)

def open_files(stacked_file_paths):
  list_of_images = []

  for raw_file_path in stacked_file_paths:
    # raw = rawpy.imread(raw_file_path)
    # im = raw.raw_image
    list_of_images.append(cv2.imread(raw_file_path))

  return np.array(list_of_images)

# def find_significance(fft_frames):
# stacked_file_paths

base_images = open_files(stacked_file_paths)
print(f'Number of files: {len(base_images)}')

print("Generate FFT Stack")
fft_stack = generate_fft_stack(base_images)
save_stack(fft_stack, 'fft')

print('Compute AVG Tensor')
avg_fft = avg_tensor(fft_stack)
save(avg_fft, f'avg_fft{output_filetype}')

print('Convert back to image')
avg_image = from_fft(avg_fft)
save(avg_fft, f'avg_fft_converted{output_filetype}')

print('Complete!')
