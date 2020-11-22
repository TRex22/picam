import os
import time
import glob

from picamera import PiCamera

# Supported file types: https://picamera.readthedocs.io/en/release-1.10/api_camera.html#picamera.camera.PiCamera.capture
# 'jpeg' - Write a JPEG file
# 'png' - Write a PNG file
# 'gif' - Write a GIF file
# 'bmp' - Write a Windows bitmap file
# 'yuv' - Write the raw image data to a file in YUV420 format
# 'rgb' - Write the raw image data to a file in 24-bit RGB format
# 'rgba' - Write the raw image data to a file in 32-bit RGBA format
# 'bgr' - Write the raw image data to a file in 24-bit BGR format
# 'bgra' - Write the raw image data to a file in 32-bit BGRA format
# 'raw' - Deprecated option for raw captures; the format is taken from the deprecated raw_format attribute

filetype = '.jpg'

dcim_images_manual_path = '/home/pi/DCIM/images/manual'
dcim_images_path = '/home/pi/DCIM/images'
dcim_videos_path = '/home/pi/DCIM/videos'

os.mkdir(dcim_images_path)
os.mkdir(dcim_videos_path)


existing_folders = glob.glob(f'{dcim_images_manual_path}/*')

filecount = len(existing_folders)
frame_count = filecount

manual_dir = f'{dcim_images_manual_path}/{filecount}'
os.mkdir(manual_dir)

camera = PiCamera()
# camera.resolution = (w, h)
# camera.brightness = step
# camera.exif_tags['IFD0.Copyright'] = 'Copyright (c) 2013 Foo Industries'

w = 3280
h = 2464
camera.resolution = (w, h)

# format = 'bgr'
# format = 'yuv'
format = 'jpeg'

# iso
# Available isos:
# 0 - 1600
# 100, 200, 320, 400, 500, 640, 800
print('=======================================================================')
print('iso')
available_isos = [0, 100, 200, 320, 400, 500, 640, 800, 1600]
for iso in available_isos:
  filename = f'{manual_dir}/{frame_count}_iso_{iso}{filetype}'
  print(filename)

  camera.iso(iso)
  camera.capture(filename, format=format)

camera.iso(0)

# shutter speed
# shutter speed of the camera in microseconds, or 0 which indicates that the speed will be automatically determined by the auto-exposure algorithm.
# You can query the exposure_speed attribute to determine the actual shutter speed being used when this attribute is set to 0.
print('=======================================================================')
print('shutter_speed')
print(f'exposure_speed for 0: {camera.exposure_speed}')
available_shutter_speeds = [0, 1, 10, 30, 50, 100, 1000, 10000, 100000]

for shutter_speed in available_shutter_speeds:
  filename = f'{manual_dir}/{frame_count}_shutter_speed_{shutter_speed}{filetype}'
  print(filename)

  camera.shutter_speed(shutter_speed)
  camera.capture(filename, format=format)

camera.shutter_speed(0)

# exposure / white balance
print('=======================================================================')
print("exposure_compensation")
# When queried, the exposure_compensation property returns an integer value
# between -25 and 25 indicating the exposure level of the camera. Larger values result in brighter images.
available_exposure_compensations = [-25, -20, -15, -10, -5, 0, 5, 10, 15, 20, 25]

for exposure_compensation in available_exposure_compensations:
  filename = f'{manual_dir}/{frame_count}_exposure_compensation_{exposure_compensation}{filetype}'
  print(filename)

  camera.exposure_compensation(exposure_compensation)
  camera.capture(filename, format=format)

camera.exposure_compensation(0)

print('=======================================================================')
print("exposure_mode")
# Retrieves or sets the exposure mode of the camera.

# When queried, the exposure_mode property returns a string representing
# the exposure setting of the camera. The possible values can be obtained from the PiCamera.EXPOSURE_MODES

# Exposure mode 'off' is special: this disables the camera’s automatic gain control,
# fixing the values of digital_gain and analog_gain. Please note that these properties are not directly settable,
# and default to low values when the camera is first initialized.
# Therefore it is important to let them settle on higher values before disabling
# automatic gain control otherwise all frames captured will appear black.

print(f'digital_gain: {camera.digital_gain}')
print(f'analog_gain: {camera.analog_gain}')
available_exposure_modes = ['off', 'auto', 'night', 'nightpreview', 'backlight', 'spotlight', 'sports', 'snow', 'beach', 'verylong', 'fixedfps', 'antishake', 'fireworks']

for exposure_mode in available_exposure_modes:
  filename = f'{manual_dir}/{frame_count}_exposure_mode_{exposure_mode}{filetype}'
  print(filename)

  camera.exposure_mode(exposure_mode)
  camera.capture(filename, format=format)

camera.exposure_mode('auto')

# image_denoise
print('=======================================================================')
print("image_denoise")
# image_denoise # Default is True
filename = f'{manual_dir}/{frame_count}_denoise_{false}{filetype}'
print(filename)
camera.image_denoise(False)
camera.capture(filename, format=format)

filename = f'{manual_dir}/{frame_count}_denoise_{true}{filetype}'
print(filename)
camera.image_denoise(True)
camera.capture(filename, format=format)

# effect
print('=======================================================================')
print("image_effect")

available_effects = ['none', 'negative', 'solarize', 'sketch', 'denoise', 'emboss', 'oilpaint', 'hatch', 'gpen', 'pastel', 'watercolor', 'film', 'blur', 'saturation', 'colorswap', 'washedout', 'posterise', 'colorpoint', 'colorbalance', 'cartoon', 'deinterlace1', 'deinterlace2']
for image_effect in available_effects:
  filename = f'{manual_dir}/{frame_count}_effect_{image_effect}{filetype}'
  print(filename)

  camera.image_effect(image_effect)
  camera.capture(filename, format=format)

camera.image_effect('none')

# drc_strength
print('=======================================================================')
print("drc_strength")
available_drc_strengths = ['off', 'low', 'medium', 'high']
for drc_strength in available_drc_strengths:
  filename = f'{manual_dir}/{frame_count}_drc_strength_{drc_strength}{filetype}'
  print(filename)

  camera.drc_strength(drc_strength)
  camera.capture(filename, format=format)

camera.drc_strength('off')

# contrast
print('=======================================================================')
print("contrast")
# -100 and 100, default is 0
available_contrasts = [-100, -80, -60, -40, -20, 0, 20, 40, 60, 80, 100]
for contrast in available_contrasts:
  filename = f'{manual_dir}/{frame_count}_contrast_{contrast}{filetype}'
  print(filename)

  camera.contrast(contrast)
  camera.capture(filename, format=format)

camera.contrast(0)

# brightness
print('=======================================================================')
print("brightness")
# 0 and 100, default is 50
available_brightnesses = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
for brightness in available_brightnesses:
  filename = f'{manual_dir}/{frame_count}_brightness_{brightness}{filetype}'
  print(filename)

  camera.brightness(brightness)
  camera.capture(filename, format=format)

camera.brightness(50)

print('Much Success!')
