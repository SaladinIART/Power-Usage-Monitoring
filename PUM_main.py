import time
from rx380 import RX380
from data_logger import save_to_csv, save_to_ods

def main():
    rx380 = RX380(slave_address=1)
    
    try:
        while True:
            data = rx380.read_data()
            if data:
                print("\nRX380 Readings:")
                print(f"Phase Voltage (V): L1={data['voltage_l1']:.1f}, L2={data['voltage_l2']:.1f}, L3={data['voltage_l3']:.1f}")
                print(f"Line Voltage (V): L12={data['voltage_l12']:.1f}, L23={data['voltage_l23']:.1f}, L31={data['voltage_l31']:.1f}")
                print(f"Max Line Voltage (V): L12={data['voltage_l12_max']:.1f}, L23={data['voltage_l23_max']:.1f}, L31={data['voltage_l31_max']:.1f}")
                print(f"Min Line Voltage (V): L12={data['voltage_l12_min']:.1f}, L23={data['voltage_l23_min']:.1f}, L31={data['voltage_l31_min']:.1f}")
                print(f"Current (A): L1={data['current_l1']:.2f}, L2={data['current_l2']:.2f}, L3={data['current_l3']:.2f}, LN={data['current_ln']:.2f}")
                print(f"Total Real Power: {data['total_real_power']} W")
                print(f"Total Apparent Power: {data['total_apparent_power']} VA")
                print(f"Total Reactive Power: {data['total_reactive_power']} VAR")
                print(f"Total Power Factor: {data['total_power_factor']:.3f}")
                print(f"Frequency: {data['frequency']:.2f} Hz")
                print(f"Total Real Energy: {data['total_real_energy']} kWh")
                print(f"Total Reactive Energy: {data['total_reactive_energy']} kVARh")
                print(f"Total Apparent Energy: {data['total_apparent_energy']} kVAh")
                
                # Save data to CSV and ODS
                save_to_csv(data)
                save_to_ods(data)
            
            time.sleep(5)  # Read every 5 seconds
    except KeyboardInterrupt:
        print("Program stopped by user")

if __name__ == "__main__":
    main()