import os
import time
import glob
import math

from io import BytesIO

from picamerax import PiCamera
from picamerax import mmal

import RPi.GPIO as GPIO

# Modules
import overlay_handler
import menu_handler
import mmal_handler
from thread_writer import ThreadWriter
from thread_raw_converter import ThreadRawConverter

################################################################################
##                                Camera Instance                             ##
################################################################################
def start_preview(camera, config):
  config["preview"] = True

  # options are: "built-in" "continuous_shot"
  # if config["preview_mode"] == "continuous_shot":
  #   format = config["format"]
  #   bayer = config["bayer"]

  #   # for frame in camera.capture_continuous(rawCapture, format=format, bayer=bayer, use_video_port=True):
  #   # TODO:
  #   time.sleep(0.1)
  # else: # default
  #   camera.start_preview()
  #   key_press = input("Press enter to quit\n\n") # Run until someone presses enter
  #   print(key_press)

  camera.start_preview()
  key_press = input("Press enter to quit\n\n") # Run until someone presses enter
  print(key_press)

def stop_preview(camera, config):
  # Just set the variable. The loop in the other thread will halt on next iteration
  config["preview"] = False

  if config["preview_mode"] == config["default_preview_mode"]:
    camera.stop_preview()

def start_camera(original_config, skip_auto=False):
  global camera
  global overlay
  global config

  # Force variables to be blanked
  camera = None
  overlay = None
  config = original_config

  # Config Variables
  screen_fps = config["screen_fps"]
  capture_timeout = config["capture_timeout"]

  screen_w = config["screen_w"]
  screen_h = config["screen_h"]
  width = config["width"]
  height = config["height"]

  # Init
  # https://github.com/waveform80/picamera/issues/329
  PiCamera.CAPTURE_TIMEOUT = capture_timeout
  print(f'Camera Timeout: {PiCamera.CAPTURE_TIMEOUT}')
  camera = PiCamera() # framerate=fps is bugged - rather set camera.framerate

  if skip_auto == False:
    auto_mode(camera, overlay, config)

  overlay = None

  camera.resolution = (screen_w, screen_h)
  camera.framerate = screen_fps # fps

  config["set_zoom"] = '1x'

  overlay = overlay_handler.add_overlay(camera, overlay, config)
  overlay_handler.display_text(camera, '', config)
  print(f'screen: ({screen_w}, {screen_h}), res: ({width}, {height})')

  start_button_listen(config)
  start_preview(camera, config)

  return [camera, overlay]

def stop_camera(camera, overlay, config):
  stop_preview(camera, config)

  if overlay != None:
    overlay_handler.remove_overlay(camera, overlay, config)

  if camera != None:
    camera.close()

################################################################################
##                                  GPIO Stuff                                ##
################################################################################
def button_callback_1():
  global camera
  global overlay
  global config

  print("Button 1: Menu")
  menu_handler.select_menu_item(camera, config)

def button_callback_2():
  global camera
  global overlay
  global config

  print("Button 2: Option")
  menu_handler.select_option(camera, overlay, config)

def button_callback_3():
  global camera
  global overlay
  global config

  print("Button 3: Zoom")
  zoom(camera, config)
  overlay = overlay_handler.add_overlay(camera, overlay, config)

def button_callback_4():
  global camera
  global overlay
  global config

  print("Button 4: Take shot")

  overlay = overlay_handler.remove_overlay(camera, overlay, config)

  if config['delay_time'] != 0:
    time.sleep(config['delay_time'])

  if config["video"]:
    trigger_video(camera, overlay, config)
  else:
    if config["hdr"]:
      take_hdr_shot(camera, overlay, config)
    else:
      take_single_shot(camera, overlay, config)

  overlay = overlay_handler.add_overlay(camera, overlay, config)

def start_button_listen(config):
  # GPIO Config
  button_1 = config["gpio"]["button_1"]
  button_2 = config["gpio"]["button_2"]
  button_3 = config["gpio"]["button_3"]
  button_4 = config["gpio"]["button_4"]
  bouncetime = config["gpio"]["bouncetime"]

  # Set button callbacks
  # GPIO.setwarnings(False) # Ignore warning for now
  GPIO.setwarnings(True)
  # GPIO.setmode(GPIO.BOARD) # Use physical pin numbering
  GPIO.setmode(GPIO.BCM)

  GPIO.setup(button_1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
  GPIO.setup(button_2, GPIO.IN, pull_up_down=GPIO.PUD_UP)
  GPIO.setup(button_3, GPIO.IN, pull_up_down=GPIO.PUD_UP)
  GPIO.setup(button_4, GPIO.IN, pull_up_down=GPIO.PUD_UP)

  GPIO.add_event_detect(button_1, GPIO.RISING, callback=lambda x: button_callback_1(), bouncetime=bouncetime)
  GPIO.add_event_detect(button_2, GPIO.RISING, callback=lambda x: button_callback_2(), bouncetime=bouncetime)
  GPIO.add_event_detect(button_3, GPIO.RISING, callback=lambda x: button_callback_3(), bouncetime=bouncetime)
  GPIO.add_event_detect(button_4, GPIO.RISING, callback=lambda x: button_callback_4(), bouncetime=bouncetime)

def stop_button_listen():
  GPIO.cleanup() # Clean up

################################################################################
##                                Camera Actions                              ##
################################################################################

# TODO - Better auto and other modes
# Reference:
# camera.iso = 1600
# camera.shutter_speed = 1000000000
# camera.exposure_compensation = 10
# camera.exposure_mode = 'off' #'auto'
# camera.image_denoise = True
# camera.image_effect = 'none'
# camera.drc_strength = 'off'
# camera.contrast = 10
# camera.brightness = 50
# camera.hflip = False
# camera.vflip = False
# camera.rotation = 270
def auto_mode(camera, overlay, config, skip_dpc=False):
  print('auto mode!')

  camera.iso = config["default_iso"]
  camera.exposure_mode = config["default_exposure_mode"]
  camera.shutter_speed = config["default_shutter_speed"]
  camera.awb_mode = config["default_awb_mode"]
  camera.framerate = compute_framerate(camera, config)

  if skip_dpc == False and config['dpc'] != config['default_dpc']:
    config['dpc'] = config['default_dpc']
    set_dpc(camera, overlay, config)

  if config["fom"] != config["default_fom"]:
    config["fom"] = config["default_fom"]
    adjust_fom(camera, config)
    set_fom(camera, config)

  overlay_handler.display_text(camera, '', config)

def adjust_exposure_mode(camera, config):
  idex = config["available_exposure_modes"].index(config["exposure_mode"]) + 1

  if idex < len(config["available_exposure_modes"]):
    camera.exposure_mode = config["available_exposure_modes"][idex]
  else:
    camera.exposure_mode = config["default_exposure_mode"]

  overlay_handler.display_text(camera, '', config)

  config["exposure_mode"] = camera.exposure_mode
  print(f'exposure_mode: {config["exposure_mode"]}')

def adjust_delay(camera, config):
  if idex < len(config["delay_times"]):
    idex = config["delay_times"].index(config["delay_time"]) + 1
  else:
    idex = 0

  config["delay_time"] = config["delay_times"][idex]

  overlay_handler.display_text(camera, '', config)
  print(f'delay_time: {config["delay_time"]}')

def adjust_iso(camera, config):
  idex = config["available_isos"].index(config["iso"]) + 1

  if idex < len(config["available_isos"]):
    camera.iso = config["available_isos"][idex]
  else:
    camera.iso = config["default_iso"]

  overlay_handler.display_text(camera, '', config)

  config["iso"] = camera.iso
  print(f'iso: {config["iso"]}')

def adjust_shutter_speed(camera, config):
  idex = config["available_shutter_speeds"].index(config["shutter_speed"]) + 1

  if idex < len(config["available_shutter_speeds"]):
    config["shutter_speed"] = config["available_shutter_speeds"][idex]
  else:
    config["shutter_speed"] = config["default_shutter_speed"]

  # camera.framerate = compute_framerate(camera, config) # Done when taking the shot
  camera.shutter_speed = config["shutter_speed"]
  config["take_long_shutter_speed"] = False

  overlay_handler.display_text(camera, '', config)
  print(f'shutter_speed: {overlay_handler.compute_shutter_speed_from_us(config["shutter_speed"])}, set speed: {camera._get_shutter_speed()}, fps: {camera.framerate}')

def long_shutter_speed(camera, config):
  idex = config["available_long_shutter_speeds"].index(config["long_shutter_speed"]) + 1

  if idex < len(config["available_long_shutter_speeds"]):
    config["long_shutter_speed"] = config["available_long_shutter_speeds"][idex]
  else:
    config["long_shutter_speed"] = config["default_shutter_speed"]

  config["take_long_shutter_speed"] = True

  config["shutter_speed"] = 0
  camera.framerate = config["screen_fps"] # compute_framerate(camera, config) # Done when taking the shot
  camera.shutter_speed = config["shutter_speed"]

  overlay_handler.display_text(camera, '', config)
  print(f'long_shutter_speed: {overlay_handler.compute_shutter_speed_from_us(config["long_shutter_speed"])}, set speed: {camera._get_shutter_speed()}, fps: {camera.framerate}')

# TODO: Look at long vs short, and set a high speed framerate
# Alternatively set the low high fps mmal object
def compute_framerate(camera, config):
  if config["take_long_shutter_speed"] == True:
    return config["min_fps"] #1/camera.exposure_speed # Suggested approach for long exposures

  framerate = config["max_fps"]
  exposure_fps = camera.exposure_speed

  if config["shutter_speed"] > 0.0:
    exposure_fps = math.ceil(1000000/config["shutter_speed"])

  # Possible Approach:
  if exposure_fps < config["max_fps"]:
    framerate = exposure_fps

  # if framerate <= 0.009:
  #   framerate = 1.0

  return framerate

def adjust_awb_mode(camera, config):
  idex = config["available_awb_mode"].index(config["awb_mode"]) + 1

  if idex < len(config["available_awb_mode"]):
    config["awb_mode"] = config["available_awb_mode"][idex]
  else:
    config["awb_mode"] = config["default_awb_mode"]

  camera.awb_mode = config["awb_mode"]
  overlay_handler.display_text(camera, '', config)
  print(f'awb_mode: {config["awb_mode"]}')

def set_hdr(camera, config):
  config["hdr"] = not config["hdr"]
  overlay_handler.display_text(camera, '', config)
  print(f'hdr: {config["hdr"]}')

def set_video(camera, config):
  config["video"] = not config["video"]
  overlay_handler.display_text(camera, '', config)
  print(f'video: {config["video"]}')

def adjust_encoding(camera, config):
  config["encoding"] = not config["encoding"]
  overlay_handler.display_text(camera, '', config)
  print(f'encoding: {config["encoding"]}')

def adjust_dpc(config):
  current_dpc = config["dpc"]

  if (current_dpc == config["default_dpc"]):
    print("Set DPC to disabled")
    config["dpc"] = 0
  elif (current_dpc == 0):
    print("Set DPC to 1")
    config["dpc"] = 1
  elif (current_dpc == 1):
    print("Set DPC to 2")
    config["dpc"] = 2
  elif (current_dpc == 2):
    print("Set DPC to 3")
    config["dpc"] = 3
  else:
    print("Reset DPC")
    config["dpc"] = config["default_dpc"]

# Disabled until it can be done properly
def set_dpc(camera, overlay, config):
  current_dpc = config["dpc"]
  print(f'current_dpc: {current_dpc}')

  # Turn off Camera
  # stop_camera(camera, overlay, config)

  # Set DPC Mode
  # TODO: Add to MMAL interface here: https://github.com/labthings/picamerax/blob/master/picamerax/mmal.py
  # os.system(f'sudo vcdbg set imx477_dpc {current_dpc}') # TODO: Security risk here!

  # Start Camera
  # camera, overlay = start_camera(config, skip_auto=True)
  # start_preview(camera, config) # Runs main camera loop

def set_raw_convert(camera, config):
  config["raw_convert"] = not config["raw_convert"]
  overlay_handler.display_text(camera, '', config)
  print(f'raw_convert: {config["raw_convert"]}')

def adjust_fom(camera, config):
  config["fom"] = not config["fom"]
  overlay_handler.display_text(camera, '', config)

def set_fom(camera, config):
  value = config["fom"]
  parameter = mmal.MMAL_PARAMETER_DRAW_BOX_FACES_AND_FOCUS
  mmal_handler.set_mmal_parameter(camera, parameter, value)
  print(f'fom: {config["fom"]}')

def adjust_hdr2(camera, config):
  config["hdr2"] = not config["hdr2"]
  overlay_handler.display_text(camera, '', config)

def set_hdr2(camera, config):
  value = config["hdr2"]
  parameter = mmal.MMAL_PARAMETER_HIGH_DYNAMIC_RANGE
  mmal_handler.set_mmal_parameter(camera, parameter, value)
  print(f'hdr2: {config["hdr2"]}')

def zoom(camera, config):
  current_zoom = camera.zoom
  print(f'current_zoom: {current_zoom}')

  if (current_zoom == config["default_zoom"]):
    print("Set Zoom to max_zoom")
    config["set_zoom"] = '2x'
    camera.zoom = config["max_zoom"]
  elif (current_zoom == config["max_zoom"]):
    print("Set Zoom to max_zoom_2")
    config["set_zoom"] = '4x'
    camera.zoom = config["max_zoom_2"]
  elif (current_zoom == config["max_zoom_2"]):
    print("Set Zoom to max_zoom_3")
    config["set_zoom"] = '8x'
    camera.zoom = config["max_zoom_3"]
  else:
    print("Reset Zoom")
    config["set_zoom"] = '1x'
    camera.zoom = config["default_zoom"]

def take_hdr_shot(camera, overlay, config):
  screen_w = config["screen_w"]
  screen_h = config["screen_h"]

  width = config["width"]
  height = config["height"]

  format = config["format"]
  bayer = config["bayer"]

  dcim_hdr_images_path = config["dcim_hdr_images_path"]

  if config["take_long_shutter_speed"] == True:
    camera.framerate = compute_framerate(camera, config)
    camera.shutter_speed = config["long_shutter_speed"]
  else:
    camera.framerate = compute_framerate(camera, config)
    camera.shutter_speed = config["shutter_speed"]

  if config["short_delay"]:
    time.sleep(config["short_delay_time"])

  camera.resolution = (width, height)

  start_time = time.time()

  # SEE: https://github.com/KEClaytor/pi-hdr-timelapse
  nimages = 5
  exposure_min = 25
  exposure_max = 75

  exp_step = (exposure_max - exposure_min) / (nimages - 1.0)
  exposure_times = range(exposure_min, exposure_max + 1, int(exp_step))

  existing_files = glob.glob(f'{dcim_hdr_images_path}/*.{format}')
  filecount = len(existing_files)
  frame_count = filecount

  original_brightness = camera.brightness
  original_exposure_compensation = camera.exposure_compensation

  for step in exposure_times: # available_exposure_compensations:
    filename = f'{dcim_hdr_images_path}/{frame_count}_{step}_HDR.{format}'
    # filename = f'{dcim_tmp_path}/{frame_count}_{step}_HDR.{format}'

    camera.brightness = step
    # camera.exposure_compensation = step

    stream = BytesIO()
    camera.capture(stream, format, bayer=bayer)
    write_via_thread(filename, 'wb', stream.getbuffer())

  # for file in filenames:
  # shutil.copyfile(src, dst)

  print("--- %s seconds ---" % (time.time() - start_time))

  camera.brightness = original_brightness
  camera.exposure_compensation = original_exposure_compensation
  camera.resolution = (screen_w, screen_h)

  if config["take_long_shutter_speed"] == True:
    camera.framerate = config['screen_fps']
    camera.shutter_speed = 0

def take_single_shot(camera, overlay, config):
  screen_w = config["screen_w"]
  screen_h = config["screen_h"]

  width = config["width"]
  height = config["height"]

  dcim_images_path_raw = config["dcim_images_path_raw"]
  dcim_original_images_path = config["dcim_original_images_path"]

  format = config["format"]
  bayer = config["bayer"]

  existing_files = glob.glob(f'{dcim_original_images_path}/*.{format}')
  filecount = len(existing_files)
  frame_count = filecount

  raw_filename = f'{dcim_images_path_raw}/{frame_count}.dng'
  original_filename = f'{dcim_original_images_path}/{frame_count}.{format}'
  print(original_filename)

  stream = BytesIO()

  start_time = time.time()

  camera.resolution = (width, height)

  if config["take_long_shutter_speed"] == True:
    camera.framerate = compute_framerate(camera, config)
    camera.shutter_speed = config["long_shutter_speed"]
  else:
    camera.framerate = compute_framerate(camera, config)
    camera.shutter_speed = config["shutter_speed"]

  if config["short_delay"]:
    time.sleep(config["short_delay_time"])

  print(f'screen: ({screen_w}, {screen_h}), res: ({width}, {height}), shutter_speed: {camera.shutter_speed}, fps: {camera.framerate}')

  camera.capture(stream, format, bayer=bayer)
  write_via_thread(original_filename, 'wb', stream.getbuffer())

  if (config["raw_convert"] == True):
    print("Begin conversion and save DNG raw ...")
    ThreadRawConverter(config, stream, raw_filename)
  else:
    print("--- skip raw conversion ---")

  print("--- %s seconds ---" % (time.time() - start_time))

  camera.resolution = (screen_w, screen_h)

  if config["take_long_shutter_speed"] == True:
    camera.framerate = config['screen_fps']
    camera.shutter_speed = 0

def trigger_video(camera, overlay, config):
  if config["recording"]:
    camera.stop_recording()
    config["recording"] = False
  else:
    screen_w = config["screen_w"]
    screen_h = config["screen_h"]

    width = config["width"]
    height = config["height"]

    dcim_videos_path = config["dcim_videos_path"]

    format = config["video_format"]

    existing_files = glob.glob(f'{dcim_videos_path}/*.{format}')
    filecount = len(existing_files)

    original_filename = f'{dcim_videos_path}/{filecount}.{format}'
    print(original_filename)

    camera.resolution = (width, height)
    print(f'screen: ({screen_w}, {screen_h}), res: ({width}, {height}), shutter_speed: {camera.shutter_speed}')

    config["recording"] = True
    camera.start_recording(original_filename, format)

def write_via_thread(original_filename, write_type, stream):
  w = ThreadWriter(original_filename, write_type)
  w.write(stream)
  w.close()
