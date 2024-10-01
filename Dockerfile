# Use the official Python image as a parent image
FROM python:3.11-slim-buster

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Upgrade pip and install required packages
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Make port 80 available to the world outside this container
EXPOSE 80

# Run PUM_main.py when the container launches
CMD ["python", "PUM_main.py"]