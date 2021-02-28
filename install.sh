#!/bin/bash
# Version 0.1
# TODO: Check configurations exist
# TODO: Automated rpi config

cd ~/
# Setup:
# [] WLAN
# [] Auto login - Console
# [] Wait for network No
# [] Camera Interface Enable
# [] SSH Enable
# [] SPI Enable
# [] I2C Enable
# [] 200mb GPU memory
# [] OC?
# [] RTC
# [] Expand File-system
sudo raspi-config
mkdir -p ~/DCIM

sudo apt update
sudo apt install -y samba samba-common git build-essential cmake python3 python3-pip libopencv-dev python-opencv python-picamera python3-picamera libatlas-base-dev libhdf5-dev libhdf5-serial-dev libatlas-base-dev libjasper-dev libqtgui4 libqt4-test libatlas-base-dev libxml2-dev libxslt-dev

pip3 install opencv-contrib-python numpy ExifRead
sudo pip3 install Click==7.0
sudo pip3 install adafruit-python-shell

git clone https://github.com/TRex22/PyDNG.git
git clone https://github.com/TRex22/Colour_Profiles.git
git clone https://github.com/tasanakorn/rpi-fbcp.git
git clone https://github.com/adafruit/Raspberry-Pi-Installer-Scripts.git
git clone https://github.com/TRex22/picam.git

pip3 install ~/PyDNG/src/.

# rpi-fbcp
cd ~/rpi-fbcp
mkdir ~/rpi-fbcp/build
cd ~/rpi-fbcp/build
cmake ..
make
sudo cp fbcp /usr/bin
cd ~/

# adafruit screen
# https://learn.adafruit.com/adafruit-2-2-pitft-hat-320-240-primary-display-for-raspberry-pi
# https://learn.adafruit.com/adafruit-2-2-pitft-hat-320-240-primary-display-for-raspberry-pi/easy-install
cd ~/Raspberry-Pi-Installer-Scripts
# sudo python3 adafruit-pitft.py --display=22 --rotation=90 --install-type=console
sudo python3 adafruit-pitft.py --display=22 --rotation=90 --install-type=fbcp --reboot=no
cd ~/

# User boot
# picam
tee -a ~/.bashrc << EOF
/usr/bin/fbcp &
python /home/pi/picam/test/camera_test.py
EOF

# Hostname
sudo tee -a /etc/hosts << EOF
127.0.0.1   picam
EOF

sudo tee /etc/hostname << EOF
picam
EOF

# Samba
sudo systemctl stop smbd
sudo systemctl stop nmbd

sudo tee -a /etc/samba/smb.conf << EOF
[DCIM]
  comment = DCIM
  path = /home/pi/DCIM
  browseable = yes
  read only = no
  guest ok = yes
EOF

sudo systemctl start smbd
sudo systemctl start nmbd

sudo reboot
