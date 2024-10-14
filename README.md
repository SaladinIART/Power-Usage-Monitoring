1. Project Overview

Introduction:
This project focuses on monitoring the electrical consumption (in kilowatt-hours) at a workplace using the RX380 power meter, with the goal of identifying which locations consume the most electricity at specific times. The solution is cost-effective, targeting small and medium enterprises (SMEs) or hobbyists with limited budgets, particularly in Southeast Asia. By collecting and analyzing this data, companies can better manage their energy consumption and make informed decisions on energy efficiency.

The proof of concept (PoC) phase is already complete, demonstrating successful communication between the RX380 and a Raspberry Pi 5 using Python code. Data is being transferred from the RX380 to the Raspberry Pi and then stored in an MSSQL server, with further plans to integrate a dashboard using Node-RED for real-time data visualization.

This project is ongoing, with future plans to explore different controllers such as the PiControl CM4 Industrial Controller, which may be better suited for environments where Raspberry Pi 5 is not ideal.

Audience:
The project is intended for:

Engineers and technicians in small to medium enterprises (SMEs) seeking a low-cost solution for power monitoring.
Hobbyists or individuals involved in industrial automation with limited resources.
Researchers and developers looking to collect and analyze energy consumption data for small-scale industrial or commercial setups.

2. Data Output
This project monitors several key electrical parameters, which are captured every 10 seconds, displayed on the terminal every 2 minutes, and logged into a CSV file every 5 minutes. Below is a list of the data points being monitored:

Line Voltages (V):
Voltage between lines 1 and 2 (L12)
Voltage between lines 2 and 3 (L23)
Voltage between lines 3 and 1 (L31)
Voltage for each individual phase (L1, L2, L3)
Currents (A):
Current in line 1 (L1)
Current in line 2 (L2)
Current in line 3 (L3)
Power:
Total real power (in watts)
Power factor (dimensionless, calculated)
Frequency (Hz):
System frequency
CSV Data Storage:
Data is logged into a CSV file with the following fields:

timestamp: The time when the data was read.
voltage_l12, voltage_l23, voltage_l31: Line voltages.
voltage_l1, voltage_l2, voltage_l3: Voltages on each phase.
current_l1, current_l2, current_l3: Currents on each phase.
total_real_power: Total real power in watts.
total_power_factor: The power factor of the system.
frequency: System frequency in hertz.

2.1. Error Handling
The project has robust error handling mechanisms to ensure the system remains stable during operation. Each Modbus register read is wrapped in a try-except block. If any exception occurs (e.g., communication failure or timeout), the system logs the error into a log file (rx380_logger.log) without crashing the entire program.

Example of Error Handling:
python
Copy code
except Exception as e:
    logging.error(f"Error reading scaled value from register {register_address}: {e}")
Troubleshooting:
If the system fails to read data from the RX380, error messages will be logged in the rx380_logger.log file.
Look for messages like "Error reading scaled value from register X" to identify specific issues with the registers.
Ensure that the serial connection is stable, the correct device configurations are in place, and the Raspberry Pi has the appropriate permissions to access the USB port.

Device physical connection:

RX380 Power Meter:
Connected to the RS485 converter using a 3-core wire (RS485 communication).
RS485 to USB Converter:
Converts the RS485 signal to USB and connects to the Raspberry Pi via the USB port.
Raspberry Pi 5:
Receives the data via USB and processes it through Python scripts for data logging.

3. Hardware and Software Setup
Hardware:
Acer Predator Helios Neo 16 (Windows 11)
This laptop is the main development environment, where all the programming, debugging, and project management take place. It has been configured with the necessary tools for Python development, SSH, and Docker for containerization.
Raspberry Pi 5 (Location: Office)
Operating System: Bookworm OS
The Raspberry Pi 5 acts as the controller, interfacing with the RX380 via Modbus RTU (through a USB to RS485/422 isolated converter). It is accessed remotely from the development laptop through SSH, allowing for seamless deployment and real-time testing.
Software and Tools:
Microsoft Visual Studio Code (VS Code)

SSH Integration: Remotely control and program the Raspberry Pi from VS Code via SSH. This enables easy debugging and execution of Python scripts on the Pi.
Git & GitHub Integration: Version control is implemented using Git, GitHub Desktop, and the Git extension in VS Code to track changes, collaborate with colleagues, and ensure stable project management.
Docker Desktop

The current setup is being prepared for deployment in a containerized environment using Docker. This ensures all dependencies and configurations are consistent across different environments, which will be fully implemented in version 1.6.
LibreOffice

Initially used to save data in both .csv and .ods formats, though .csv has been chosen as the final format for its simplicity and ease of retrieval. LibreOffice may still be used for additional data manipulation if required.
Codesys IDE

Future versions will integrate Codesys to convert Python code logic into Function Block Diagrams (FBD) and Structured Text (ST) to meet specific industrial requirements.
Challenges and Solutions:
File Saving Issues (v1.4)

Early versions encountered system freezes when saving data in .csv and .ods formats simultaneously. This was resolved by sticking to the .csv format only, ensuring smooth performance and ease of access for data logging.
Library Versioning Problems

Testing on different systems led to issues with library incompatibilities (e.g., due to varying Python versions and dependencies). The solution involves Docker containerization in version 1.6, which will package all necessary dependencies into a single environment.
Error Logging

The system logs errors into rx380_logger.log, providing details for troubleshooting any failures during communication with the RX380 or other runtime issues.

