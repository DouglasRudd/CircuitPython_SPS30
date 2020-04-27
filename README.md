# CircuitPython_SPS30

CircuitPython driver for the [Sensiron SPS 30](https://www.sensirion.com/en/environmental-sensors/particulate-matter-sensors-pm25/)

### Usage
Copy Sensiron_sps30.py to your CircuitPython device.
See sps30_test.py for an example implementation.

### Example Output
```
Mass Concentration PM 1.0 [ug/m3] : 1.06156
Mass Concentration PM 2.5 [ug/m3] : 1.11157
Mass Concentration PM 4.0 [ug/m3] : 1.12688
Mass Concentration PM 10 [ug/m3] : 1.13172
Number Concentration PM 0.5 [#/m3] : 8.11561
Number Concentration PM 1.0 [#/m3] : 9.19413
Number Concentration PM 2.5 [#/m3] : 9.23619
Number Concentration PM 4.0 [#/m3] : 9.23938
Number Concentration PM 10 [#/m3] : 9.24018
Typical Particle Size [um] : 0.601643
```

### Special Thanks to:
* UnravelTec for their [RaspberryPi implementation](https://github.com/UnravelTEC/Raspi-Driver-SPS30)
* Adafruit for CircuitPython/I2C libraries
