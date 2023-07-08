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
import rawpy

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

  # raw_file_path = '/run/media/trex22/Scratch Disk/tmp/812 Waxing Gibbons/raw/812.dng'

  save_path = 'G:\\tmp\\continious_shot\\3\\output\\'
  frames_save_path = f'{save_path}\\frames'
else:
  stacked_file_paths = [
    "/data/photography/continious_shot/3/885_continuous.jpeg",
    "/data/photography/continious_shot/3/886_continuous.jpeg",
    "/data/photography/continious_shot/3/887_continuous.jpeg",
    "/data/photography/continious_shot/3/888_continuous.jpeg",
    "/data/photography/continious_shot/3/889_continuous.jpeg",
    "/data/photography/continious_shot/3/890_continuous.jpeg",
    "/data/photography/continious_shot/3/891_continuous.jpeg",
    "/data/photography/continious_shot/3/892_continuous.jpeg",
    "/data/photography/continious_shot/3/893_continuous.jpeg",
    "/data/photography/continious_shot/3/894_continuous.jpeg"
  ]

  # stacked_file_paths = [
  #   "/data/photography/continious_shot/3/raw/885_continuous.dng",
  #   "/data/photography/continious_shot/3/raw/886_continuous.dng",
  #   "/data/photography/continious_shot/3/raw/887_continuous.dng",
  #   "/data/photography/continious_shot/3/raw/888_continuous.dng",
  #   "/data/photography/continious_shot/3/raw/889_continuous.dng",
  #   "/data/photography/continious_shot/3/raw/890_continuous.dng",
  #   "/data/photography/continious_shot/3/raw/891_continuous.dng",
  #   "/data/photography/continious_shot/3/raw/892_continuous.dng",
  #   "/data/photography/continious_shot/3/raw/893_continuous.dng",
  #   "/data/photography/continious_shot/3/raw/894_continuous.dng"
  # ]

  # raw_file_path = '/run/media/trex22/Scratch Disk/tmp/812 Waxing Gibbons/raw/812.dng'

  save_path = '/run/media/trex22/Scratch Disk/tmp/continious_shot/3/output/'
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
  fft = np.fft.fft2(channel)
  # fft = np.fft.fftn(channel) # whole image
  # fft = np.fft.fftn(channel[...,::-1])
  # fft = np.fft.fftshift(channel)
  # fft *= 255.0 / fft.max()  # proper scaling into 0..255 range
  # return np.absolute(fft)
  return fft

def ifft(channel):
  # ifft = np.fft.ifftshift(channel)
  # ifftc *= 255.0 / ifft.max()
  # ifft = np.fft.ifft2(ifft)

  # ifft = fftpack.ifft2(channel).real
  # channel_shift = channel * (255.0 / channel.max())
  ifft = np.fft.ifft2(channel)
  # ifft = np.fft.ifftn(channel_shift)
  # ifft = np.fft.ifftn(channel)
  # ifft *= 255.0 / ifft.max()  # proper scaling back to 0..255 range

  # return np.absolute(ifft)
  return ifft

def channel_shift(channel):
  return channel * (255.0 / channel.max())

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

def to_fft(image):
  # ifftshift, fft2, fft
  # f_ishift = np.fft.ifftshift(frame)
  # return f_ishift

  # channels = cv2.split(frame)
  # result_array = np.zeros_like(frame, dtype=float)

  # if frame.shape[2] > 1:  # grayscale images have only one channel
  #   for i, channel in enumerate(channels):
  #     ichan = np.fft.fft2(channel)
  #     # ichan *= 255.0 / ichan.max()
  #     # result_array[..., i] = ichan
  #     result_array[..., i] = np.fft.fftshift(ichan)

  #   # result_array = np.fft.fft2(frame)
  # else:
  #   result_array[...] = np.fft.fft2(channels[0])

  # return np.array(result_array) # Image.fromarray(result_array)
  rgb_fft = np.zeros_like(image, dtype=float)

  for i in range(3):
    rgb_fft[..., i] = np.fft.fftshift(np.fft.fft2((image[:, :, i])))

  return np.array(rgb_fft)

def from_fft(frame):
  # img_back = np.fft.ifft2(f_ishift)
  # return img_back
  # channels = np.split(frame, 3, axis=2)
  # result_array = np.zeros_like(frame, dtype=float)

  # if frame.shape[2] > 1:  # grayscale images have only one channel
  #   for i, channel in enumerate(channels):
  #     ichan = np.fft.fft2(channel[:,:,0])
  #     # ichan *= 255.0 / ichan.max()
  #     result_array[..., i] = np.abs(np.fft.ifft2(ichan))

    # result_array[..., 0] = np.fft.ifft2(frame[:,:,0]).real
    # result_array[..., 1] = np.fft.ifft2(frame[:,:,1]).real
    # result_array[..., 2] = np.fft.ifft2(frame[:,:,2]).real

    # result_array = np.absolute(np.fft.ifftn(frame))
    # result_array = np.fft.ifftn(frame) #.real
  # else:
  #   result_array[...] = np.fft.ifft2(channels[0])
  # result_array = np.zeros_like(frame, dtype=float)
  # result_array[..., 0] = abs(np.fft.ifft2(frame[:,:,0]))
  # result_array[..., 1] = abs(np.fft.ifft2(frame[:,:,1]))
  # result_array[..., 2] = abs(np.fft.ifft2(frame[:,:,2]))

  # return np.array(result_array) # Image.fromarray(result_array)

  transformed_channels = [
    abs(np.fft.ifft2(frame[0])),
    abs(np.fft.ifft2(frame[1])),
    abs(np.fft.ifft2(frame[2]))
  ]
  return np.dstack([transformed_channels[0].astype(int),
             transformed_channels[1].astype(int),
             transformed_channels[2].astype(int)])

# https://stackoverflow.com/questions/43626200/numpy-mean-of-complex-numbers-with-infinities#43626307
# https://stackoverflow.com/questions/43626200/numpy-mean-of-complex-numbers-with-infinities
def avg_tensor(tensor_stack):
  # return np.mean(tensor_stack, axis=0)
  return np.mean(tensor_stack[np.isfinite(tensor_stack)], axis=0)

def save(frame, name):
  cv2.imwrite(f'{save_path}{name}{output_filetype}', frame)

def plot(image, caption='Original image'):
  # im = plt.imread('../../../../data/moonlanding.png').astype(float)

  plt.figure()
  # plt.imshow(image, plt.cm.gray)
  # plt.imshow(image[...,::-1]) # cv2.cvtColor(lena, cv2.COLOR_BGR2RGB)
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
  return cv2.cvtColor(cv2.imread(path), cv2.COLOR_BGR2RGB)
  # return rawpy.imread(path).raw_image

def open_files(stacked_file_paths):
  list_of_images = []

  for raw_file_path in stacked_file_paths:
    # raw = rawpy.imread(raw_file_path)
    # im = raw.raw_image
    list_of_images.append(open_file(raw_file_path))

  return np.array(list_of_images)

# def find_significance(fft_frames):
# stacked_file_paths

# https://www.pythonpool.com/numpy-ifft/
# https://towardsdatascience.com/image-processing-with-python-application-of-fourier-transformation-5a8584dc175b
def fourier_transform_rgb(image):
  f_size = 25
  transformed_channels = []
  for i in range(3):
    rgb_fft = np.fft.fftshift(np.fft.fft2((image[:, :, i])))
    rgb_fft[:225, 235:237] = 1
    rgb_fft[-225:,235:237] = 1
    transformed_channels.append(abs(np.fft.ifft2(rgb_fft)))

  final_image = np.dstack([transformed_channels[0].astype(int),
                           transformed_channels[1].astype(int),
                           transformed_channels[2].astype(int)])

  fig, ax = plt.subplots(1, 2, figsize=(17,12))
  ax[0].imshow(image)
  ax[0].set_title('Original Image', fontsize = f_size)
  ax[0].set_axis_off()

  ax[1].imshow(final_image)
  ax[1].set_title('Transformed Image', fontsize = f_size)
  ax[1].set_axis_off()

  fig.tight_layout()
  plt.show()

base_images = open_files(stacked_file_paths)
print(f'Number of files: {len(base_images)}')

# base_image = base_images[0]
# fourier_transform_rgb(base_image)

print("Generate FFT Stack")
fft_stack = generate_fft_stack(base_images)

print('Compute AVG Tensor')
avg_fft = avg_tensor(fft_stack)
# plot(avg_fft.real, 'AVG FFT')

print('Filter AVG Tensor')
# filtered_base_image = filter_fft(avg_fft, keep_fraction = 0.2)
# plot(filtered_base_image, 'FILTER AVG FFT')

print('Convert back to image')
avg_image = from_fft(avg_fft)
# save(avg_image, f'avg_fft_converted')
plot(avg_image.real, 'AVG_IMAGE')

print('Complete!')
