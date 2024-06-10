# Use the official Python image as the base image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Upgrade pip to the latest version
RUN python -m pip install --upgrade pip

# Increase pip timeout and optionally use a different mirror for PyPI
RUN pip install --no-cache-dir --default-timeout=1000 -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# Expose port 5000 to the outside world
EXPOSE 5000

# Define environment variable
ENV NAME World

# Command to run the Flask application
CMD ["python", "app.py"]
