#!env python3

import struct 
with open("/dev/input/mouse0", "rb") as f:
    x = 0
    y = 0
    while True:
        data = f.read(3)
        status, dx, dy = struct.unpack('3b', data)
        x += dx
        y += dy
        print(x, y)
