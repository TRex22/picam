# https://stackoverflow.com/questions/30135091/write-thread-safe-to-file-in-python

from threading import Thread
from thread_writer import ThreadWriter
from pydng.core import RPICAM2DNG
import document_handler

class ThreadRawConverter:
  def __init__(self, config, stream, filename):
    self.config = config
    self.json_colour_profile = document_handler.load_colour_profile(config)
    self.filename = filename
    self.stream = stream

    self.finished = False
    self.thread_writer = ThreadWriter(self.filename, 'wb')

    Thread(name = "ThreadRawConverter", target=self.internal_converter).start()

  def internal_converter(self):
    while not self.finished:
      if self.stream != None:
        RPICAM2DNG().convert(self.stream, json_camera_profile=self.json_colour_profile)
        self.thread_writer.write(self.output)
        self.finished = True
        self.thread_writer.close()
