import board, busio, struct
from adafruit_bus_device.i2c import I2CDevice

__version__ = ""
__repo__ = ""

class SPS30:

    """Sensiron SPS30 driver.

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
        checksum = calc_crc8(byte_array)
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