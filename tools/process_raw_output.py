# TODO: Commandline inputs
# Converts JPEGs with bayer EXIFdata into DNGs with camera profile applied
VERSION = "0.0.1"

import sys
sys.path.insert(1, '../src/')
sys.path.insert(1, 'src/')

import os
import time
import glob
import re

from io import BytesIO

from pydng.core import RPICAM2DNG
from pydng.core import RAW2DNG, DNGTags, Tag

# Modules
import document_handler

# Constants
original_files_path = "/home/pi/DCIM/images/original"
raw_file_save_path = "/home/pi/DCIM/images/raw"
filetype = '.dng'

# TODO: List them all
# Colour profiles:
colour_profile_path = "/home/pi/Colour_Profiles/imx477/Raspberry Pi High Quality Camera Lumariver 2860k-5960k Neutral Look.json"
# colour_profile_path = "/home/pi/Colour_Profiles/imx477/Raspberry Pi High Quality Camera Lumariver 2860k-5960k Skin+Sky Look.json"
# colour_profile_path = "/home/pi/Colour_Profiles/imx477/PyDNG_profile"

print(f'Starting to convert original images to RAW with colour profile (Version: {VERSION})...')
print(f'original_files_path: {original_files_path}')
print(f'raw_file_save_path: {raw_file_save_path}\n')

json_colour_profile = document_handler.load_colour_profile({ "colour_profile_path": colour_profile_path })

document_handler.detect_or_create_folder(original_files_path)
document_handler.detect_or_create_folder(raw_file_save_path)

original_files = glob.glob(f'{original_files_path}/*')
print(f'{len(original_files)} files to be processed.\n')

global_start_time = time.time()

for f in original_files:
  filename = re.sub(original_files_path, raw_file_save_path, f)
  filename = re.sub('.jpg', filetype, filename)
  filename = re.sub('.jpeg', filetype, filename)

  print(f'{f} -> {filename}', end='')

  # Open file as a stream
  start_time = time.time()
  stream = BytesIO()

  try:
    with open(f, 'rb') as original_f_stream:
      stream = BytesIO(original_f_stream.read())

    output = RPICAM2DNG().convert(stream, json_camera_profile=json_colour_profile)
    stream.close()

    with open(filename, 'wb') as raw_f_stream:
      raw_f_stream.write(output)

    # Completed file conversion
    print(f' ({(time.time() - start_time)} seconds)')
  finally:
    print(' ... failed, skipping file.')

total_time = (time.time() - global_start_time)
average_time = total_time / len(original_files)

print(f'--- {total_time} total seconds ---')
print(f'--- {average_time} average seconds ---')

print('Much Success!')
