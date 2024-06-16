# Use an official Python runtime as a parent image
FROM python:3.10.8-slim

# Set the working directory to /app
WORKDIR /app

COPY requirements.txt /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY *.py /app

# Run app.py when the container launches
# ENTRYPOINT ["python", "backup_manager.py"]
CMD ["bash"]
