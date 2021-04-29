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

def adjust_exposure_mode(camera, config):
  # Fix other settings
  # Now fix the values
  # camera.shutter_speed = 150000 #camera.exposure_speed
  # # camera.exposure_mode = 'off'
  # # off, auto, night, nightpreview, backlight, spotlight, sports, snow, beach,
  # # verylong, fixedfps, antishake, fireworks
  # camera.exposure_mode = 'auto'
  # g = camera.awb_gains
  # camera.awb_mode = 'off'
  # camera.awb_gains = g

  idex = config["available_exposure_modes"].index(config["exposure_mode"]) + 1

  if idex < len(config["available_exposure_modes"]):
    camera.exposure_mode = config["available_exposure_modes"][idex]
  else:
    camera.exposure_mode = 'off'

  overlay_handler.display_text(camera, 'Photo Mode', config)

  config["exposure_mode"] = camera.exposure_mode
  print(f'exposure_mode: {config["exposure_mode"]}')

def adjust_iso(camera, config):
  idex = config["available_isos"].index(config["iso"]) + 1

  if idex < len(config["available_isos"]):
    camera.iso = config["available_isos"][idex]
  else:
    camera.iso = 0

  overlay_handler.display_text(camera, 'Photo Mode', config)

  config["iso"] = camera.iso
  print(f'iso: {config["iso"]}')

def take_hdr_shot(camera, config):
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

  overlay_handler.remove_overlay(camera, overlay, config)
  overlay = None

  camera.resolution = (width, height)

  start_time = time.time()
  available_exposure_compensations = [-25, -20, -15, -10, -5, 0, 5, 10, 15, 20, 25] # TODO

  # SEE: https://github.com/KEClaytor/pi-hdr-timelapse
  nimages = 5 #10 #2160
  exposure_min = 10
  exposure_max = 80 #90
  exp_step = 5

  exp_step = (exposure_max - exposure_min) / (nimages - 1.0)
  exposure_times = range(exposure_min, exposure_max + 1, int(exp_step))

  filenames = []

  existing_files = glob.glob(f'{dcim_hdr_images_path}/*.{format}')
  filecount = len(existing_files)
  frame_count = filecount

  original_brightness = camera.brightness
  # original_exposure_compensation = camera.exposure_compensation

  for step in exposure_times: # available_exposure_compensations:
    filename = f'{dcim_hdr_images_path}/{frame_count}_{step}_HDR.{format}'
    # filename = f'{dcim_tmp_path}/{frame_count}_{step}_HDR.{format}'

    camera.brightness = step
    # camera.exposure_compensation = step

    camera.capture(filename, format, bayer=True)

  camera.brightness = original_brightness
  # camera.exposure_compensation = original_exposure_compensation

  camera.resolution = (screen_w, screen_h)
  overlay = overlay_handler.add_overlay(camera, overlay, config)

  # for file in filenames:
  # shutil.copyfile(src, dst)

  print("--- %s seconds ---" % (time.time() - start_time))

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
