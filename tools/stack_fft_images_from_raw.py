# https://docs.opencv.org/4.5.3/de/dbc/tutorial_py_fourier_transform.html
import sys
sys.path.insert(1, '../src/')
sys.path.insert(1, 'src/')

import os
import glob
import math

import cv2
import numpy as np
from scipy import fftpack
import matplotlib.pyplot as plt

import platform
environment = platform.system().lower()
print(f'Environment detected: {environment}')

import rawpy
from PIL import Image

# Modules
import document_handler

# TODO:
# Blur Combine
# Contrast equalisation / compensation
# Progress bar
# EXIF Copy
# Select Base Image

if (environment == 'windows'):
  stacked_file_paths = [
    "G:\\tmp\\continious_shot\\3\\885_continuous.jpeg",
    "G:\\tmp\\continious_shot\\3\\886_continuous.jpeg",
    "G:\\tmp\\continious_shot\\3\\887_continuous.jpeg",
    "G:\\tmp\\continious_shot\\3\\888_continuous.jpeg",
    "G:\\tmp\\continious_shot\\3\\889_continuous.jpeg",
    "G:\\tmp\\continious_shot\\3\\890_continuous.jpeg",
    "G:\\tmp\\continious_shot\\3\\891_continuous.jpeg",
    "G:\\tmp\\continious_shot\\3\\892_continuous.jpeg",
    "G:\\tmp\\continious_shot\\3\\893_continuous.jpeg",
    "G:\\tmp\\continious_shot\\3\\894_continuous.jpeg"
  ]

  # raw_file_path = '/mnt/g/tmp/812 Waxing Gibbons/raw/812.dng'

  save_path = 'G:\\tmp\\continious_shot\\3\\output\\'
  frames_save_path = f'{save_path}\\frames'
else:
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

# https://stackoverflow.com/questions/38476359/fft-on-image-with-python
# http://scipy-lectures.org/intro/scipy/auto_examples/solutions/plot_fft_image_denoise.html
def filter(fft, keep_fraction = 0.1):
  im_fft2 = fft.copy()

  # Set r and c to be the number of rows and columns of the array.
  r, c = im_fft2.shape

  # Set to zero all rows with indices between r*keep_fraction and
  # r*(1-keep_fraction):
  im_fft2[int(r*keep_fraction):int(r*(1-keep_fraction))] = 0

  # Similarly with the columns:
  im_fft2[:, int(c*keep_fraction):int(c*(1-keep_fraction))] = 0

  return im_fft2

def fft(channel):
  # fft = fftpack.fft2(channel)
  # fft = np.fft.fft2(channel)
  fft = np.fft.fftn(channel)
  # fft = np.fft.fftshift(channel)
  # fft *= 255.0 / fft.max()  # proper scaling into 0..255 range
  # return np.absolute(fft)
  return fft

def ifft(channel):
  # ifft = np.fft.ifftshift(channel)
  # ifftc *= 255.0 / ifft.max()
  # ifft = np.fft.ifft2(ifft)

  # ifft = fftpack.ifft2(channel).real
  channel_shift = channel * (255.0 / channel.max())
  # ifft = np.fft.ifft2(channel_shift)
  ifft = np.fft.ifftn(channel_shift)
  # ifft *= 255.0 / ifft.max()  # proper scaling back to 0..255 range

  # return np.absolute(ifft)
  return ifft

def filter_fft(frame, keep_fraction = 0.1):
  # ifftshift, fft2, fft
  # f_ishift = np.fft.ifftshift(frame)
  # return f_ishift

  channels = cv2.split(frame.real)
  result_array = np.zeros_like(frame.real)

  if frame.shape[2] > 1:  # grayscale images have only one channel
    for i, channel in enumerate(channels):
      result_array[..., i] = filter(channel, keep_fraction)
  else:
    result_array[...] = filter(channels[0], keep_fraction)

  return np.array(result_array) # Image.fromarray(result_array)

def to_fft(frame):
  # ifftshift, fft2, fft
  # f_ishift = np.fft.ifftshift(frame)
  # return f_ishift

  channels = cv2.split(frame)
  result_array = np.zeros_like(frame, dtype=float)

  if frame.shape[2] > 1:  # grayscale images have only one channel
    # for i, channel in enumerate(channels):
    #   result_array[..., i] = fft(channel)
    result_array = np.fft.fftn(frame)
  else:
    result_array[...] = fft(channels[0])

  return np.array(result_array) # Image.fromarray(result_array)

def from_fft(frame):
  # img_back = np.fft.ifft2(f_ishift)
  # return img_back
  breakpoint()
  channels = cv2.split(frame)
  result_array = np.zeros_like(frame, dtype=float)

  if frame.shape[2] > 1:  # grayscale images have only one channel
    for i, channel in enumerate(channels):
      result_array[..., i] = ifft(channel)

    # result_array = np.absolute(np.fft.ifftn(frame))
    # result_array = np.fft.ifftn(frame) #.real
  else:
    result_array[...] = ifft(channels[0])

  return np.array(result_array) # Image.fromarray(result_array)

def avg_tensor(tensor_stack):
  return np.mean(tensor_stack, axis=0)

def save(frame, name):
  cv2.imwrite(f'{save_path}{name}{output_filetype}', frame)

def plot(image, caption='Original image'):
  # im = plt.imread('../../../../data/moonlanding.png').astype(float)

  plt.figure()
  # plt.imshow(image, plt.cm.gray)
  plt.imshow(image)
  plt.title(caption)
  plt.show()

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

def open_file(path):
  return cv2.imread(path)

def open_files(stacked_file_paths):
  list_of_images = []

  for raw_file_path in stacked_file_paths:
    # raw = rawpy.imread(raw_file_path)
    # im = raw.raw_image
    list_of_images.append(open_file(raw_file_path))

  return np.array(list_of_images)

# def find_significance(fft_frames):
# stacked_file_paths

base_images = open_files(stacked_file_paths)
print(f'Number of files: {len(base_images)}')

base_image = base_images[0]
# save(base_image, 'base_image')
plot(base_image, 'Base Image')


# TEST:
# base_fft = to_fft(base_image)
# base_fft = fft(base_image[:,:,0])
base_fft = fft(base_image)
plot(base_fft.real, 'Base FFT')
# save(base_fft, 'base_image_fft')

filtered_base_image = filter_fft(base_fft, keep_fraction = 0.2)
plot(filtered_base_image.real, 'Base Filter')

# base_ifft = from_fft(base_fft)
base_ifft = ifft(filtered_base_image[:,:,0])
plot(base_ifft.real, 'Base IFFT Filter')
# save(base_ifft.real, 'base_image_ifft')

# print('Filter Test')
# base_image_fft = to_fft(base_image)
# base_image_filter_fft = filter_fft(base_image_fft, keep_fraction = 0.2)
# save(base_image_filter_fft, 'base_image_filter_fft')
# filtered_base_image = from_fft(base_image_filter_fft)

# breakpoint()
# im = Image.fromarray(filtered_base_image)
# im.save(f'{save_path}filtered_base_image.png')
# cv2.imwrite(f'{save_path}filtered_base_image.bmp', im)
# save(filtered_base_image, 'filtered_base_image')
# plot(filtered_base_image)

# print("Generate FFT Stack")
# fft_stack = generate_fft_stack(base_images)
# # save_stack(fft_stack, 'fft')

# print('Compute AVG Tensor')
# avg_fft = avg_tensor(fft_stack)
# save(avg_fft, f'avg_fft')

# print('Convert back to image')
# avg_image = from_fft(avg_fft)
# save(avg_image, f'avg_fft_converted')
# plot(avg_image)

print('Complete!')
