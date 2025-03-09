# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install tree command and other utilities
RUN apt-get update && \
    apt-get install -y tree && \
    apt-get install -y build-essential && \
    rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Create necessary directories
RUN mkdir -p /app/data

# Copy application
COPY app/ ./app/
COPY README.md .
COPY .env .

# Verify static files are present
RUN ls -la /app/app/static || echo "Static directory not found"

# Expose the port (setting a default but will be overridden by environment)
EXPOSE 5220

# Define the default command - explicitly use gunicorn for production-grade server
CMD ["python", "-m", "flask", "--app", "app.main:app", "run", "--host=0.0.0.0", "--port=5220"]