import numpy as np
from PIL import Image, ImageDraw, ImageFont

def display_text(camera, text, config):
  # camera.annotate_text = f'{camera.annotate_text} - {camera.exposure_mode}'
  if config["video"]:
    mode = "Photo Mode"
  else:
    mode = "Video Mode"

  menu_item = config["menu_item"]
  camera.annotate_text = f'{mode} - exposure mode: {camera.exposure_mode}, iso: {camera.iso}, hdr: {config["hdr"]}\nSelected Menu Item: {config["menu_item"]}\n{text}'

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
  camera.annotate_text = 'Photo mode' # TODO: Cleanup

  camera.framerate = config["screen_fps"]

  return overlay

def remove_overlay(camera, overlay, config):
  camera.remove_overlay(overlay)
  camera.annotate_text = None
  camera.framerate = config["fps"]

  # del overlay # Doesnt work
  # overlay = None # Global variable

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
