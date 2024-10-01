import time
import logging
import threading
import signal
import sys
from datetime import datetime
from rx380 import RX380
from data_logger import save_to_csv, save_to_ods

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
                        if current_time - last_save_time >= 60:  # Save every 60 seconds
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
            
            # Sleep for 5 seconds
            time.sleep(5)
    except Exception as e:
        logging.critical(f"Critical error in main function: {e}")
        print(f"Critical error: {e}")
    finally:
        logging.info("Shutting down RX380 data logging")
        print("Shutting down RX380 data logging")
        sys.exit(0)

if __name__ == "__main__":
    main()