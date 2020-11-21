import time
import glob

from picamera import PiCamera

filetype = '.h264'
dcim_images_path = '/home/pi/DCIM/images'
dcim_videos_path = '/home/pi/DCIM/videos'

existing_files = glob.glob(f'{dcim_videos_path}/*{filetype}')
filecount = len(existing_files)
frame_count = filecount + 1

# Available formats: https://picamera.readthedocs.io/en/release-1.10/api_camera.html#picamera.camera.PiCamera.capture
# 'h264' - Write an H.264 video stream
# 'mjpeg' - Write an M-JPEG video stream
# 'yuv' - Write the raw video data to a file in YUV420 format
# 'rgb' - Write the raw video data to a file in 24-bit RGB format
# 'rgba' - Write the raw video data to a file in 32-bit RGBA format
# 'bgr' - Write the raw video data to a file in 24-bit BGR format
# 'bgra' - Write the raw video data to a file in 32-bit BGRA format

format = 'h264'

camera = PiCamera()

filename = f'{dcim_videos_path}/{frame_count}{filetype}'
print(filename)

# camera.start_preview()
camera.start_recording(filename, format=format)
time.sleep(15)
camera.stop_recording()
# camera.stop_preview()
