from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import os
import subprocess
import shutil
import logging
import json
import time
from datetime import datetime

# Configure logging
log_file = os.path.join('logs', f'backend_{datetime.now().strftime("%Y-%m-%d")}.log')
os.makedirs('logs', exist_ok=True)

# Custom JSON formatter for ELK compatibility
class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "path": record.pathname,
            "function": record.funcName,
            "line_number": record.lineno,
            "service": "weather_ops_backend"
        }
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record)

# Set up the logger
logger = logging.getLogger("weather_ops")
logger.setLevel(logging.INFO)

# File handler for JSON logs
file_handler = logging.FileHandler(log_file)
file_handler.setFormatter(JsonFormatter())
logger.addHandler(file_handler)

# Console handler for development
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(console_handler)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Log middleware
@app.middleware("http")
async def log_requests(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(
        f"Request: {request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.3f}s"
    )
    return response

RAW_DATA_PATH = "data/raw_weather.csv"
CLEANED_DATA_PATH = "data/cleaned_weather.csv"
MODEL_PATH = "model.pkl"

@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {"message": "Weather Prediction API is running"}

def manual_pipeline():
    """Run the data processing pipeline manually without DVC"""
    logger.info("Starting manual data processing pipeline")
    try:
        # Ensure data directory exists
        os.makedirs("data", exist_ok=True)
        
        # Execute data cleaning
        if os.path.exists(RAW_DATA_PATH):
            logger.info("Running data cleaning process")
            subprocess.run(["python", "data_cleaner.py"], check=True)
        
        # Execute model training
        if os.path.exists(CLEANED_DATA_PATH):
            logger.info("Running model training process")
            subprocess.run(["python", "train.py"], check=True)
        
        logger.info("Manual pipeline completed successfully")
        return True
    except Exception as e:
        logger.error(f"Manual pipeline error: {str(e)}", exc_info=True)
        return False

def initialize_dvc():
    """Initialize DVC if it's not already initialized"""
    try:
        # Check if .dvc directory exists
        if not os.path.exists(".dvc"):
            logger.info("Initializing DVC")
            subprocess.run(["dvc", "init"], check=True)
            return True
        logger.info("DVC already initialized")
        return True
    except Exception as e:
        logger.error(f"DVC initialization error: {str(e)}", exc_info=True)
        return False

@app.post("/upload/")
async def upload_dataset(file: UploadFile = File(...)):
    logger.info(f"File upload requested: {file.filename}")
    
    if not file.filename.endswith(".csv"):
        logger.warning(f"Invalid file format: {file.filename}")
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")

    new_data = pd.read_csv(file.file)
    
    # Validate required columns
    required_cols = {"time", "tavg", "tmin", "tmax", "prcp", "wspd"}
    if not required_cols.issubset(set(new_data.columns)):
        missing_cols = required_cols - set(new_data.columns)
        logger.warning(f"Missing required columns: {missing_cols}")
        raise HTTPException(status_code=400, detail=f"Missing required columns: {missing_cols}")
    
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)
    
    new_data["time"] = pd.to_datetime(new_data["time"])
    
    if os.path.exists(RAW_DATA_PATH):
        logger.info("Appending to existing data file")
        existing = pd.read_csv(RAW_DATA_PATH)
        existing["time"] = pd.to_datetime(existing["time"])
        combined = pd.concat([existing, new_data]).drop_duplicates(subset="time").sort_values("time")
    else:
        logger.info("Creating new data file")
        combined = new_data

    combined.to_csv(RAW_DATA_PATH, index=False)
    logger.info(f"Data saved to {RAW_DATA_PATH}, {len(combined)} total rows")

    # Try DVC approach first
    try:
        # Initialize DVC if needed
        if initialize_dvc():
            logger.info("Running DVC pipeline")
            subprocess.run(["dvc", "repro"], check=True)
            logger.info("DVC pipeline completed successfully")
            return {"message": "✅ Data uploaded, appended, and model retrained using DVC."}
    except Exception as e:
        logger.warning(f"DVC pipeline failed: {str(e)}")
        # If DVC fails, try manual approach
        if manual_pipeline():
            logger.info("Manual pipeline completed successfully")
            return {"message": "✅ Data uploaded, appended, and model retrained manually."}
        else:
            logger.error("Both DVC and manual pipeline failed")
            # Both approaches failed, but at least save the data
            return {"message": "⚠️ Data uploaded and appended, but model retraining failed."}

import uvicorn

if __name__ == "__main__":
    logger.info("Starting Weather_ops backend application")
    uvicorn.run(app, host="0.0.0.0", port=5000)
