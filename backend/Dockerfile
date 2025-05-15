FROM python:3.12-slim

WORKDIR /app

# Install git if DVC needs it and clean up in the same layer
RUN apt-get update && \
    apt-get install -y git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    rm -rf /root/.cache/pip

# Create data directory explicitly for volume mounting
RUN mkdir -p /app/data

# Copy application code
COPY . .

# Make sure app has access to data directory
RUN chmod -R 777 /app/data

# Expose port for FastAPI
EXPOSE 5000

# Start the API
CMD ["python", "main.py"]
