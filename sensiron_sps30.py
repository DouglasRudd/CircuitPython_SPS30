import board, busio, struct, time
from collections import OrderedDict
from adafruit_bus_device.i2c_device import I2CDevice


__version__ = ""
__repo__ = ""

class SPS30:
    """Sensiron SPS30 driver.

    Notes: address, crc_init, and crc_poly should likely never need to be modified

    Args:
        i2c_bus (busio.I2C): The i2c bus
        address (int): i2c address of the SPS30 (default 0x69)
        crc_init (int): crc initialization value (default 0xFF)
        crc_poly (int): crc polynomial value (default 0x131)
    """

    def __init__(self, i2c_bus, address=0x69, crc_init=0xFF, crc_poly=0x131):
        self.i2c_device = I2CDevice(i2c_bus, address)
        self.crc_init = crc_init
        self.crc_poly = crc_poly

###############################
#### CRC8 Helper Functions ####
###############################
    
    def calc_crc8(self, byte_array):
        """
        Given an array of bytes calculate the CRC8 checksum.

        Args:
            byte_array (bytearray): The bytes needed to calculate the checksum
        
        Returns:
            crc (int): The calculated CRC8 checksum for the provided bytes
        """
        crc = self.crc_init
        for byte in byte_array:
            crc ^= byte
            for bit in range(8):
                if crc & 0x80 != 0:
                    crc = (crc << 1) ^ self.crc_poly
                else:
                    crc = crc << 1
        return crc

    def validate_crc8(self, byte_array, crc):
        """
        Given an array of bytes and a CRC8 checksum validate that the 
        checksum matches the one created by the bytes.

        Args:
            byte_array (bytearray): The bytes needed to calculate the checksum
            crc (int): The CRC8 checksum to check against

        Returns:
            bool: True if the bytes match the checksum, false if not.
        """
        checksum = self.calc_crc8(byte_array)
        if checksum == crc:
            return True
        else:
            return False

    def parse_crc8(self, byte_array):
        """
            Given a set of bytes, verify that the data matches the 
            CRC8 checksum bytes and provide the raw data without checksums.
        
        Note:
            This function assumes that every two bytes are followed by a checksum byte

        TODO: Provide some better error checking/exception raising
        TODO: Write some better comments about what's going on in the code

        Args:
            byte_array (bytearray): Bytes, with checksum, to verify and decode

        """
        byte_counter = 0
        parsed_byte_array = bytearray()
        temp_byte_array = bytearray(2)

        for byte in byte_array:
            #Check to see if we're looking at the checksum bit
            if byte_counter % 3 != 2:
                temp_byte_array[byte_counter] = byte
                byte_counter += 1
            else:
                byte_counter += 1
                #We're at the checksum bit so let's calculate it and make sure it's right
                if self.validate_crc8(temp_byte_array, byte):
                    parsed_byte_array.extend(temp_byte_array)
                    temp_byte_array = bytearray(2)
                    byte_counter = 0
                #Raise a real error here?
                else:
                    return False
        return parsed_byte_array

################################
#### SPS30 Helper Functions ####
################################

    def calcFloat(self, byte_array):
        #Shamelessly stolen from the UnravelTec driver
        #TODO: Investigate using the struct library for other byte-bashing
        struct_float = struct.pack('>BBBB', byte_array[0], byte_array[1], byte_array[2], byte_array[3])
        return struct.unpack('>f', struct_float)[0]

    def parseMeasurement(self, measurement):
        measurement_obj = OrderedDict()

        measurement_obj["Mass Concentration PM 1.0 [ug/m3]"] = self.calcFloat(measurement[0:4])
        measurement_obj["Mass Concentration PM 2.5 [ug/m3]"] = self.calcFloat(measurement[4:8])
        measurement_obj["Mass Concentration PM 4.0 [ug/m3]"] = self.calcFloat(measurement[8:12])
        measurement_obj["Mass Concentration PM 10 [ug/m3]"] = self.calcFloat(measurement[12:16])

        measurement_obj["Number Concentration PM 0.5 [#/m3]"] = self.calcFloat(measurement[16:20])
        measurement_obj["Number Concentration PM 1.0 [#/m3]"] = self.calcFloat(measurement[20:24])
        measurement_obj["Number Concentration PM 2.5 [#/m3]"] = self.calcFloat(measurement[24:28])
        measurement_obj["Number Concentration PM 4.0 [#/m3]"] = self.calcFloat(measurement[28:32])
        measurement_obj["Number Concentration PM 10 [#/m3]"] = self.calcFloat(measurement[32:36])

        measurement_obj["Typical Particle Size [um]"] = self.calcFloat(measurement[36:40])


        return measurement_obj

#######################################
#### SPS30 Communication Functions ####
#######################################

    def sendCommand(self, cmd):
        """
        Helper function for sending commands to the SPS30 that require no response parsing, etc.
        """
        with self.i2c_device as i2c:
            i2c.write(cmd)


    def startMeasurement(self):
        """
        Starts the measurement mode.
        Datasheet section 6.3.1 

        Notes:
            Output format is hard-coded to Big Endian IEEE754 float values and the readMeasurement function is designed to handle this format only.
        """
        cmd = bytearray([0x00, 0x10, 0x03, 0x00, self.calc_crc8([0x03, 0x00])])
        
        with self.i2c_device as i2c:
            i2c.write(cmd)

        #FIXME: Right now we just YOLO and assume everything is OK. In the future we should read the device's status (Section 6.3.11)  


    def stopMeasurement(self):
        """
        Stops the sensor from taking measurements. Send back to idle-mode
        Datasheet section 6.3.2
        """
        self.sendCommand(bytearray([0x01, 0x04]))


    def dataReady(self):
        """
        Check to see if there is data to be read. This should be called before any measurements are read.
        Notes:
            Originally this was combined with the readMeasurement function but for
            the sake of complexity I think the user should be responsible for checking

        Datasheet section 6.3.3
        """
        cmd = bytearray([0x02, 0x02])
        buf = bytearray(3)

        with self.i2c_device as i2c:
            i2c.write_then_readinto(cmd, buf)
        #Check the CRC and parse the data out. The flag that we want is always in the second bit
        data_ready = self.parse_crc8(buf)[1]

        if data_ready == 0:
            return False
        elif data_ready == 1:
            return True


    def readMeasurement(self):
        """
        Check to see if there are measurements ready and then read, parse and return them.
        Datasheet sections 6.3.4

        TODO: need to make this more bullet-proof. Save/retry from checksum errors and data-not-available errors, 
        bubble up real exceptions from both this and the checksum functions.
        """

        for attempts in range(5):
            if attempts > 0:
                #Let's take a little nap before we try again.
                time.sleep(0.5)
            if self.dataReady():
                cmd = bytearray([0x03, 0x00])
                buf = bytearray(60)

                with self.i2c_device as i2c:
                    i2c.write_then_readinto(cmd, buf)
        
                measurement = self.parse_crc8(buf)
                if measurement != False:
                    return self.parseMeasurement(measurement)



    def cleanFan(self):
        """
        Starts the fan self-cleaning process. This is set to happen by default after one week of continuous operation.
        Datasheet section 6.3.7

        Notes: 
            While this process is running the 'read data ready' flag remains active, but the data is not updated

            This process must be started while the device is in measurement mode 
        """
        self.sendCommand(bytearray([0x56, 0x07]))


    def getSerialNumber(self):
        """
        Retrieve the serial number of the device, and parse it into readable ASCII.
        Datasheet section 6.3.9
        """
        serialNumber = ''
        cmd = bytearray([0xD0, 0x33])
        buf = bytearray(47)
        with self.i2c_device as i2c:
            i2c.write_then_readinto(cmd, buf)
        
        for i in self.parse_crc8(buf):
            #Keep to the printable ASCII bytes to make it clean
            if i > 0x20 and i < 0x7F:
                serialNumber += chr(i)
                 
        return(serialNumber)


    def reset(self):
        """
        Sets the sensor back to its initial state. If the sensor is reset it will need to be re-instantiated in order to continue using it.
        Datasheet section 6.3.13
        """
        self.sendCommand(bytearray([0xD3, 0x04]))


    
    
    #Functionality not yet implemented
    #These appear to have issues operating with the adafruit i2c library. Not a high-priority item
    #TODO: Implement sleep mode (6.3.5)
    #TODO: Implement wakeup mode (6.3.6)

    #TODO: Implement Read/Write Auto Cleaning Interval (6.3.8)
    #TODO: Implement Read firmware version (6.3.10)
    #TODO: Implement Read Device Status Register (6.3.11, 4.4)





