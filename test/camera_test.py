import os
import time
import glob

from picamera import PiCamera
# from gpiozero import Button
import RPi.GPIO as GPIO

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
dcim_images_path = '/home/pi/DCIM/images'
dcim_videos_path = '/home/pi/DCIM/videos'

try:
  os.mkdir(dcim_images_path)
except OSError as error:
  print(error)

try:
  os.mkdir(dcim_videos_path)
except OSError as error:
  print(error)

camera = PiCamera()
# camera.resolution = (w, h)
# camera.brightness = step

# 8MP pi camera v2.1
# w = 3280
# h = 2464

screen_w = 320
screen_h = 240

# 12MP Pi HQ camera
w = 4056
h = 3040

# camera.resolution = (w, h)

# Preview
def preview(camera, zoom=False):
  if zoom == True:
    camera.zoom = (0.4,0.4,0.2,0.2)

  camera.start_preview()
  time.sleep(10)
  # camera.capture(filename)
  camera.stop_preview()

def button_callback_1(channel):
  camera.stop_preview()
  print("Button 1 was pushed!")

  existing_files = glob.glob(f'{dcim_images_path}/*{filetype}')
  filecount = len(existing_files)
  frame_count = filecount

  filename = f'{dcim_images_path}/{frame_count}{filetype}'
  print(filename)

  camera.resolution = (w, h)
  camera.capture(filename)

  camera.resolution = (screen_w, screen_h)
  camera.start_preview()

def button_callback_2(channel):
  print("Button 2 was pushed!")

def button_callback_3(channel):
  print("Button 3 was pushed!")

def button_callback_4(channel):
  print("Button 4 was pushed!")

# button_1 = 13 # 27
# button_2 = 16 # 23
# button_3 = 15 # 22
# button_4 = 11 # 17

# button_1 = 20 # 27
# button_2 = 16 # 23
# button_3 = 15 # 22
# button_4 = 10 # 17

button_1 = 27
button_2 = 23
button_3 = 22
button_4 = 17

GPIO.setwarnings(False) # Ignore warning for now
GPIO.setmode(GPIO.BOARD) # Use physical pin numbering
# GPIO.setmode(GPIO.BCM) # Use physical pin numbering

GPIO.setup(button_1, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(button_2, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(button_3, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(button_4, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

GPIO.add_event_detect(button_1, GPIO.RISING, callback=button_callback_1)
GPIO.add_event_detect(button_2, GPIO.RISING, callback=button_callback_2)
GPIO.add_event_detect(button_3, GPIO.RISING, callback=button_callback_3)
GPIO.add_event_detect(button_4, GPIO.RISING, callback=button_callback_4)

camera.resolution = (screen_w, screen_h)
camera.start_preview()

message = input("Press enter to quit\n\n") # Run until someone presses enter
camera.stop_preview()
GPIO.cleanup() # Clean up