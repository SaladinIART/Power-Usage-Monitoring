# Use Python 3.11.2 slim image as the base
FROM python:3.11.2-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory inside the container
WORKDIR /usr/src/app

# Install build tools
RUN apt-get update && apt-get install -y \
    cmake \
    ninja-build \
    build-essential

RUN pip install --upgrade pip

# Copy the requirements file to the working directory
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code to the container
COPY . .

# Set the command to run your Python application
CMD ["python", "Rx380_watchdog_1.5.py"]