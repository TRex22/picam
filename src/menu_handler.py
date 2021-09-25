import overlay_handler
import camera_handler

def select_menu_item(camera, config):
  idex = config["current_menu_items"].index(config["menu_item"]) + 1

  if idex < len(config["current_menu_items"]):
    config["menu_item"] = config["current_menu_items"][idex]
  else:
    config["menu_item"] = config["default_menu_item"]

  overlay_handler.display_text(camera, '', config)
  print(f'menu_item: {config["menu_item"]}')

def select_option(camera, overlay, config):
  if config["menu_item"] == "auto":
    camera_handler.auto_mode(camera, overlay, config)
  if config["menu_item"] == "exposure_mode":
    camera_handler.adjust_exposure_mode(camera, config)
  if config["menu_item"] == "iso":
    camera_handler.adjust_iso(camera, config)
  if config["menu_item"] == "shutter_speed":
    camera_handler.adjust_shutter_speed(camera, config)
  if config["menu_item"] == "long_shutter_speed":
    camera_handler.long_shutter_speed(camera, config)
  if config["menu_item"] == "awb_mode":
    camera_handler.adjust_awb_mode(camera, config)
  if config["menu_item"] == "hdr":
    camera_handler.set_hdr(camera, config)
  if config["menu_item"] == "video":
    camera_handler.set_video(camera, config)
  if config["menu_item"] == "encoding":
    camera_handler.adjust_encoding(camera, config)
  if config["menu_item"] == "dpc - star eater":
    camera_handler.adjust_dpc(config)
    camera_handler.set_dpc(camera, overlay, config)
  if config["menu_item"] == "raw_convert":
    camera_handler.set_raw_convert(camera, config)
  if config["menu_item"] == "fom":
    camera_handler.adjust_fom(camera, config)
    camera_handler.set_fom(camera, config)
  if config["menu_item"] == "hdr2":
    camera_handler.adjust_hdr2(camera, config)
    camera_handler.set_hdr2(camera, config)
  if config["menu_item"] == "delay_time":
    camera_handler.adjust_delay(camera, config)
  if config["menu_item"] == "continuous_shot":
    camera_handler.adjust_shot(camera, config)
  if config["menu_item"] == "sub_menu":
    handle_sub_menu(config)

def handle_sub_menu(config):
  if (config["current_menu_items"] == config["available_menu_items"]):
    config["current_menu_items"] = config["available_sub_menu_items"]
  else:
    config["current_menu_items"] = config["available_menu_items"]

  config["default_menu_item"] = config["current_menu_items"][0]
