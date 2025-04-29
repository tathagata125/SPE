# data_getter.py

import os
import pandas as pd
from datetime import datetime
from meteostat import Daily, Point

location = Point(12.9716, 77.5946)  # Bangalore
start = datetime(2014, 1, 1)
end = datetime(2022,12,31)

data = Daily(location, start, end)
df = data.fetch()
df.reset_index(inplace=True)

os.makedirs("data", exist_ok=True)
df.to_csv("data/raw_weather.csv", index=False)
print("✅ Raw data saved to data/raw_weather.csv")

