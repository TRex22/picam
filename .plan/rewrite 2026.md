# Prompt
Please help generate a plan to migrate my picam project from v1.5 which is on developemnt branch of the repo here: /Users/trex22/development/picam to a new re-written V2. I have a proof of concept attached to the prompt which implements a simple UI and threaded model of rapsberry pi camera. The original version used a framebuffer copy screen, gpio buttons, console output with no desktop on a pi4. This version uses a pi5 and a DSP touch screen. Im still working on the 3d modelling and case options.

Below is a list of features I want and also a review / fix list for the proof of concept. Ive also attached pictures of the UI on the screen.

The biggest missing feature is around the custom colour profile I have from the IMX477 sensor. I want to support other sensors too but Ive got a custom more accurate colour profile I'd like to use by default for that sensor.

# Feature Wishlist
[] Battery Control
[] Different Screen support (HDMI, DSP, FrameBuffer)
[] Save png / jpeg / save options that can have dual save
[] Colour profiles including my custom one (https://github.com/trex22/Colour_Profiles.git)
[] Multi-Sensor support including ArduCam ones like the autofocus module
[] Dual sensor support
[] AWB settings
[] Install script
[] Able to mount as camera in Darktable or Image Capture (on mac)
[] Samba support
[] Darktable install on device
[] Raspberry Pi 4 and 5 support
[] Auto login and run
[] Touch Screen Zoom with pinch and expand focus window
[] Timer Delay
[] Video Support
[] RAW Video Support
[] Auto Mode
[] Shutter Speed Simulation in Preview
[] Screen brightness control
[] Battery percentage tracking
[] Focus support tools like zebra and dots
[] Remote control support
[] Audio input (mic) support
[] Better cage stl models with handles
[] Settings can map GPIO buttons dynamically
[] bitrate controls
[] Model selection controls
[] Temp monitoring
[] in-memoyr buffer (using ramdrive?) The pi 5 has 8GB of ram.

# Optimisation List
[] Fast Boot
[] Power optimisation
[] Fix physical battery pack issues

# Proof Of Concept Review and Improvements
[] Raw EXIF data improvements (Actual date timestamp, Custom camera name, metadata describing raspberrypi and connected sensor)
[] GPS support (if data available). As a setting
[] Settings file
[] Default boot state of settings
[] Clear text for drop downs
[] Preview needs to be exact aspect of camera output
[] white balance controls
[] focus window the mouse can drag and resize
[] zoom using focus window
[] proper fullscreen
[] Indication that a picture has been taken
[] Embed colour profile into raw output
[] Have option to save as RAW and JPEG or PNG

There is also an older todo list in the folder ./plan/ in the repo: /Users/trex22/development/picam to also evaluate.

Make this plan markdown
