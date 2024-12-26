import os
import time
import logging
from datetime import datetime, timedelta
import asyncio
import minimalmodbus
import sqlite3

# Set up logging
logging.basicConfig(filename='rx380_logger.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

class RX380:
    """Class to handle Modbus communication with RX380 device."""
    def __init__(self, port='/dev/ttyUSB0', slave_address=1):
        self.instrument = minimalmodbus.Instrument(port, slave_address)
        self.setup_instrument()

    def setup_instrument(self):
        """Configure the Modbus instrument settings."""
        self.instrument.serial.baudrate = 19200
        self.instrument.serial.bytesize = 8
        self.instrument.serial.parity = minimalmodbus.serial.PARITY_EVEN
        self.instrument.serial.stopbits = 1
        self.instrument.serial.timeout = 1
        self.instrument.mode = minimalmodbus.MODE_RTU

    async def read_scaled_value(self, register_address, scale_factor):
        """Read and scale values from the Modbus registers."""
        try:
            raw_value = await asyncio.to_thread(
                self.instrument.read_registers, register_address, 2, functioncode=4
            )
            value = (raw_value[0] << 16 | raw_value[1]) * scale_factor
            return value
        except Exception as e:
            logging.error(f"Error reading scaled value from register {register_address}: {e}")
            return None

    async def read_data(self):
        """Read all necessary data from RX380."""
        data = {}
        try:
            # Read voltages
            data['voltage_l1'] = await self.read_scaled_value(4034, 0.1)  # V
            data['voltage_l2'] = await self.read_scaled_value(4036, 0.1)  # V
            data['voltage_l3'] = await self.read_scaled_value(4038, 0.1)  # V
            data['voltage_l12'] = await self.read_scaled_value(4028, 0.1)  # V
            data['voltage_l23'] = await self.read_scaled_value(4030, 0.1)  # V
            data['voltage_l31'] = await self.read_scaled_value(4032, 0.1)  # V

            # Read max voltages
            data['voltage_l12_max'] = await self.read_scaled_value(4124, 0.1)  # V
            data['voltage_l23_max'] = await self.read_scaled_value(4128, 0.1)  # V
            data['voltage_l31_max'] = await self.read_scaled_value(4132, 0.1)  # V

            # Read min voltages
            data['voltage_l12_min'] = await self.read_scaled_value(4212, 0.1)  # V
            data['voltage_l23_min'] = await self.read_scaled_value(4216, 0.1)  # V
            data['voltage_l31_min'] = await self.read_scaled_value(4220, 0.1)  # V

            # Read current
            data['current_l1'] = await self.read_scaled_value(4020, 0.001)  # A
            data['current_l2'] = await self.read_scaled_value(4022, 0.001)  # A
            data['current_l3'] = await self.read_scaled_value(4024, 0.001)  # A
            data['current_ln'] = await self.read_scaled_value(4026, 0.001)  # A

            # Read power
            data['total_real_power'] = await self.read_scaled_value(4012, 1)  # W
            data['total_apparent_power'] = await self.read_scaled_value(4014, 1)  # VA
            data['total_reactive_power'] = await self.read_scaled_value(4016, 1)  # VAR

            # Read power factor and frequency
            data['total_power_factor'] = await self.read_scaled_value(4018, 0.001)
            data['frequency'] = await self.read_scaled_value(4019, 0.01)  # Hz

            # Read energy
            data['total_real_energy'] = await self.read_scaled_value(4002, 1)  # kWh
            data['total_reactive_energy'] = await self.read_scaled_value(4010, 1)  # kVARh
            data['total_apparent_energy'] = await self.read_scaled_value(4006, 1)  # kVAh

            return data
        except Exception as e:
            logging.error(f"Error reading data: {e}")
            return None

class DataManager:
    """Class to handle data storage in SQLite."""
    def __init__(self, db_path='PUA_Office.sqlite'):
        self.db_path = db_path
        self.create_table()

    def create_table(self):
        """Ensure the `PUA_Office` table exists."""
        create_table_query = """
        CREATE TABLE IF NOT EXISTS PUA_Office (
            ReadingID INTEGER PRIMARY KEY AUTOINCREMENT,
            Timestamp TEXT NOT NULL,
            VoltageL1_v REAL,
            VoltageL2_v REAL,
            VoltageL3_v REAL,
            VoltageL12_v REAL,
            VoltageL23_v REAL,
            VoltageL31_v REAL,
            VoltageL12_maxv REAL,
            VoltageL23_maxv REAL,
            VoltageL31_maxv REAL,
            VoltageL12_minv REAL,
            VoltageL23_minv REAL,
            VoltageL31_minv REAL,
            CurrentL1_I REAL,
            CurrentL2_I REAL,
            CurrentL3_I REAL,
            CurrentLn_I REAL,
            TotalRealPower_kWh REAL,
            TotalApparentPower_kWh REAL,
            TotalReactivePower_kWh REAL,
            TotalPowerFactor_kWh REAL,
            Frequency REAL,
            TotalRealEnergy INTEGER,
            TotalReactiveEnergy INTEGER,
            TotalApparentEnergy INTEGER
        );
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(create_table_query)
            conn.commit()
        logging.info("Table PUA_Office ensured in SQLite database.")

    def save_to_sqlite(self, data):
        """Save data to SQLite database."""
        insert_query = """
        INSERT INTO PUA_Office (
            Timestamp, VoltageL1_v, VoltageL2_v, VoltageL3_v, VoltageL12_v, VoltageL23_v, VoltageL31_v,
            VoltageL12_maxv, VoltageL23_maxv, VoltageL31_maxv, VoltageL12_minv, VoltageL23_minv, VoltageL31_minv,
            CurrentL1_I, CurrentL2_I, CurrentL3_I, CurrentLn_I, TotalRealPower_kWh, TotalApparentPower_kWh,
            TotalReactivePower_kWh, TotalPowerFactor_kWh, Frequency, TotalRealEnergy, TotalReactiveEnergy, TotalApparentEnergy
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(insert_query, data)
                conn.commit()
            logging.info("Data successfully inserted into PUA_Office.")
        except Exception as e:
            logging.error(f"Error inserting data into SQLite: {e}")

async def main():
    """Main function to handle data reading and saving."""
    rx380 = RX380()
    data_manager = DataManager()

    logging.info("Starting RX380 data logging")

    try:
        while True:
            # Read data from RX380
            data = await rx380.read_data()
            if data:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                data_tuple = (
                    timestamp, data['voltage_l1'], data['voltage_l2'], data['voltage_l3'],
                    data['voltage_l12'], data['voltage_l23'], data['voltage_l31'],
                    data['voltage_l12_max'], data['voltage_l23_max'], data['voltage_l31_max'],
                    data['voltage_l12_min'], data['voltage_l23_min'], data['voltage_l31_min'],
                    data['current_l1'], data['current_l2'], data['current_l3'], data['current_ln'],
                    data['total_real_power'], data['total_apparent_power'], data['total_reactive_power'],
                    data['total_power_factor'], data['frequency'],
                    data['total_real_energy'], data['total_reactive_energy'], data['total_apparent_energy']
                )
                data_manager.save_to_sqlite(data_tuple)
                logging.info(f"Data logged at {timestamp}")

            # Wait 10 minutes before reading again
            await asyncio.sleep(600)

    except asyncio.CancelledError:
        pass
    except KeyboardInterrupt:
        logging.info("Program interrupted by user. Shutting down...")
    finally:
        logging.info("RX380 data logging shut down.")

if __name__ == "__main__":
    asyncio.run(main())
