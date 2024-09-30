import csv
import os
from datetime import datetime
from pyexcel_ods3 import save_data, get_data
from collections import OrderedDict

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