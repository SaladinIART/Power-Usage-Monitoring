import asyncio
import json
from pathlib import Path
from datetime import datetime, timedelta
import logging

from modbus_client import ModbusClient
from data_storage import SQLDataManager, CSVDataManager
from logger_setup import setup_logger

async def main():
    # Load configuration from config.json
    config_path = Path("config.json")
    with config_path.open("r") as f:
        config = json.load(f)
    
    # Set up logging
    logger = setup_logger(config["logging"])
    logger.info("Configuration and logger set up.")

    # Create modbus client (dependency injection: pass modbus config and logger)
    modbus_client = ModbusClient(config["modbus"], logger)
    
    # Create data managers for SQL and CSV
    sql_manager = SQLDataManager(config["database"], logger)
    csv_manager = CSVDataManager(config["csv"], logger)

    logger.info("Starting main loop...")
    
    # Schedule the next data save (every 10 minutes)
    next_save_time = (datetime.now() + timedelta(minutes=10)).replace(second=0, microsecond=0)
    logger.info(f"Next data save scheduled at {next_save_time}")

    while True:
        now = datetime.now()
        wait_time = (next_save_time - now).total_seconds()
        if wait_time > 0:
            await asyncio.sleep(wait_time)
        data = await modbus_client.read_data()
        if data:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            data['timestamp'] = timestamp
            logger.info("Data read successfully from Modbus.")
            # Save data concurrently to both SQL and CSV
            await asyncio.gather(
                sql_manager.save_to_sql([data]),
                csv_manager.save_to_csv(data)
            )
            logger.info(f"Data saved at {timestamp}")
            next_save_time = (datetime.now() + timedelta(minutes=10)).replace(second=0, microsecond=0)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Shutting down...")  
