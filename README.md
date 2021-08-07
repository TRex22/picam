# PiCam
RaspberryPi Camera project to create a software and hardware stack to build your own professional style camera.
My test model of the platform is called JankyCam.

I hope that this project will inspire others to help contribute and eventually make something everyone can use to gain access to the world of photography and lenses beyond just mobile phones. Also for this to be used as a platform for computational photography and experimentation/learning.

This is still early days and requires a lot of work before its easy to use.

# Development branch
I actively work on the ``development` branch - `main` is used for releases only.

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
