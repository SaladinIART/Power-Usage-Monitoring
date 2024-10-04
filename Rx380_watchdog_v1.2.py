import asyncio
import minimalmodbus
import csv
import logging
from datetime import datetime
from pyexcel_ods3 import save_data, get_data
from collections import OrderedDict, deque
import signal
import struct
from pathlib import Path

# Set up logging
logging.basicConfig(filename='rx380_logger.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

class GracefulKiller:
    kill_now = False
    pause = False
    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, *args):
        self.kill_now = True

class RX380:
    def __init__(self, port='/dev/ttyUSB0', slave_address=1):
        self.instrument = minimalmodbus.Instrument(port, slave_address)
        self.instrument.serial.baudrate = 19200
        self.instrument.serial.bytesize = 8
        self.instrument.serial.parity = minimalmodbus.serial.PARITY_EVEN
        self.instrument.serial.stopbits = 1
        self.instrument.serial.timeout = 1
        self.instrument.mode = minimalmodbus.MODE_RTU

    async def read_scaled_value(self, register_address, scale_factor):
        try:
            raw_value = await asyncio.to_thread(self.instrument.read_registers, register_address, 2, functioncode=4)
            value = (raw_value[0] << 16 | raw_value[1]) * scale_factor
            return value
        except Exception as e:
            logging.error(f"Error reading scaled value from register {register_address}: {e}")
            return None

    async def read_float(self, register_address, number_of_registers=2):
        try:
            raw_value = await asyncio.to_thread(self.instrument.read_long, register_address, functioncode=4)
            return struct.unpack('>f', struct.pack('>I', raw_value))[0]
        except Exception as e:
            logging.error(f"Error reading float from register {register_address}: {e}")
            return None

    async def read_long(self, register_address):
        try:
            return await asyncio.to_thread(self.instrument.read_long, register_address, functioncode=4, signed=True)
        except Exception as e:
            logging.error(f"Error reading long from register {register_address}: {e}")
            return None

    async def read_unsigned_long(self, register_address):
        try:
            return await asyncio.to_thread(self.instrument.read_long, register_address, functioncode=4, signed=False)
        except Exception as e:
            logging.error(f"Error reading unsigned long from register {register_address}: {e}")
            return None

    async def read_data(self):
        data = {}
        try:
            # Read phase voltages (L-N)
            data['voltage_l1'] = await self.read_scaled_value(4034, 0.1)  # V
            data['voltage_l2'] = await self.read_scaled_value(4036, 0.1)  # V
            data['voltage_l3'] = await self.read_scaled_value(4038, 0.1)  # V

            # Read line voltages (L-L)
            data['voltage_l12'] = await self.read_scaled_value(4028, 0.1)  # V
            data['voltage_l23'] = await self.read_scaled_value(4030, 0.1)  # V
            data['voltage_l31'] = await self.read_scaled_value(4032, 0.1)  # V

            # Read current
            data['current_l1'] = await self.read_scaled_value(4020, 0.001)  # A
            data['current_l2'] = await self.read_scaled_value(4022, 0.001)  # A
            data['current_l3'] = await self.read_scaled_value(4024, 0.001)  # A

            # Read power
            data['total_real_power'] = await self.read_long(4012)  # W
            data['total_apparent_power'] = await self.read_unsigned_long(4014)  # VA
            data['total_reactive_power'] = await self.read_long(4016)  # VAR

            # Read power factor and frequency
            data['total_power_factor'] = await asyncio.to_thread(self.instrument.read_register, 4018, number_of_decimals=3, signed=True, functioncode=4)
            data['frequency'] = await asyncio.to_thread(self.instrument.read_register, 4019, number_of_decimals=2, functioncode=4)  # Hz

            # Read energy
            data['total_real_energy'] = await self.read_unsigned_long(4002)  # kWh
            data['total_reactive_energy'] = await self.read_unsigned_long(4010)  # kVARh
            data['total_apparent_energy'] = await self.read_unsigned_long(4006)  # kVAh

            return data
        except Exception as e:
            logging.error(f"Error reading data: {e}")
            return None

def get_filename(extension):
    today = datetime.now().strftime("%Y-%m-%d")
    return f"rx380_data_{today}.{extension}"

async def save_to_csv(data, folder_path=None):
    if folder_path is None:
        folder_path = Path.home() / "Desktop" / "PUA_Office" / "PUA" / "rx380_daily_logs"
    folder_path = Path(folder_path)
    folder_path.mkdir(parents=True, exist_ok=True)
    
    filename = folder_path / get_filename("csv")
    file_exists = filename.is_file()
    
    async with asyncio.Lock():
        with open(filename, 'a', newline='') as csvfile:
            fieldnames = ['timestamp'] + list(data[0].keys())
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            if not file_exists:
                writer.writeheader()
            
            for entry in data:
                row_data = {'timestamp': entry['timestamp']}
                row_data.update(entry)
                writer.writerow(row_data)

async def save_to_ods(data, folder_path=None):
    if folder_path is None:
        folder_path = Path.home() / "Desktop" / "PUA_Office" / "PUA" / "rx380_daily_logs"
    folder_path = Path(folder_path)
    folder_path.mkdir(parents=True, exist_ok=True)
    
    filename = folder_path / get_filename("ods")
    
    async with asyncio.Lock():
        if filename.is_file():
            sheet_data = await asyncio.to_thread(get_data, str(filename))
            sheet = sheet_data["Sheet1"]
        else:
            sheet = [['timestamp'] + list(data[0].keys())]
        
        for entry in data:
            row_data = [entry['timestamp']] + list(entry.values())
            sheet.append(row_data)
        
        await asyncio.to_thread(save_data, str(filename), OrderedDict([("Sheet1", sheet)]))

async def main():
    rx380 = RX380(slave_address=1)
    killer = GracefulKiller()
    
    logging.info("Starting RX380 data logging")
    print("RX380 data logging started. Press Ctrl+C to quit.")
    
    data_buffer = deque(maxlen=30)  # Circular buffer to store 5 minutes of readings
    
    try:
        while not killer.kill_now:
            if not killer.pause:
                try:
                    data = await rx380.read_data()
                    if data:
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        data['timestamp'] = timestamp
                        data_buffer.append(data)
                        logging.info("Data read successfully")
                        
                        # Display output on terminal
                        print(f"\nRX380 Readings at {timestamp}:")
                        print(f"Phase Voltage (V): L1={data['voltage_l1']:.1f}, L2={data['voltage_l2']:.1f}, L3={data['voltage_l3']:.1f}")
                        print(f"Line Voltage (V): L12={data['voltage_l12']:.1f}, L23={data['voltage_l23']:.1f}, L31={data['voltage_l31']:.1f}")
                        print(f"Current (A): L1={data['current_l1']:.2f}, L2={data['current_l2']:.2f}, L3={data['current_l3']:.2f}")
                        print(f"Total Real Power: {data['total_real_power']} W")
                        print(f"Total Power Factor: {data['total_power_factor']:.3f}")
                        print(f"Frequency: {data['frequency']:.2f} Hz")
                        
                        # Save data every 5 minutes
                        if len(data_buffer) == 30:  # 30 * 10 seconds = 5 minutes
                            await save_to_csv(list(data_buffer))
                            await save_to_ods(list(data_buffer))
                            logging.info("Data saved to CSV and ODS files")
                    else:
                        logging.warning("Failed to read data")
                        print("Failed to read data")
                except Exception as e:
                    logging.error(f"Error in main loop: {e}")
                    print(f"Error: {e}")
            
            await asyncio.sleep(10)  # Read data every 10 seconds
    except asyncio.CancelledError:
        pass
    finally:
        logging.info("Shutting down RX380 data logging")
        print("Shutting down RX380 data logging")

if __name__ == "__main__":
    asyncio.run(main())