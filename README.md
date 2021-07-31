# PiCam
RaspberryPi Camera project to create a software and hardware stack to build your own professional style camera.
My test model of the platform is called JankyCam.

I hope that this project will inspire others to help contribute and eventually make something everyone can use to gain access to the world of photography and lenses beyond just mobile phones. Also for this to be used as a platform for computational photography and experimentation/learning.

This is still early days and requires a lot of work before its easy to use.

# Requirements
- opencv-python
- numpy
- picamerax
- libavcodec
- pip3
- sudo apt-get install libopencv-dev python-opencv python-picamera
- pip3 install opencv-contrib-python
- sudo apt-get install -y libatlas-base-dev libhdf5-dev libhdf5-serial-dev libatlas-base-dev libjasper-dev  libqtgui4  libqt4-test
- sudo apt-get install libatlas-base-dev libxml2-dev libxslt-dev

# Other tools
## PiCam experimental viewfinder
```
/usr/bin/fbcp &
raspivid -t 3000000000
```

# RAW support
```
# git clone https://github.com/schoolpost/PyDNG.git
git clone https://github.com/TRex22/PyDNG.git # Use the fork for now
cd PyDNG

# install
pip3 install src/.

# Colour profiles
# git clone https://github.com/davidplowman/Colour_Profiles.git
git clone https://github.com/trex22/Colour_Profiles.git
```

# dcamprof dcp to json conversion
https://torger.se/anders/dcamprof.html#download

```
./dcamprof.exe dcp2json "C:/development/Colour_Profiles/imx477/Raspberry Pi High Quality Camera Lumariver 2860k-5960k Skin+Sky Look.dcp" "C:/development/Colour_Profiles/imx477/Raspberry Pi High Quality Camera Lumariver 2860k-5960k Skin+Sky Look.json"

./dcamprof.exe dcp2json "C:/development/Colour_Profiles/imx477/Raspberry Pi High Quality Camera Lumariver 2860k-5960k Neutral Look.dcp" "C:/development/Colour_Profiles/imx477/Raspberry Pi High Quality Camera Lumariver 2860k-5960k Neutral Look.json"
```

# TODO List:
  - histograms
  - profiles
  - logging
  - Focus assist
  - Astral-photography modes
  - Face detection
  - Contrast Hist
  - Edge detect algo
  - Camera Intrinsics tool
  - Web control
  - Motion vectors
  - Improve tools
  - Cleanup test
  - Write actual tests
  - Histogram and analysis tools
  - RAW sensor capture: https://raspberrypi.stackexchange.com/questions/51191/how-can-i-stop-the-overlay-of-images-between-my-pi-camera-and-flir-camera
  - Resolution (FPS as label)
  - FPS option (wrt resolution)
  - Menus
  - Proper overlay
  - Audio?
  - sharpness
  - Contrast
  - brightness
  - saturation
  - ev compression
  - awb - auto white balance
  - image effect
  - colour effect
  - metering mode?
  - roi
  - dynamic range compression
  - image statistics
  - awb gains
  - sensor input mode??? / video
  - bitrate
  - video stabilisation
  - other video options
  - Add zoom to config
  - Lens shading control https://github.com/waveform80/picamera/pull/470
  - Other engines like raspistill and then new gpu pipeline
  - Camera reinitialize and better preview fps
  - https://raspberrypi.stackexchange.com/questions/61427/can-i-set-the-cameras-shutter-speed-for-video
  - Motion MMAL https://www.raspberrypi.org/forums/viewtopic.php?f=43&t=44966&p=1116392&hilit=motion+mmal#p1116392
  - metering modes (average,spot,backlit,matrix)
  - continuous shot
  - stop motion mode
  - astro-photography mode
  - Lens exif data tool
  - Improve tools to be cli
  - python module
  - pyton requirements.txt
  - EXIF copyright info
  - Image watermark tool
  - Photo Viewer
  - 60fps bpp 10 Full
  - DOL-HDR
  - FOM: https://www.raspberrypi.org/forums/viewtopic.php?f=43&t=273804
  - long exposures: https://www.raspberrypi.org/forums/viewtopic.php?t=277689
  - https://www.raspberrypi.org/forums/viewtopic.php?t=275962
  - https://www.raspberrypi.org/forums/viewtopic.php?t=275962
  - https://www.raspberrypi.org/forums/viewtopic.php?t=279752
  - Star Eater: https://photo.stackexchange.com/questions/116765/new-pi-camera-any-good-for-astrophotography
  - https://www.raspberrypi.org/forums/viewtopic.php?f=43&t=277768
  - https://github.com/raspberrypi/userland/blob/3fd8527eefd8790b4e8393458efc5f94eb21a615/interface/mmal/mmal_parameters_camera.h
