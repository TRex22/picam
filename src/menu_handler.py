import overlay_handler
import camera_handler

def select_menu_item(camera, config):
  idex = config["available_menu_items"].index(config["menu_item"]) + 1

  if idex < len(config["available_menu_items"]):
    config["menu_item"] = config["available_menu_items"][idex]
  else:
    config["menu_item"] = config["default_menu_item"]

  overlay_handler.display_text(camera, '', config)
  print(f'menu_item: {config["menu_item"]}')

def select_option(camera, config):
  if config["menu_item"] == "auto":
    camera.iso = config["default_iso"]
    camera.exposure_mode = config["default_exposure_mode"]
  if config["menu_item"] == "exposure_mode":
    camera_handler.adjust_exposure_mode(camera, config)
  if config["menu_item"] == "iso":
    camera_handler.adjust_iso(camera, config)
  if config["menu_item"] == "hdr":
    camera_handler.set_hdr(camera, config)
  if config["menu_item"] == "video":
    camera_handler.set_video(camera, config)
  if config["menu_item"] == "encoding":
    camera_handler.adjust_encoding(camera, config)
