import asyncio
import minimalmodbus
import logging

class ModbusClient:
    def __init__(self, config, logger: logging.Logger):
        self.port = config["port"]
        self.slave_address = config["slave_address"]
        self.baudrate = config["baudrate"]
        self.logger = logger
        self.instrument = minimalmodbus.Instrument(self.port, self.slave_address)
        self.setup_instrument()

    def setup_instrument(self):
        self.instrument.serial.baudrate = self.baudrate
        self.instrument.serial.bytesize = 8
        self.instrument.serial.parity = minimalmodbus.serial.PARITY_EVEN
        self.instrument.serial.stopbits = 1
        self.instrument.serial.timeout = 1
        self.instrument.mode = minimalmodbus.MODE_RTU
        self.logger.info("Modbus instrument set up.")

    async def read_scaled_value(self, register_address, scale_factor):
        try:
            raw_value = await asyncio.to_thread(
                self.instrument.read_registers, register_address, 2, functioncode=4
            )
            value = (raw_value[0] << 16 | raw_value[1]) * scale_factor
            return value
        except Exception as e:
            self.logger.error(f"Error reading scaled value from register {register_address}: {e}")
            return None

    async def read_data(self):
        data = {}
        try:
            # Example: reading three voltages concurrently
            results = await asyncio.gather(
                self.read_scaled_value(4034, 0.1),
                self.read_scaled_value(4036, 0.1),
                self.read_scaled_value(4038, 0.1)
            )
            data['voltage_l1'], data['voltage_l2'], data['voltage_l3'] = results
            self.logger.info("Data read successfully from modbus registers.")
            return data
        except Exception as e:
            self.logger.error(f"Error reading data: {e}")
            return None
