import minimalmodbus
import struct

class RX380:
    def __init__(self, port='/dev/ttyUSB0', slave_address=1):
        self.instrument = minimalmodbus.Instrument(port, slave_address)
        self.instrument.serial.baudrate = 19200
        self.instrument.serial.bytesize = 8
        self.instrument.serial.parity = minimalmodbus.serial.PARITY_EVEN
        self.instrument.serial.stopbits = 1
        self.instrument.serial.timeout = 1
        self.instrument.mode = minimalmodbus.MODE_RTU

    def read_scaled_value(self, register_address, scale_factor):
        raw_value = self.instrument.read_registers(register_address, 2, functioncode=4)
        value = (raw_value[0] << 16 | raw_value[1]) * scale_factor
        return value

    def read_float(self, register_address, number_of_registers=2):
        raw_value = self.instrument.read_long(register_address, functioncode=4)
        return struct.unpack('>f', struct.pack('>I', raw_value))[0]

    def read_long(self, register_address):
        return self.instrument.read_long(register_address, functioncode=4, signed=True)

    def read_unsigned_long(self, register_address):
        return self.instrument.read_long(register_address, functioncode=4, signed=False)

    def read_data(self):
        data = {}
        try:
            # Read phase voltages (L-N)
            data['voltage_l1'] = self.read_scaled_value(4034, 0.1)  # V
            data['voltage_l2'] = self.read_scaled_value(4036, 0.1)  # V
            data['voltage_l3'] = self.read_scaled_value(4038, 0.1)  # V

            # Read line voltages (L-L)
            data['voltage_l12'] = self.read_scaled_value(4028, 0.1)  # V
            data['voltage_l23'] = self.read_scaled_value(4030, 0.1)  # V
            data['voltage_l31'] = self.read_scaled_value(4032, 0.1)  # V

            # Read maximum line-to-line voltages
            data['voltage_l12_max'] = self.read_scaled_value(4124, 0.1)  # V
            data['voltage_l23_max'] = self.read_scaled_value(4128, 0.1)  # V
            data['voltage_l31_max'] = self.read_scaled_value(4132, 0.1)  # V

            # Read minimum line-to-line voltages
            data['voltage_l12_min'] = self.read_scaled_value(4212, 0.1)  # V
            data['voltage_l23_min'] = self.read_scaled_value(4216, 0.1)  # V
            data['voltage_l31_min'] = self.read_scaled_value(4220, 0.1)  # V

            # Read current
            data['current_l1'] = self.read_scaled_value(4020, 0.001)  # A
            data['current_l2'] = self.read_scaled_value(4022, 0.001)  # A
            data['current_l3'] = self.read_scaled_value(4024, 0.001)  # A
            data['current_ln'] = self.read_scaled_value(4026, 0.001)  # A

            # Read power
            data['total_real_power'] = self.read_long(4012)  # W
            data['total_apparent_power'] = self.read_unsigned_long(4014)  # VA
            data['total_reactive_power'] = self.read_long(4016)  # VAR

            # Read power factor and frequency
            data['total_power_factor'] = self.instrument.read_register(4018, number_of_decimals=3, signed=True, functioncode=4)
            data['frequency'] = self.instrument.read_register(4019, number_of_decimals=2, functioncode=4)  # Hz

            # Read energy
            data['total_real_energy'] = self.read_unsigned_long(4002)  # kWh
            data['total_reactive_energy'] = self.read_unsigned_long(4010)  # kVARh
            data['total_apparent_energy'] = self.read_unsigned_long(4006)  # kVAh

            return data
        except Exception as e:
            print(f"Error reading data: {e}")
            return None