import os
import pandas as pd
from datetime import datetime
from meteostat import Daily, Point

# Define location and date range
location = Point(12.9716, 77.5946)  # Bangalore
start = datetime(2014, 1, 1)
end = datetime(2023, 12, 31)

# Fetch new data
data = Daily(location, start, end)
df = data.fetch()
df.reset_index(inplace=True)

# Ensure the 'time' column is of datetime type (to avoid issues)
df['time'] = pd.to_datetime(df['time'])

# Define file path
existing_path = "data/raw_weather.csv"

# Check if the file exists
if os.path.exists(existing_path):
    existing_data = pd.read_csv(existing_path)
    
    # Ensure the 'time' column is of datetime type in existing data
    existing_data['time'] = pd.to_datetime(existing_data['time'])
    
    # Check if new data has any rows that don't exist in the current file
    new_data = df[~df['time'].isin(existing_data['time'])]
    
    if not new_data.empty:
        # Append new data and remove duplicates
        combined = pd.concat([existing_data, new_data], ignore_index=True)
        combined = combined.drop_duplicates(subset='time').sort_values('time')
        combined.to_csv(existing_path, index=False)
        print("✅ Appended new data to data/raw_weather.csv")
    else:
        print("🔄 No new data to append.")
else:
    # If no existing data, just save the new data
    os.makedirs("data", exist_ok=True)
    df.to_csv(existing_path, index=False)
    print("✅ Raw data saved to data/raw_weather.csv")
