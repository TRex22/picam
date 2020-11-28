# picam
RaspberryPi Camera software to be used with a screen module.

# Requirements
- opencv-python
- numpy
- picamera
- libavcodec
- pip3
- sudo apt-get install libopencv-dev python-opencv python-picamera
- pip3 install opencv-contrib-python
- sudo apt-get install -y libatlas-base-dev libhdf5-dev libhdf5-serial-dev libatlas-base-dev libjasper-dev  libqtgui4  libqt4-test
- sudo apt-get install libatlas-base-dev libxml2-dev libxslt-dev
- pip install clairmeta

# Other tools
## PiCam experimental viewfinder
```
/usr/bin/fbcp &
raspivid -t 3000000000
```

# RAW support
```
git clone https://github.com/schoolpost/PyDNG.git
cd PyDNG

# install
pip3 install src/.

# Colour profiles
git clone https://github.com/davidplowman/Colour_Profiles.git
```