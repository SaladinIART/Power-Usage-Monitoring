import os
import time
import subprocess
from datetime import datetime, timedelta
import logging
import asyncio
import minimalmodbus
import csv
import pymssql
import json
from pathlib import Path

# Set up logging
logging.basicConfig(filename='auto_recovery.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Configuration
WIFI_SSID = "Alumac IOT"
WIFI_PASSWORD = "nY$FV7jd74"
RECONNECT_INTERVAL = 60  # Check every 60 seconds

# Load configuration from config.json
with open('config.json') as config_file:
    config = json.load(config_file)

console = logging.StreamHandler()
console.setLevel(logging.INFO)
logging.getLogger('').addHandler(console)

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

    async def read_register(self, register_address, number_of_decimals, signed):
        """Read a single register value."""
        try:
            return await asyncio.to_thread(
                self.instrument.read_register, register_address, number_of_decimals, signed=signed, functioncode=4
            )
        except Exception as e:
            logging.error(f"Error reading register {register_address}: {e}")
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
            data['total_power_factor'] = await self.read_register(4018, 3, True)
            data['frequency'] = await self.read_register(4019, 2, False)  # Hz

            # Read energy
            data['total_real_energy'] = await self.read_scaled_value(4002, 1)  # kWh
            data['total_reactive_energy'] = await self.read_scaled_value(4010, 1)  # kVARh
            data['total_apparent_energy'] = await self.read_scaled_value(4006, 1)  # kVAh

            return data
        except Exception as e:
            logging.error(f"Error reading data: {e}")
            return None

class DataManager:
    """Class to handle data storage in SQL and CSV."""
    def __init__(self):
        self.db_config = {
            'server': '192.168.0.226',
            'database': 'Power_Usage_Alumac',
            'user': 'sa',
            'password': 'password'
        }

    async def save_to_sql(self, data_buffer):
        """Save data to SQL Server with error handling."""
        insert_query = """
        INSERT INTO dbo.PUA_Office 
           (Timestamp, VoltageL1_v, VoltageL2_v, VoltageL3_v, VoltageL12_v, VoltageL23_v, VoltageL31_v,
            VoltageL12_maxv, VoltageL23_maxv, VoltageL31_maxv, VoltageL12_minv, VoltageL23_minv, VoltageL31_minv,
            CurrentL1_I, CurrentL2_I, CurrentL3_I, CurrentLn_I,
            TotalRealPower_kWh, TotalApparentPower_kWh, TotalReactivePower_kWh, TotalPowerFactor_kWh, Frequency,
            TotalRealEnergy, TotalReactiveEnergy, TotalApparentEnergy)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        try:
            conn = await asyncio.to_thread(pymssql.connect, **self.db_config)
            cursor = conn.cursor()
            for data in data_buffer:
                values = (
                    data['timestamp'],
                    data['voltage_l1'], data['voltage_l2'], data['voltage_l3'],
                    data['voltage_l12'], data['voltage_l23'], data['voltage_l31'],
                    data['voltage_l12_max'], data['voltage_l23_max'], data['voltage_l31_max'],
                    data['voltage_l12_min'], data['voltage_l23_min'], data['voltage_l31_min'],
                    data['current_l1'], data['current_l2'], data['current_l3'], data['current_ln'],
                    data['total_real_power'] / 1000, data['total_apparent_power'] / 1000, data['total_reactive_power'] / 1000,
                    data['total_power_factor'], data['frequency'],
                    data['total_real_energy'], data['total_reactive_energy'], data['total_apparent_energy']
                )
                await asyncio.to_thread(cursor.execute, insert_query, values)
            await asyncio.to_thread(conn.commit)
            logging.info(f"Data inserted successfully into SQL Server! ({len(data_buffer)} records)")
        except Exception as e:
            logging.error(f"Error inserting data into SQL Server: {e}")
            if 'conn' in locals():
                await asyncio.to_thread(conn.rollback)
        finally:
            if 'cursor' in locals():
                await asyncio.to_thread(cursor.close)
            if 'conn' in locals():
                await asyncio.to_thread(conn.close)

def is_wifi_connected():
    """Check if the Raspberry Pi is connected to the specified WiFi network."""
    try:
        result = subprocess.check_output(['iwgetid', '--raw'], universal_newlines=True).strip()
        return result == WIFI_SSID
    except subprocess.CalledProcessError:
        return False


def restart_wifi():
    """Restart WiFi connection."""
    try:
        logging.info("Restarting WiFi...")
        subprocess.call(['sudo', 'nmcli', 'device', 'wifi', 'connect', WIFI_SSID, 'password', WIFI_PASSWORD])
        time.sleep(5)
        logging.info("WiFi restarted.")
    except Exception as e:
        logging.error(f"Error restarting WiFi: {e}")


def relaunch_modbus_connection():
    """Reinitialize the Modbus connection."""
    try:
        logging.info("Reinitializing Modbus connection...")
        # Add logic to reinitialize Modbus here
        logging.info("Modbus connection reinitialized.")
    except Exception as e:
        logging.error(f"Error reinitializing Modbus connection: {e}")

def monitor_system():
    """Monitor WiFi and ensure the Python script is running."""
    while True:
        if not is_wifi_connected():
            logging.warning("WiFi not connected. Attempting to reconnect...")
            restart_wifi()
            time.sleep(10)

        # Wait before the next check
        time.sleep(RECONNECT_INTERVAL)

async def main():
    """Main function to handle data reading, saving, and logging."""
    rx380 = RX380(slave_address=1)
    data_manager = DataManager()

    logging.info("Starting RX380 data logging")
    print("RX380 data logging started.")

    try:
        # Calculate the next 10-minute mark
        now = datetime.now()
        next_save_time = (now + timedelta(minutes=10 - now.minute % 10)).replace(second=0, microsecond=0)
        logging.info(f"Next data save scheduled at {next_save_time}")

        while True:
            # Wait until the next 10-minute mark
            now = datetime.now()
            wait_time = (next_save_time - now).total_seconds()
            if wait_time > 0:
                await asyncio.sleep(wait_time)

            # Collect and save a single data point
            data = await rx380.read_data()
            if data:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                data['timestamp'] = timestamp
                logging.info("Data read successfully")

                # Save data to SQL and CSV
                await data_manager.save_to_sql([data])  # Pass as a list with one data point
                logging.info(f"Data saved at {timestamp}")

                # Schedule the next save time
                next_save_time = (datetime.now() + timedelta(minutes=10)).replace(second=0, microsecond=0)
                logging.info(f"Next data save scheduled at {next_save_time}")

    except asyncio.CancelledError:
        pass
    except KeyboardInterrupt:
        print("Program interrupted by user. Shutting down...")
    finally:
        logging.info("Shutting down RX380 data logging")
        print("RX380 data logging shut down.")

if __name__ == "__main__":
    logging.info("Starting auto-recovery and RX380 logging...")
    try:
        monitor_system()
    except Exception as e:
        logging.error(f"Error during monitoring: {e}")
    asyncio.run(main())
