# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set environment variables for non-interactive apt install
ENV DEBIAN_FRONTEND=noninteractive

# Set the working directory in the container
WORKDIR /app

# Install ffmpeg and other system dependencies
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements.txt file and install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy the Django project files into the container
COPY . .

# Set environment variables for Django
ENV DJANGO_SETTINGS_MODULE=myproject.settings
ENV PYTHONUNBUFFERED=1

# Expose the port that Django uses
EXPOSE 8000

# Run the Django server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
