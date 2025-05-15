#!/bin/bash

# Create backend and frontend folders
mkdir -p backend frontend

# Move backend-related files
mv app.py backend/
mv data_cleaner.py backend/
mv data_getter.py backend/
mv train.py backend/
mv predict.py backend/
mv model.pkl backend/ 2>/dev/null
mv metrics.json backend/ 2>/dev/null
mv dvc.yaml backend/ 2>/dev/null
mv dvc.lock backend/ 2>/dev/null

# Move frontend file
mv main.py frontend/

echo "✅ Files organized into backend/ and frontend/"

# Done
