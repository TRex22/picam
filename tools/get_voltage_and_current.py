# IMPORT THE LIBERARY.
# See: https://wiki.52pi.com/index.php/UPS_(With_RTC_%26_Coulometer)_For_Raspberry_Pi_SKU:_EP-0118#Using_Overlays
from ina219 import INA219
from ina219 import DeviceRangeError
SHUNT_OHMS = 0.05


def read():
    """Define method to read information from coulometer."""
    ina = INA219(SHUNT_OHMS)
    ina.configure()
    print("Bus Voltage: %.3f V" % ina.voltage())
    try:
        print("Bus Current: %.3f mA" % ina.current())
        print("Power: %.3f mW" % ina.power())
        print("Shunt voltage: %.3f mV" % ina.shunt_voltage())
    except DeviceRangeError as e:
        print(e)

if __name__ == "__main__":
    read()
