# TODO: Commandline inputs
# Converts JPEGs with bayer EXIFdata into DNGs with camera profile applied
VERSION = "0.0.2"

import sys
sys.path.insert(1, '../src/')
sys.path.insert(1, 'src/')

import time
import glob
import re

from io import BytesIO

from pydng.core import RPICAM2DNG

# Modules
import document_handler

# Constants
original_files_path = "/mnt/g/tmp/original"
raw_file_save_path = "/mnt/g/tmp/raw"
filetype = '.dng'

# TODO: List them all
# Colour profiles:
# colour_profile_path = "../Colour_Profiles/imx477/Raspberry Pi High Quality Camera Lumariver 2860k-5960k Neutral Look.json"
# colour_profile_path = "../Colour_Profiles/imx477/Raspberry Pi High Quality Camera Lumariver 2860k-5960k Skin+Sky Look.json"
# colour_profile_path = "../Colour_Profiles/imx477/PyDNG_profile"

config = {
  "neutral_colour_profile": "../Colour_Profiles/imx477/Raspberry Pi High Quality Camera Lumariver 2860k-5960k Neutral Look.json",
  "neutral_colour_profile_name": "neutral_colour",
  "skin_tone_colour_profile": "../Colour_Profiles/imx477/Raspberry Pi High Quality Camera Lumariver 2860k-5960k Skin+Sky Look.json",
  "skin_tone_colour_profile_name": "skin_tone",
  "pydng_colour_profile": "../Colour_Profiles/imx477/PyDNG_profile.json",
  "pydng_colour_profile_name": "pydng",
  "selected_colour_profile": "neutral_colour_profile" #"all" # can be all or neutral_colour_profile, skin_tone_colour_profile, pydng_colour_profile ... others to be added later
}

def generate_filename(original_files_path, raw_file_save_path, f, config, colour_profile_name):
  raw_file_save_path_with_profile = f'{raw_file_save_path}/{colour_profile_name}'
  document_handler.detect_or_create_folder(raw_file_save_path_with_profile)

  filename = re.sub(original_files_path, raw_file_save_path_with_profile, f)
  filename = re.sub('.jpg', filetype, filename)
  filename = re.sub('.jpeg', filetype, filename)

  return filename

def convert_file(f, filename, config, colour_profile_name):
  print(f'{f} -> {filename}', end='')
  start_time = time.time()

  json_colour_profile = document_handler.load_colour_profile({ "colour_profile_path": config[colour_profile_name] })

  # Open file as a stream
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
  except:
    print(' ... failed, skipping file.')

print(f'Starting to convert original images to RAW with colour profile (Version: {VERSION})...')
print(f'original_files_path: {original_files_path}')
print(f'raw_file_save_path: {raw_file_save_path}\n')

document_handler.detect_or_create_folder(original_files_path)
document_handler.detect_or_create_folder(raw_file_save_path)

original_files = glob.glob(f'{original_files_path}/*')
print(f'{len(original_files)} files to be processed.\n')

global_start_time = time.time()

colour_profile_name = config["selected_colour_profile"]
if (colour_profile_name == 'all' or colour_profile_name == "ALL"):
  print("Converting files to all colour profiles...")
  # TODO: Clean up this code even more

  profile_start_time = time.time()
  for f in original_files:
    filename = generate_filename(original_files_path, raw_file_save_path, f, config, "neutral_colour_profile")
    convert_file(f, filename, config, "neutral_colour_profile")
  print(f'--- {(time.time() - profile_start_time)} total profile seconds ---\n')

  profile_start_time = time.time()
  for f in original_files:
    filename = generate_filename(original_files_path, raw_file_save_path, f, config, "skin_tone_colour_profile")
    convert_file(f, filename, config, "skin_tone_colour_profile")
  print(f'--- {(time.time() - profile_start_time)} total profile seconds ---\n')

  profile_start_time = time.time()
  for f in original_files:
    filename = generate_filename(original_files_path, raw_file_save_path, f, config, "pydng_colour_profile")
    convert_file(f, filename, config, "pydng_colour_profile")
  print(f'--- {(time.time() - profile_start_time)} total profile seconds ---\n')
else:
  print(f'Converting files to {colour_profile_name}...')

  for f in original_files:
    filename = generate_filename(original_files_path, raw_file_save_path, f, config, colour_profile_name)
    convert_file(f, filename, config, colour_profile_name)

total_time = (time.time() - global_start_time)
average_time = total_time / len(original_files)

print(f'\n--- {total_time} total seconds ---')
print(f'--- {average_time} average seconds ---')

print('Much Success!')
