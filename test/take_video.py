import time
import glob

from picamera import PiCamera

filetype = '.h264'
dcim_images_path = '/home/pi/DCIM/images'
dcim_videos_path = '/home/pi/DCIM/videos'

existing_files = glob.glob(f'{dcim_videos_path}/*{filetype}')
filecount = len(existing_files)
frame_count = filecount + 1

camera = PiCamera()

camera.start_preview()
camera.start_recording(f'{dcim_videos_path}/{frame_count}{filetype}')
time.sleep(15)
camera.stop_recording()
camera.stop_preview()
