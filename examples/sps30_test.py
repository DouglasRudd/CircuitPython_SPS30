import board
import busio
import sensiron_sps30
import time

i2c = busio.I2C(board.SCL, board.SDA)

sps30 = sensiron_sps30.SPS30(i2c)

print(sps30.getSerialNumber())
sps30.startMeasurement()

time.sleep(2)
while True:
    for key, value in sps30.readMeasurement().items():
        print("{} : {}".format(key, value))
    
    time.sleep(2)