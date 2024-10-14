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
From the code, it seems like you are monitoring several key electrical parameters. These will be captured and displayed periodically (every 2 minutes) and logged into a CSV file every 5 minutes. Here's a summary of the data points you're currently monitoring:

Line Voltages (V):

Voltage between lines 1 and 2 (L12)
Voltage between lines 2 and 3 (L23)
Voltage between lines 3 and 1 (L31)
Voltage for each phase (L1, L2, L3)
Currents (A):

Current in line 1 (L1)
Current in line 2 (L2)
Current in line 3 (L3)
Power:

Total real power (in watts)
Power factor (calculated, dimensionless)
Frequency (Hz):

System frequency
The data is stored in a CSV file with the following fields:

timestamp: The time when the data was read.
voltage_l12, voltage_l23, voltage_l31: Line voltages.
voltage_l1, voltage_l2, voltage_l3: Voltages on each phase.
current_l1, current_l2, current_l3: Currents on each phase.
total_real_power: Total real power in watts.
total_power_factor: The power factor of the system.
frequency: System frequency in hertz.
This gives us a solid foundation for the Data Output section of the documentation.

Error Handling
Based on your code, here's how the error handling works:

Each modbus register read is wrapped in a try-except block. If an exception occurs during reading (such as connection failures or timeout), it logs the error in the rx380_logger.log file. The error message contains details like which register failed and the exception message.
Example error handling in your code:

python
Copy code
except Exception as e:
    logging.error(f"Error reading scaled value from register {register_address}: {e}")
This provides a fallback mechanism where failures are logged but don't crash the entire program. You could document this as:

Troubleshooting:
If the system fails to read data from the RX380, the error will be logged in rx380_logger.log. Check this file for messages such as "Error reading scaled value from register X" to identify problematic register addresses or communication issues. Ensure the serial connection is stable, and the device is correctly configured.

Optimization & Scalability
You mentioned the plan for version 1.6 to be Dockerized. Here’s how we can describe the scalability benefits:

Scalability:
Future versions of this project will be containerized using Docker to ensure easy deployment across multiple locations. By packaging the Python environment and all dependencies in a Docker container, the system can be deployed on any compatible device without worrying about specific system configurations or missing dependencies. This will make it easier to scale the solution across different locations or industrial sites.

Next Steps on Future Integrations
For future integrations and Industrial IoT (IIoT) systems, here are a few ideas we could document as potential development paths:

Cloud Integration: Connect the system to cloud platforms like AWS IoT or Microsoft Azure IoT Hub to store, process, and analyze data over time. This would allow for centralized monitoring and more advanced analytics like trend analysis and forecasting.
MQTT Protocol: Using MQTT to send real-time data to a centralized dashboard. This could extend the Node-RED integration you mentioned and allow for a more flexible and scalable IoT architecture.
Predictive Analytics: Once sufficient data is collected, machine learning algorithms could be implemented to detect patterns in power consumption. This could predict when machinery will fail or require maintenance, saving on operational costs.

3. Hardware and Software Setup
Hardware:
Laptop:

Acer Predator Helios Neo 16 (Windows 11)
This laptop serves as the main development environment for the project. It has been configured with the necessary software tools for Python development, SSH, and Docker containerization.
Raspberry Pi 5:

Location: Office
Operating System: Bookworm OS
The Raspberry Pi 5 serves as the central controller connected to the RX380 via Modbus RTU using a USB to RS485/422 isolated converter. It is accessed remotely via SSH for development and code deployment.
Software and Tools:
Microsoft Visual Studio Code (VS Code):

SSH Integration: The Raspberry Pi is controlled remotely via SSH from VS Code, allowing you to write, deploy, and test Python code on the Raspberry Pi.
Git & GitHub Desktop Integration: Version control is managed through Git and GitHub. VS Code's Git extension and GitHub Desktop are used to track changes and collaborate with others.
Docker Desktop:

The current setup is being prepared for containerization. Docker Desktop is installed and configured to manage Python environments and dependencies, ensuring that the system can be deployed consistently across multiple devices.
LibreOffice (for data storage):

During earlier versions (v1.4), you encountered issues while saving data both locally and using .ods files with LibreOffice. The final decision was to save data only in .csv format, ensuring easier retrieval and compatibility across systems.
Codesys IDE:

You’re working on converting the current Python-based logic into Function Block Diagram (FBD) and Structured Text (ST) in Codesys to meet specific requirements. This will be a future phase of the project and is currently in progress.
Challenges Encountered:
File Saving Freezes:
During version 1.4, an issue arose where saving data locally using .csv and .ods formats caused the system to freeze. The problem was resolved by sticking to the .csv format exclusively, as it is lightweight and easier to work with, especially for large datasets.

Library Versioning Issue:
When testing the code on a colleague's laptop, you encountered issues due to Python library version incompatibilities. This highlights the importance of version control for both the Python environment and the project itself. To avoid such issues, the move to Docker in version 1.6 will ensure that all dependencies are packaged and version-controlled.

Error Logging:
You have implemented an error logging system (rx380_logger.log) to capture any issues during runtime. This log will help troubleshoot problems such as communication failures with the RX380 or other unexpected errors in the code.

Future Plans (Version 1.6):
Docker Containerization:
The project will be containerized to ensure consistent environments across different devices. This will prevent versioning issues like the ones encountered during testing on a different laptop.
Integration with Codesys:
As you transition from Python to Codesys, the same logic will be re-implemented using FBD and ST. This will allow the project to meet industrial control requirements while maintaining flexibility for future expansions.


