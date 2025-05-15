FROM python:3.12-slim

WORKDIR /app

# Clean up apt cache to reduce image size
RUN apt-get update && \
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

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
