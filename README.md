# picam
RaspberryPi Camera software to be used with a screen module.

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

# dcamprof
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
  - ISO
  - Shutter Speed
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
  - exposure mode
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
