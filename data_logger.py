import csv
import logging
from datetime import datetime
from pyexcel_ods3 import save_data, get_data
from collections import OrderedDict
from pathlib import Path

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
    
    try:
        with open(filename, 'a', newline='') as csvfile:
            fieldnames = ['timestamp'] + list(data.keys())
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            if not file_exists:
                writer.writeheader()
            
            row_data = {'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            row_data.update(data)
            writer.writerow(row_data)
        logging.info(f"Data saved to CSV: {filename}")
    except Exception as e:
        logging.error(f"Error saving to CSV: {e}")

def save_to_ods(data, folder_path=None):
    if folder_path is None:
        folder_path = Path.home() / "Desktop" / "PUA_Office" / "PUA" / "rx380_daily_logs"
    folder_path = Path(folder_path)
    folder_path.mkdir(parents=True, exist_ok=True)
    
    filename = folder_path / get_filename("ods")
    
    try:
        if filename.is_file():
            sheet_data = get_data(str(filename))
            sheet = sheet_data["Sheet1"]
        else:
            sheet = [['timestamp'] + list(data.keys())]
        
        row_data = [datetime.now().strftime("%Y-%m-%d %H:%M:%S")] + list(data.values())
        sheet.append(row_data)
        
        save_data(str(filename), OrderedDict([("Sheet1", sheet)]))
        logging.info(f"Data saved to ODS: {filename}")
    except Exception as e:
        logging.error(f"Error saving to ODS: {e}")