from fastapi import FastAPI, File, UploadFile, HTTPException
import pandas as pd
import os
import subprocess

app = FastAPI()

RAW_DATA_PATH = "data/raw_weather.csv"

@app.post("/upload/")
async def upload_dataset(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")

    new_data = pd.read_csv(file.file)
    
    # Validate required columns
    required_cols = {"time", "tavg", "tmin", "tmax", "prcp", "wspd"}
    if not required_cols.issubset(set(new_data.columns)):
        raise HTTPException(status_code=400, detail="Missing required columns.")
    
    new_data["time"] = pd.to_datetime(new_data["time"])
    
    if os.path.exists(RAW_DATA_PATH):
        existing = pd.read_csv(RAW_DATA_PATH)
        existing["time"] = pd.to_datetime(existing["time"])
        combined = pd.concat([existing, new_data]).drop_duplicates(subset="time").sort_values("time")
    else:
        combined = new_data

    combined.to_csv(RAW_DATA_PATH, index=False)

    # Re-run pipeline (this assumes dvc is installed and paths are configured)
    subprocess.run(["dvc", "repro"], check=True)

    return {"message": "✅ Data uploaded, appended, and model retrained."}
