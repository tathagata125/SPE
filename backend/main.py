from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import os
import subprocess
import shutil

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

RAW_DATA_PATH = "data/raw_weather.csv"
CLEANED_DATA_PATH = "data/cleaned_weather.csv"
MODEL_PATH = "model.pkl"

@app.get("/")
async def root():
    return {"message": "Weather Prediction API is running"}

def manual_pipeline():
    """Run the data processing pipeline manually without DVC"""
    try:
        # Ensure data directory exists
        os.makedirs("data", exist_ok=True)
        
        # Execute data cleaning
        if os.path.exists(RAW_DATA_PATH):
            subprocess.run(["python", "data_cleaner.py"], check=True)
        
        # Execute model training
        if os.path.exists(CLEANED_DATA_PATH):
            subprocess.run(["python", "train.py"], check=True)
        
        return True
    except Exception as e:
        print(f"Manual pipeline error: {str(e)}")
        return False

def initialize_dvc():
    """Initialize DVC if it's not already initialized"""
    try:
        # Check if .dvc directory exists
        if not os.path.exists(".dvc"):
            subprocess.run(["dvc", "init"], check=True)
            return True
        return True
    except Exception as e:
        print(f"DVC initialization error: {str(e)}")
        return False

@app.post("/upload/")
async def upload_dataset(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")

    new_data = pd.read_csv(file.file)
    
    # Validate required columns
    required_cols = {"time", "tavg", "tmin", "tmax", "prcp", "wspd"}
    if not required_cols.issubset(set(new_data.columns)):
        raise HTTPException(status_code=400, detail="Missing required columns.")
    
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)
    
    new_data["time"] = pd.to_datetime(new_data["time"])
    
    if os.path.exists(RAW_DATA_PATH):
        existing = pd.read_csv(RAW_DATA_PATH)
        existing["time"] = pd.to_datetime(existing["time"])
        combined = pd.concat([existing, new_data]).drop_duplicates(subset="time").sort_values("time")
    else:
        combined = new_data

    combined.to_csv(RAW_DATA_PATH, index=False)

    # Try DVC approach first
    try:
        # Initialize DVC if needed
        if initialize_dvc():
            subprocess.run(["dvc", "repro"], check=True)
            return {"message": "✅ Data uploaded, appended, and model retrained using DVC."}
    except Exception as e:
        print(f"DVC error: {str(e)}")
        # If DVC fails, try manual approach
        if manual_pipeline():
            return {"message": "✅ Data uploaded, appended, and model retrained manually."}
        else:
            # Both approaches failed, but at least save the data
            return {"message": "⚠️ Data uploaded and appended, but model retraining failed."}

import uvicorn

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
