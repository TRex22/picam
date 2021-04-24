import numpy as np
from PIL import Image, ImageDraw, ImageFont

# https://picamera.readthedocs.io/en/release-1.10/recipes1.html#overlaying-images-on-the-preview
def add_overlay(camera, overlay, config):
  if overlay != None:
    return overlay

  overlay_w = config["screen_w"] # 320
  overlay_h = config["screen_h"] # 280

  # Create an array representing a wxh image of
  # a cross through the center of the display. The shape of
  # the array must be of the form (height, width, color)
  a = np.zeros((overlay_h, overlay_w, 4), dtype=np.uint8)
  half_height = int(overlay_h/2)
  half_width = int(overlay_w/2)

  a[half_height, :, :] = 0xff
  a[:, half_width, :] = 0xff

  # Create image bytes
  img = Image.fromarray(a, 'RGBA')
  image_bytes = img.tobytes()

  # Broken docs ...
  # overlay = camera.add_overlay(a.tobytes(), layer=3, alpha=64)

  # Image.new("RGB", (320, 240))
  # overlay = camera.add_overlay(Image.fromarray(a, 'RGB'), size=(320,240), layer=3, alpha=64)
  overlay = camera.add_overlay(image_bytes, size=img.size, layer=3, alpha=64, format="rgba")
  camera.annotate_text = 'Photo mode' # TODO: Cleanup

  return overlay

def remove_overlay(camera, overlay):
  camera.remove_overlay(overlay)
  camera.annotate_text = None

  # del overlay # Doesnt work
  # overlay = None # Global variable
