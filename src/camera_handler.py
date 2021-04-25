import os
import shutil
import time
import glob
import json

from io import BytesIO
from picamerax import PiCamera

import RPi.GPIO as GPIO

from pydng.core import RPICAM2DNG
from pydng.core import RAW2DNG, DNGTags, Tag

import document_handler

def take_single_shot(camera, config):
  screen_w = config["screen_w"]
  screen_h = config["screen_h"]

  width = config["width"]
  height = config["height"]

  dcim_path = config["dcim_path"]
  dcim_images_path_raw = config["dcim_images_path_raw"]
  dcim_original_images_path = config["dcim_original_images_path"]
  dcim_hdr_images_path = config["dcim_hdr_images_path"]
  dcim_videos_path = config["dcim_videos_path"]
  dcim_tmp_path = config["dcim_tmp_path"]

  format = config["format"]
  bayer = config["bayer"]

  existing_files = glob.glob(f'{dcim_original_images_path}/*.{format}')
  filecount = len(existing_files)
  frame_count = filecount

  filename = f'{dcim_images_path_raw}/{frame_count}.{format}'
  original_filename = f'{dcim_original_images_path}/{frame_count}.{format}'
  print(original_filename)

  stream = BytesIO()

  start_time = time.time()
  camera.resolution = (width, height)
  # Set iso

  # Fix other settings
  # Now fix the values
  camera.shutter_speed = 150000 #camera.exposure_speed
  # camera.exposure_mode = 'off'
  # off, auto, night, nightpreview, backlight, spotlight, sports, snow, beach,
  # verylong, fixedfps, antishake, fireworks
  camera.exposure_mode = 'auto'
  g = camera.awb_gains
  camera.awb_mode = 'off'
  camera.awb_gains = g

  print(f'screen: ({screen_w}, {screen_h}), res: ({width}, {height}), shutter_speed: {camera.shutter_speed}')

  camera.capture(stream, format, bayer=bayer)

  with open(original_filename, 'wb') as f:
    f.write(stream.getbuffer())

  if (config["convert_raw"] == True):
    print("Begin conversion and save DNG raw ...")
    json_colour_profile = document_handler.load_colour_profile(config)
    output = RPICAM2DNG().convert(stream, json_camera_profile=json_colour_profile)

    with open(filename, 'wb') as f:
      f.write(output)
  else:
    print("--- skip raw conversion ---")

  print("--- %s seconds ---" % (time.time() - start_time))

  camera.resolution = (screen_w, screen_h)
