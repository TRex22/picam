# https://stackoverflow.com/questions/30135091/write-thread-safe-to-file-in-python

from threading import Thread
from thread_writer import ThreadWriter
from pydng.core import RPICAM2DNG
import document_handler

class ThreadRawConverter:
  def __init__(self, config, filename):
    self.config = config
    self.json_colour_profile = document_handler.load_colour_profile(config)
    self.filename = filename

    self.finished = False
    self.thread_writer = ThreadWriter(self.filename, 'wb')

    Thread(name = "ThreadRawConverter", target=self.internal_converter).start()

  def convert(self, data):
    self.output = RPICAM2DNG().convert(stream, json_camera_profile=json_colour_profile)

  def internal_converter(self):
    while not self.finished:
      try:
        self.output
      except Empty:
        continue

      self.thread_writer.write(self.output)
    
  def close(self):
    self.finished = True
    self.thread_writer.close()
