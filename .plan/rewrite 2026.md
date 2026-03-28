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


# Updates

Please make sure that shutter speeds that would make the preview unusable dont change the preview (too slow shutter speeds) and rather use a simulated preview. Thats important for setting up long exposures. I also want a reset settings button for going back to the configured default quickly. With a plan for future saved profiles that can be applied quickly. Like for astrophotography (moon, or planet or long exposure star shots).

I want to have planned out tests and CI/CD workflow. With AI reviewer and security reviews. Use /Users/trex22/development/artemis as an example of such an implementation.

Also plan for repo cleanup. I will tag v1.5 and then want to clear development and master branches and start fresh with the new implementation.

I'd like to keep some support for the older screen and gpio buttons if I build out a smaller cheaper model in the future. This should be planned for.

Plan for future UI themes, colours and fonts

Plan for an image and video gallery view in the future. This way captured images can be viewed and zoomed on in real-time.

Plan for a feature where the current lens can be manually selected from a manually updated database of available lenses and lens configurations. This would then be saved in the EXIF data.

multi-sensor and dual sensor support is the same thing. Combine them. Allow for up to two previews at the same time with a way to scroll through available sensors.

DPC and other sensor registry controls which were toggled in the older version of the app should be available in the new version.

GPS support is the lowest priority feature.

Timer delay is actually very important to have earlier on
Ive done some image processing work in this tool: /Users/trex22/development/MagicForge

Also add in a manual focus bracketing continuous shot feature

remote control I was thinking a bluetooth HID device, or remote web access. Not IR.



