# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install dependencies
COPY app/requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy application
COPY app/ .

# Expose the port
EXPOSE 5000

# Define the default command
CMD ["python", "main.py"]