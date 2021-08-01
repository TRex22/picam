import RPi.GPIO as GPIO

# Modules
import overlay_handler
import camera_handler
import menu_handler

# Set Globals to be used by the callbacks - I know this is very ugly
global config
global camera
global overlay

# GPIO Stuff - Needs to be in the same context as camera
def button_callback_1(channel):
  print("Button 1: Menu")
  global camera
  global overlay
  global config

  menu_handler.select_menu_item(camera, config)

def button_callback_2(channel):
  print("Button 2: Option")
  global camera
  global overlay
  global config

  menu_handler.select_option(camera, config)

def button_callback_3(channel):
  print("Button 3: Zoom")
  global camera
  global overlay
  global config

  camera_handler.zoom(camera, config)
  overlay = overlay_handler.add_overlay(camera, overlay, config)

def button_callback_4(channel):
  print("Button 4: Take shot")
  global camera
  global overlay
  global config

  overlay_handler.remove_overlay(camera, overlay, config)
  overlay = None

  if config["video"]:
    camera_handler.trigger_video(camera, config)
  else:
    if config["hdr"]:
      camera_handler.take_hdr_shot(camera, config)
    else:
      camera_handler.take_single_shot(camera, config)

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

  GPIO.add_event_detect(button_1, GPIO.RISING, callback=button_callback_1, bouncetime=bouncetime)
  GPIO.add_event_detect(button_2, GPIO.RISING, callback=button_callback_2, bouncetime=bouncetime)
  GPIO.add_event_detect(button_3, GPIO.RISING, callback=button_callback_3, bouncetime=bouncetime)
  GPIO.add_event_detect(button_4, GPIO.RISING, callback=button_callback_4, bouncetime=bouncetime)

def stop_button_listen():
  GPIO.cleanup() # Clean up
