import minimalmodbus
import time
import csv
import os
import logging
from datetime import datetime
from pyexcel_ods3 import save_data, get_data
from collections import OrderedDict
import signal
import sys
import struct
import threading
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

def user_input_handler(killer):
    while not killer.kill_now:
        user_input = input().lower()
        if user_input == 'q':
            print("Quitting...")
            killer.kill_now = True
            break  # Exit the input loop
        elif user_input == 'w':
            print("Pausing... Press 'r' to resume or 'q' to quit.")
            killer.pause = True
        elif user_input == 'r':
            if killer.pause:
                print("Resuming...")
                killer.pause = False
            else:
                print("Program is already running. Press 'w' to pause or 'q' to quit.")
                
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

def get_filename(extension):
    today = datetime.now().strftime("%Y-%m-%d")
    return f"rx380_data_{today}.{extension}"

def save_to_csv(data, folder_path=None):
    if folder_path is None:
        folder_path = Path.home() / "Desktop" / "PUA_Office" / "PUA" / "rx380_daily_logs"
    folder_path = Path(folder_path)
    folder_path.mkdir(parents=True, exist_ok=True)
    
    filename = folder_path / get_filename("csv")
    file_exists = filename.is_file()
    
    with open(filename, 'a', newline='') as csvfile:
        fieldnames = ['timestamp'] + list(data.keys())
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
        
        row_data = {'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        row_data.update(data)
        writer.writerow(row_data)

def save_to_ods(data, folder_path=None):
    if folder_path is None:
        folder_path = Path.home() / "Desktop" / "PUA_Office" / "PUA" / "rx380_daily_logs"
    folder_path = Path(folder_path)
    folder_path.mkdir(parents=True, exist_ok=True)
    
    filename = folder_path / get_filename("ods")
    
    if filename.is_file():
        sheet_data = get_data(str(filename))
        sheet = sheet_data["Sheet1"]
    else:
        sheet = [['timestamp'] + list(data.keys())]
    
    row_data = [datetime.now().strftime("%Y-%m-%d %H:%M:%S")] + list(data.values())
    sheet.append(row_data)
    
    save_data(str(filename), OrderedDict([("Sheet1", sheet)]))
def user_input_handler(killer):
    while not killer.kill_now:
        user_input = input().lower()
        if user_input == 'q':
            print("Quitting...")
            killer.kill_now = True
        elif user_input == 'w':
            print("Pausing...")
            killer.pause = True
        elif user_input == 'r':
            print("Resuming...")
            killer.pause = False

def main():
    rx380 = RX380(slave_address=1)
    killer = GracefulKiller()
    
    logging.info("Starting RX380 data logging")
    print("RX380 data logging started. Press 'q' to quit, 'w' to pause, 'r' to resume.")
    
    # Start the user input handler in a separate thread
    input_thread = threading.Thread(target=user_input_handler, args=(killer,))
    input_thread.daemon = True
    input_thread.start()
    
    last_save_time = time.time()
    
    try:
        while not killer.kill_now:
            if not killer.pause:
                try:
                    data = rx380.read_data()
                    if data:
                        logging.info("Data read successfully")
                        
                        current_time = time.time()
                        if current_time - last_save_time >= 10:  # Save every 10 seconds
                            save_to_csv(data)
                            save_to_ods(data)
                            last_save_time = current_time
                        
                        # Display output on terminal
                        print("\nRX380 Readings:")
                        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                        print(f"Phase Voltage (V): L1={data['voltage_l1']:.1f}, L2={data['voltage_l2']:.1f}, L3={data['voltage_l3']:.1f}")
                        print(f"Line Voltage (V): L12={data['voltage_l12']:.1f}, L23={data['voltage_l23']:.1f}, L31={data['voltage_l31']:.1f}")
                        print(f"Current (A): L1={data['current_l1']:.2f}, L2={data['current_l2']:.2f}, L3={data['current_l3']:.2f}")
                        print(f"Total Real Power: {data['total_real_power']} W")
                        print(f"Total Power Factor: {data['total_power_factor']:.3f}")
                        print(f"Frequency: {data['frequency']:.2f} Hz")
                    else:
                        logging.warning("Failed to read data")
                        print("Failed to read data")
                except Exception as e:
                    logging.error(f"Error in main loop: {e}")
                    print(f"Error: {e}")
            
            # Short sleep to allow for responsive input handling
            for _ in range(5):  # 5 * 0.2 seconds = 1 second total
                if killer.kill_now:
                    break
                time.sleep(0.2)
    except Exception as e:
        logging.critical(f"Critical error in main function: {e}")
        print(f"Critical error: {e}")
    finally:
        logging.info("Shutting down RX380 data logging")
        print("Shutting down RX380 data logging")
        sys.exit(0)  # Ensure the program exits

if __name__ == "__main__":
    main()