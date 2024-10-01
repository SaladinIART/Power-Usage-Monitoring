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

# Set up logging
logging.basicConfig(filename='rx380_logger.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

class GracefulKiller:
    kill_now = False
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

def save_to_csv(data, folder_path="~/Desktop/PUA_Office/PUA/rx380_log_daily"):
    folder_path = os.path.expanduser(folder_path)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

        filename = os.path.join(folder_path, get_filename("csv"))
    file_exists = os.path.isfile(filename)
    
    with open(filename, 'a', newline='') as csvfile:
        fieldnames = ['timestamp'] + list(data.keys())
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
        
        row_data = {'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        row_data.update(data)
        writer.writerow(row_data)

def save_to_ods(data, folder_path="~/Desktop/PUA_Office/PUA/rx380_log_daily"):
    folder_path = os.path.expanduser(folder_path)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    
    filename = os.path.join(folder_path, get_filename("ods"))
    
    if os.path.exists(filename):
        sheet_data = get_data(filename)
        sheet = sheet_data["Sheet1"]
    else:
        sheet = [['timestamp'] + list(data.keys())]
    
    row_data = [datetime.now().strftime("%Y-%m-%d %H:%M:%S")] + list(data.values())
    sheet.append(row_data)
    
    save_data(filename, OrderedDict([("Sheet1", sheet)]))

def main():
    rx380 = RX380(slave_address=1)
    killer = GracefulKiller()
    
    logging.info("Starting RX380 data logging")
    
    try:
        while not killer.kill_now:
            try:
                data = rx380.read_data()
                if data:
                    logging.info("Data read successfully")
                    save_to_csv(data)
                    save_to_ods(data)
                else:
                    logging.warning("Failed to read data")
            except Exception as e:
                logging.error(f"Error in main loop: {e}")
            
            time.sleep(5)  # Read every 5 seconds
    except Exception as e:
        logging.critical(f"Critical error in main function: {e}")
    finally:
        logging.info("Shutting down RX380 data logging")

if __name__ == "__main__":
    main()