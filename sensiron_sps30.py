import board, busio, struct
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
                else:
                    print("checksum failed")
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
        measurement_obj = {}

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


    def getSerialNumber(self):
        #send the following command to ge the serial number
        cmd = bytearray([0xD0, 0x33])
        buf = bytearray(47)
        with self.i2c_device as i2c:
            i2c.write_then_readinto(cmd, buf)
        #FIXME: Return the raw bytes. We should parse this into a string. 
        return(self.parse_crc8(buf))


    def startMeasurement(self):
        cmd = bytearray([0x00, 0x10, 0x03, 0x00, self.calc_crc8([0x03, 0x00])])
        
        with self.i2c_device as i2c:
            i2c.write(cmd)

        #FIXME: Right now we just YOLO and assume everything is OK. In the future we should read the device's status (Section 6.3.11)    
    
    def readMeasurement(self):
        #First check to see if there is data ready
        cmd = bytearray([0x02, 0x02])
        #Setup a buffer to read into
        buf = bytearray(3)

        with self.i2c_device as i2c:
            i2c.write_then_readinto(cmd, buf)
        #Check the CRC and parse the data out. The flag that we want is always in the second bit
        data_ready =  self.parse_crc8(buf)[1]

        if data_ready == 1:
            cmd = bytearray([0x03, 0x00])
            buf = bytearray(60)

            with self.i2c_device as i2c:
                i2c.write_then_readinto(cmd, buf)
            
            measurement = self.parse_crc8(buf)
            parsed_measurement = self.parseMeasurement(measurement)
            return parsed_measurement
        else:
            return "Data not available"

    def reset(self):
        #FIXME: Unable to reactivate after sending the reset sequence.
        cmd = bytearray([0xD3, 0x04])

        with self.i2c_device as i2c:
            i2c.write(cmd)