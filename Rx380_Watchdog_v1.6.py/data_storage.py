import csv
import asyncio
from pathlib import Path
import pymssql
import logging

class SQLDataManager:
    def __init__(self, db_config, logger: logging.Logger):
        self.db_config = db_config
        self.logger = logger

    async def save_to_sql(self, data_buffer):
        insert_query = """
        INSERT INTO Office_Readings 
           (Timestamp, VoltageL1_v, VoltageL2_v, VoltageL3_v)
        VALUES (%s, %s, %s, %s)
        """
        try:
            conn = await asyncio.to_thread(pymssql.connect, **self.db_config)
            cursor = conn.cursor()
            rows = []
            for data in data_buffer:
                rows.append((
                    data['timestamp'],
                    data['voltage_l1'],
                    data['voltage_l2'],
                    data['voltage_l3']
                ))
            await asyncio.to_thread(cursor.executemany, insert_query, rows)
            await asyncio.to_thread(conn.commit)
            self.logger.info(f"Inserted {len(data_buffer)} records into SQL Server.")
        except Exception as e:
            self.logger.error(f"Error inserting data into SQL Server: {e}")
            if 'conn' in locals():
                await asyncio.to_thread(conn.rollback)
        finally:
            if 'cursor' in locals():
                await asyncio.to_thread(cursor.close)
            if 'conn' in locals():
                await asyncio.to_thread(conn.close)

class CSVDataManager:
    def __init__(self, csv_config, logger: logging.Logger):
        self.folder_path = Path(csv_config.get("log_folder", "."))
        self.folder_path.mkdir(parents=True, exist_ok=True)
        self.logger = logger

    def get_filename(self, extension="csv"):
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        return self.folder_path / f"rx380_data_{today}.{extension}"

    async def save_to_csv(self, data):
        filename = self.get_filename()
        file_exists = filename.is_file()
        # For simplicity here we use a synchronous write; you could replace with aiofiles.
        async with asyncio.Lock():
            with open(filename, 'a', newline='') as csvfile:
                fieldnames = ['timestamp'] + list(data.keys())
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                if not file_exists:
                    writer.writeheader()
                writer.writerow(data)
        self.logger.info(f"Data saved to CSV file: {filename}")
