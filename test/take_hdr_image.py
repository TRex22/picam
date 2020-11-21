import time
import glob

from picamera import PiCamera

filetype = '.tiff'

dcim_hdr_images_path = '/home/pi/DCIM/hdr_images'
dcim_images_path = '/home/pi/DCIM/images'
dcim_videos_path = '/home/pi/DCIM/videos'

existing_files = glob.glob(f'{dcim_hdr_images_path}/*{filetype}')
filecount = len(existing_files)
frame_count = filecount + 1

camera = PiCamera()
# camera.resolution = (w, h)
# camera.brightness = step

# SEE: https://github.com/KEClaytor/pi-hdr-timelapse
nimages = 10 #2160
exposure_min = 10
exposure_max = 90
exp_step = 5
# w = 800
# h = 600

exp_step = (exposure_max - exposure_min) / (nimages - 1)
exposures = range(exposure_min, exposure_max + 1, exp_step)

fnames = []
for step in exposures:
  # Set filename based on exposure
  fname = f'{dcim_hdr_images_path}/{frame_count}_{step}_HDR_{filetype}' # 'e%d.jpg' % (step)
  fnames.append(fname)
  # Set camera properties and capture
  camera.brightness = step
  camera.capture(fname)