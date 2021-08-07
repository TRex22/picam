from picamerax import mmal
from picamerax.mmalobj import to_rational#, to_fraction, to_resolution

# Available conversions
# to_resolution
# to_fraction
# to_rational
# https://gist.github.com/rwb27/a23808e9f4008b48de95692a38ddaa08

def get_mmal_parameter(camera, parameter, type):
  shutter_speed_parameter = mmal.MMAL_PARAMETER_SHUTTER_SPEED
  if parameter == shutter_speed_parameter
    value = MMAL_PARAMETER_UINT32_T.new()
    ret = mmal.mmal_port_parameter_get_rational(camera._camera.control._port, parameter, value)
    print(f'MMAL GET Response: {ret}')
    return value

  if isinstance(type, bool) or type == 'bool':
    value = MMAL_BOOL_T.new()
    ret = mmal.mmal_port_parameter_get_boolean(camera._camera.control._port, parameter, value)
    print(f'MMAL GET Response: {ret}')
    return value
  else:
    value = MMAL_RATIONAL_T.new()
    ret = mmal.mmal_port_parameter_get_rational(camera._camera.control._port, parameter, value)
    print(f'MMAL GET Response: {ret}')
    return value

def set_mmal_parameter(camera, parameter, value):
  if isinstance(value, bool):
    ret = mmal.mmal_port_parameter_set_boolean(camera._camera.control._port, parameter, value)
    print(f'MMAL SET Response: {ret}')
    return ret
  else:
    converted_value = to_rational(value)
    ret = mmal.mmal_port_parameter_set_rational(camera._camera.control._port, parameter, converted_value)
    print(f'MMAL SET Response: {ret}')
    return ret
