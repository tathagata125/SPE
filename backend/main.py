from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
import pandas as pd
import os
import subprocess
import shutil
import logging
import json
import time
from datetime import datetime
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

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

# Prometheus metrics
REQUEST_COUNT = Counter(
    'http_requests_total', 
    'Total HTTP Requests', 
    ['method', 'endpoint', 'status']
)
REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds', 
    'HTTP Request Latency', 
    ['method', 'endpoint']
)
MODEL_PREDICTION_COUNT = Counter(
    'model_predictions_total',
    'Total number of model predictions'
)
MODEL_TRAINING_COUNT = Counter(
    'model_training_total',
    'Total number of model training runs'
)
DATA_UPLOAD_COUNT = Counter(
    'data_upload_total',
    'Total number of data uploads'
)

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
    
    # Log the request
    logger.info(
        f"Request: {request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.3f}s"
    )
    
    # Record Prometheus metrics
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    REQUEST_LATENCY.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(process_time)
    
    return response

RAW_DATA_PATH = "data/raw_weather.csv"
CLEANED_DATA_PATH = "data/cleaned_weather.csv"
MODEL_PATH = "model.pkl"

@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {"message": "Weather Prediction API is running"}

@app.get("/model")
async def get_model():
    """Endpoint to provide the trained model for the frontend"""
    logger.info("Model endpoint accessed")
    model_path = MODEL_PATH

    if not os.path.exists(model_path):
        logger.error(f"Model file not found at {model_path}")
        raise HTTPException(status_code=404, detail="Model not found")

    try:
        logger.info(f"Model successfully loaded from {model_path}")
        return FileResponse(model_path, media_type="application/octet-stream", filename="model.pkl")
    except Exception as e:
        logger.error(f"Error loading model: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error loading model: {str(e)}")

@app.get("/data/cleaned")
async def get_cleaned_data():
    """Endpoint to provide the cleaned data for the frontend"""
    logger.info("Cleaned data endpoint accessed")
    
    if not os.path.exists(CLEANED_DATA_PATH):
        logger.error(f"Cleaned data file not found at {CLEANED_DATA_PATH}")
        raise HTTPException(status_code=404, detail="Cleaned data not found")
    
    try:
        df = pd.read_csv(CLEANED_DATA_PATH)
        logger.info(f"Cleaned data successfully loaded from {CLEANED_DATA_PATH}")
        return df.to_json(orient="records")
    except Exception as e:
        logger.error(f"Error loading cleaned data: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error loading cleaned data: {str(e)}")

@app.get("/metrics")
async def metrics():
    """Endpoint for Prometheus metrics"""
    logger.info("Metrics endpoint accessed")
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

def initialize_dvc():
    """Initialize DVC if it's not already initialized"""
    try:
        # Check if .dvc directory exists
        if not os.path.exists(".dvc"):
            logger.info("Initializing DVC with --no-scm flag")
            subprocess.run(["dvc", "init", "--no-scm"], check=True)
            return True
        logger.info("DVC already initialized")
        return True
    except Exception as e:
        logger.error(f"DVC initialization error: {str(e)}", exc_info=True)
        return False

def manual_pipeline():
    """Run the data processing pipeline manually without DVC"""
    logger.info("Starting manual data processing pipeline")
    try:
        # Ensure data directory exists
        os.makedirs("data", exist_ok=True)
        
        # Execute data cleaning
        if os.path.exists(RAW_DATA_PATH):
            logger.info("Running data cleaning process")
            result = subprocess.run(["python", "data_cleaner.py"], check=True, capture_output=True, text=True)
            logger.info(f"Data cleaner output: {result.stdout}")
            if result.stderr:
                logger.warning(f"Data cleaner stderr: {result.stderr}")
        else:
            logger.error(f"Raw data file not found at {RAW_DATA_PATH}")
            return False
        
        # Execute model training
        if os.path.exists(CLEANED_DATA_PATH):
            logger.info("Running model training process")
            result = subprocess.run(["python", "train.py"], check=True, capture_output=True, text=True)
            logger.info(f"Model training output: {result.stdout}")
            if result.stderr:
                logger.warning(f"Model training stderr: {result.stderr}")
                
            # Verify that model file was created
            if os.path.exists(MODEL_PATH):
                logger.info(f"Model file created successfully at {MODEL_PATH}")
            else:
                logger.error(f"Model file was not created at {MODEL_PATH}")
                return False
        else:
            logger.error(f"Cleaned data file not found at {CLEANED_DATA_PATH}")
            return False
        
        logger.info("Manual pipeline completed successfully")
        return True
    except Exception as e:
        logger.error(f"Manual pipeline error: {str(e)}", exc_info=True)
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

    pipeline_success = False
    error_msg = None
    
    # Try DVC approach first
    try:
        # Initialize DVC if needed
        if initialize_dvc():
            logger.info("Running DVC pipeline")
            subprocess.run(["dvc", "repro"], check=True)
            logger.info("DVC pipeline completed successfully")
            pipeline_success = True
    except Exception as e:
        error_msg = str(e)
        logger.warning(f"DVC pipeline failed: {error_msg}")
    
    # If DVC fails, try manual approach
    if not pipeline_success:
        logger.info("Falling back to manual pipeline")
        if manual_pipeline():
            logger.info("Manual pipeline completed successfully")
            pipeline_success = True
        else:
            logger.error("Both DVC and manual pipeline failed")
            return {"message": "⚠️ Data uploaded and appended, but model retraining failed."}
    
    # Return detailed success message
    if pipeline_success:
        # Verify output files exist
        cleaned_exists = os.path.exists(CLEANED_DATA_PATH)
        model_exists = os.path.exists(MODEL_PATH)
        logger.info(f"Pipeline completed. Cleaned data exists: {cleaned_exists}, Model exists: {model_exists}")
        
        if cleaned_exists and model_exists:
            return {"message": "✅ Data uploaded, appended, and model retrained successfully."}
        else:
            return {
                "message": "⚠️ Pipeline completed but some files are missing.",
                "details": f"Cleaned data exists: {cleaned_exists}, Model exists: {model_exists}"
            }
    else:
        return {"message": f"⚠️ Data uploaded and appended, but model retraining failed: {error_msg}"}

import uvicorn

if __name__ == "__main__":
    logger.info("Starting Weather_ops backend application")
    uvicorn.run(app, host="0.0.0.0", port=5000)
