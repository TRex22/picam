import os
import time
import glob

from picamera import PiCamera

from io import BytesIO
import numpy as np
from pydng.core import RPICAM2DNG
from pydng.core import RAW2DNG, DNGTags, Tag

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

filetype = '.dng'
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

# Used sample from: https://github.com/schoolpost/PyDNG/blob/master/examples/raw2dng.py
existing_files = glob.glob(f'{dcim_images_path}/*{filetype}')
filecount = len(existing_files)
frame_count = filecount

camera = PiCamera()
# camera.resolution = (w, h)
# camera.brightness = step

# 8MP pi camera v2.1
# w = 3280
# h = 2464

# 12MP Pi HQ camera
# RAW image specs
width = 4096
height = 3072
bpp= 12

# format = 'bgr'
# format = 'yuv'
format = 'jpeg'

# load raw data into 16-bit numpy array.
numPixels = width*height
rawFile = 'extras/scene_daylight_211ms_c2.raw16'
rf = open(rawFile, mode='rb')
rawData = struct.unpack("H"*numPixels,rf.read(2*numPixels))
rawFlatImage = np.zeros(numPixels, dtype=np.uint16)
rawFlatImage[:] = rawData[:]
rawImage = np.reshape(rawFlatImage,(height,width))
rawImage = rawImage >> (16 - bpp)

# calibrated colour matrix
# colour_profile = "/home/pi/DCIM/Colour_Profiles/imx477/PyDNG_profile.dcp"
# colour_profile = "/home/pi/DCIM/Colour_Profiles/imx477/Raspberry Pi High Quality Camera Lumariver 2860k-5960k Skin+Sky Look.dcp"
colour_profile = "/home/pi/DCIM/Colour_Profiles/imx477/Raspberry Pi High Quality Camera Lumariver 2860k-5960k Neutral Look.dcp"
ccm1 = np.load(colour_profile)

# set DNG tags.
t = DNGTags()
t.set(Tag.ImageWidth, width)
t.set(Tag.ImageLength, height)
t.set(Tag.TileWidth, width)
t.set(Tag.TileLength, height)
t.set(Tag.Orientation, 1)
t.set(Tag.PhotometricInterpretation, 32803)
t.set(Tag.SamplesPerPixel, 1)
t.set(Tag.BitsPerSample, bpp)
t.set(Tag.CFARepeatPatternDim, [2,2])
t.set(Tag.CFAPattern, [1, 2, 0, 1])
t.set(Tag.BlackLevel, (4096 >> (16 - bpp)))
t.set(Tag.WhiteLevel, ((1 << bpp) -1) )
t.set(Tag.ColorMatrix1, ccm1)
t.set(Tag.CalibrationIlluminant1, 21)
t.set(Tag.AsShotNeutral, [[1,1],[1,1],[1,1]])
t.set(Tag.DNGVersion, [1, 4, 0, 0])
t.set(Tag.DNGBackwardVersion, [1, 2, 0, 0])
t.set(Tag.Make, "RaspberryPi")
t.set(Tag.Model, "RP_imx477")
t.set(Tag.PreviewColorSpace, 2)

# TODO:
# t.set(Tag.FocalLength, )
# t.set(Tag.35mmFocalLength, 2)
# F-stop
# Exposure bias

stream = BytesIO()

camera.resolution = (width, height)

filename = f'{dcim_images_path}/{frame_count}{filetype}'
print(filename)

# camera.start_preview()
# time.sleep(10)
# camera.capture(filename, format=format)
camera.capture(stream, format, bayer=True)

start_time = time.time()

d = RPICAM2DNG()
# output = d.convert(stream)
output = RAW2DNG().convert(stream, tags=t, filename="custom", path="")

with open(filename, 'wb') as f:
  f.write(output)

print("--- %s seconds ---" % (time.time() - start_time))

# camera.stop_preview()
