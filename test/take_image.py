import time
import glob

from picamera import PiCamera

filetype = '.tiff'
dcim_images_path = '/home/pi/DCIM/images'
dcim_videos_path = '/home/pi/DCIM/videos'

existing_files = glob.glob(f'{dcim_images_path}/*{filetype}')
filecount = len(existing_files)
frame_count = filecount + 1

camera = PiCamera()
# camera.resolution = (w, h)
# camera.brightness = step

camera.start_preview()
# time.sleep(10)
camera.capture(f'{dcim_images_path}/{frame_count}{filetype}')
camera.stop_preview()