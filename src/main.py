# Notes:
# For fixing multi-press See: https://raspberrypi.stackexchange.com/questions/28955/unwanted-multiple-presses-when-using-gpio-button-press-detection

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

# available_exposure_compensations = [-25, -20, -15, -10, -5, 0, 5, 10, 15, 20, 25]

# HQ Camera on-sensor defective pixel correction (DPC)
# https://www.raspberrypi.org/forums/viewtopic.php?f=43&t=277768
# 0 - All DPC disabled.
# 1 - Enable mapped on-sensor DPC.
# 2 - Enable dynamic on-sensor DPC.
# 3 - Enable mapped and dynamic on-sensor DPC.

# The default is (3). It would be useful to get feedback from users who do astrophotography if disabling DPC actually makes a difference or not.

# Note that this does not disable the ISP defective pixel correction that will still be active, so you will likely only see changes in the RAW image.

# 8MP pi camera v2.1
# width = 3280
# height = 2464

# 12MP Pi HQ camera
# width = 4056
# height = 3040

VERSION = "0.0.33"

# Modules
import document_handler
import camera_handler

################################################################################
##                                    Config                                  ##
################################################################################
config = {
  "colour_profile_path": "/home/pi/Colour_Profiles/imx477/Raspberry Pi High Quality Camera Lumariver 2860k-5960k Neutral Look.json",
  "dcim_path": 'home/pi/DCIM',
  "dcim_images_path_raw": '/home/pi/DCIM/images/raw',
  "dcim_original_images_path": '/home/pi/DCIM/images/original',
  "dcim_hdr_images_path": '/home/pi/DCIM/images/hdr',
  "dcim_videos_path": '/home/pi/DCIM/videos',
  "dcim_tmp_path": '/home/pi/DCIM/tmp',
  "filetype": '.dng',
  "bpp": 12,
  "format": 'jpeg',
  "video_format": 'h264', # mjpeg, h264 TODO: Make into an option
  "bayer": True,
  "delay_time": 0,
  "delay_times": [0, 1, 2, 5, 10], # in seconds
  "short_delay": False,
  "short_delay_time": 0.05,
  "min_fps": 0.005, # mode 3 for HQ cam is between 0.005 and 10 fps
  "max_fps": 40, # 40, # Possibly equal to screen_fps
  "screen_fps": 40, # 120 fps at 1012x760
  "capture_timeout": 1000, # Must be greater than max exposure in seconds
  "screen_w": 1280, # 1024 # 1012 # 320 screen res # Needs to be 4:3
  "screen_h": 960, # 768 #760 # 240 screen res # Needs to be 4:3
  "overlay_w": 320,
  "overlay_h": 240,
  "width": 4056, # Image width
  "height": 3040, # Image height
  "video_width": 4056,
  "video_height": 3040,
  "annotate_text_size": 48, # 6 to 160, inclusive. The default is 32
  "exposure_mode": 'auto',
  "default_exposure_mode": 'auto',
  "default_zoom": (0.0, 0.0, 1.0, 1.0),
  "set_zoom": '1x',
  "max_zoom": (0.4, 0.4, 0.2, 0.2),
  "max_zoom_2": (0.4499885557335775, 0.4499885557335775, 0.09999237048905166, 0.09999237048905166),
  "max_zoom_3": (0.5, 0.5, 0.05, 0.05),
  "available_exposure_modes": [
    "auto", # default has to be first in the list
    "off",
    "verylong",
    "fixedfps",
    "antishake",
    "night",
    "nightpreview",
    "backlight",
    "spotlight",
    "sports",
    "snow",
    "beach",
    "fireworks"
  ],
  "available_isos": [0, 5, 10, 25, 50, 100, 200, 320, 400, 500, 640, 800, 1600], # 0 is auto / 3200, 6400
  "iso": 5, #0, # 800 / should shift to 0 - auto
  "default_iso": 5,
  "available_shutter_speeds": [0, 100, 500, 1000, 1500, 2000, 4000, 8000, 16667, 33333, 66667, 125000, 250000, 500000, 1000000], # 1/10000, 1/2000, 1/1000, ...
  "available_long_shutter_speeds": [0, 1000000, 2000000, 3000000, 4000000, 5000000, 10000000, 15000000, 20000000, 25000000, 30000000, 35000000, 40000000, 200000000],
  "take_long_shutter_speed": False,
  "shutter_speed": 0,
  "long_shutter_speed": 0,
  "default_shutter_speed": 0,
  "available_awb_mode": ['auto', 'off', 'sunlight', 'cloudy', 'shade', 'tungsten', 'fluorescent', 'incandescent', 'flash', 'horizon'],
  "awb_mode": 'auto',
  "default_awb_mode": 'auto', # "awb_gains": 0.0 - 8.0 (),
  "dpc": 0, # 0 - 3, default is 3 and 0 is disabled
  "default_dpc": 0,
  "raw_convert": True,
  "available_dpc_options": [0, 1, 2, 3], #https://www.raspberrypi.org/forums/viewtopic.php?f=43&t=277768
  "current_menu_items": ["auto", "shutter_speed", "iso", "hdr2", "delay_time", "long_shutter_speed", "sub_menu"],
  "available_menu_items": ["auto", "shutter_speed", "iso", "hdr2", "delay_time", "long_shutter_speed", "sub_menu"],
  "available_sub_menu_items": ["exposure_mode", "awb_mode", "hdr", "video", "resolution", "encoding", "dpc - star eater", "raw_convert", "fom"],
  "menu_item": "auto",
  "default_menu_item": "auto",
  "hdr": False,
  "preview": True,
  "fom": False,
  "default_fom": True,
  "fom_overlay_x_padding": 50, # in pixels
  "fom_overlay_y_padding": 50, # in pixels
  "hdr2": False,
  "preview_mode": "built-in", # "built-in" "continuous_shot"
  "default_preview_mode": 'built-in',
  "video": False,
  "recording": False,
  "encoding": False, # TODO
  "gpio": {
    "button_1": 27,
    "button_2": 23,
    "button_3": 22,
    "button_4": 17,
    "bouncetime": 450
  }
}

document_handler.check_for_folders(config)

################################################################################
#                                  Main Loop                                   #
################################################################################

# Begin Camera start-up
camera, overlay = camera_handler.start_camera(config) # Runs main camera loop
message = input("Press enter to quit\n\n") # Run until someone presses enter

print('Stop camera!')
camera_handler.stop_camera(camera, overlay, config)
