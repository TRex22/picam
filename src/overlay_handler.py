import numpy as np
from PIL import Image

import math

from picamerax import mmal

# Modules
import mmal_handler

def compute_shutter_speed_from_us(us):
  if us == 0:
    return 'auto'

  return f'1/{math.ceil(1000000/us)} ({us} us.)'

def display_text(camera, text, config):
  # camera.annotate_text = f'{camera.annotate_text} - {camera.exposure_mode}'
  if config["video"]:
    mode = "Video Mode"
  else:
    mode = "Photo Mode"

  menu_item = config["menu_item"]

  selected_item = f'Selected Menu Item: {config["menu_item"]}'
  camera_settings = f"exposure mode: {camera.exposure_mode}, iso: {camera.iso}, awb mode: {config['awb_mode']}"

  shutter_speed = compute_shutter_speed_from_us(config["shutter_speed"])

  parameter = mmal.MMAL_PARAMETER_SHUTTER_SPEED
  set_shutter_speed = camera._get_shutter_speed() # camera.shutter_speed

  fps = camera.fps
  framerate = camera.framerate

  shutter_text = f'Shutter Speed: {shutter_speed}, set: {set_shutter_speed}'
  boolean_text = f'hdr: {config["hdr"]}, raw_convert: {config["raw_convert"]}, dpc: {config["dpc"]}'
  output_text = f'{mode} - fps:{fps} - {framerate}\n{camera_settings}\n{boolean_text}\n{selected_item}\n{shutter_text}\n{text}'

  camera.annotate_text_size = config["annotate_text_size"]
  camera.annotate_text = output_text

# https://picamera.readthedocs.io/en/release-1.10/recipes1.html#overlaying-images-on-the-preview
def add_overlay(camera, overlay, config):
  if overlay != None:
    return overlay

  overlay_w = config["overlay_w"] # 320
  overlay_h = config["overlay_h"] # 280

  img = generate_overlay_image(overlay_h, overlay_w)
  image_bytes = img.tobytes()

  # Broken docs ...
  # overlay = camera.add_overlay(a.tobytes(), layer=3, alpha=64)

  # Image.new("RGB", (320, 240))
  # overlay = camera.add_overlay(Image.fromarray(a, 'RGB'), size=(320,240), layer=3, alpha=64)
  overlay = camera.add_overlay(image_bytes, size=img.size, layer=3, alpha=64, format="rgba")
  display_text(camera, '', config)

  camera.framerate = config["screen_fps"]

  return overlay

def remove_overlay(camera, overlay, config):
  if camera != None and overlay != None:
    camera.remove_overlay(overlay)
    camera.annotate_text = None
    camera.framerate = config["fps"]

  return None

def generate_overlay_image(overlay_h, overlay_w):
  # Create an array representing a wxh image of
  # a cross through the center of the display. The shape of
  # the array must be of the form (height, width, color)
  a = np.zeros((overlay_h, overlay_w, 4), dtype=np.uint8)
  half_height = int(overlay_h/2)
  half_width = int(overlay_w/2)

  a[half_height, :, :] = 0xff
  a[:, half_width, :] = 0xff

  return Image.fromarray(a)
