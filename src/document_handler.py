import os
import json

# TODO: Write a better folder presence checker based off other work
def check_for_folders(config):
  detect_or_create_folder(config["dcim_images_path_raw"])
  detect_or_create_folder(config["dcim_original_images_path"])
  detect_or_create_folder(config["dcim_hdr_images_path"])
  detect_or_create_folder(config["dcim_videos_path"])

def detect_or_create_folder(folder_path, print_error=False):
  try:
    os.mkdir(folder_path)
  except OSError as error:
    if (print_error): print(error)

def load_colour_profile(config):
  json_colour_profile = None

  with open(config["colour_profile_path"], "r") as file_stream:
    json_colour_profile = json.load(file_stream)

  return json_colour_profile
