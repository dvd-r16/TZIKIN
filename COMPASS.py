import smbus2
import time
import math

bus = smbus2.SMBus(1)
address = 0x1e
def read_word(adr):
    high = bus.read_byte_data(address, adr)
    low = bus.read_byte_data(address, adr+1)
    val = (high << 8) + low
    if val >= 32768:
        val = val - 65536
    return val

def head_heading():
    bus.write_byte_data(address, 0x02, 0x00)
    time.sleep(0.06)
    x_out = read_word(0x03) 
    y_out = read_word(0x07)
    heading = math.atan2(y_out, x_out) * (180 / math.pi) + 180
    return heading

while True:
    heading = head_heading()
    print(f"Compass Heading: {heading} degrees")
    time.sleep(1)