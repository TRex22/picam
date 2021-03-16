import os

def check_for_folders(config):
  try:
    os.mkdir(config["dcim_images_path"])
  except OSError as error:
    print(error)

  try:
    os.mkdir(config["dcim_original_images_path"])
  except OSError as error:
    print(error)

  try:
    os.mkdir(config["dcim_hdr_images_path"])
  except OSError as error:
    print(error)

  try:
    os.mkdir(config["dcim_videos_path"])
  except OSError as error:
    print(error)

def load_colour_profile(config):
  json_colour_profile = None

  with open(colour_profile_path, "r") as file_stream:
    json_colour_profile = json.load(file_stream)

  return json_colour_profile
