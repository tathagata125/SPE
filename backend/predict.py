import pandas as pd
import pickle

# Load cleaned data
df = pd.read_csv("data/cleaned_weather.csv")

# Create lag features for 14 days
features_to_lag = ['tavg', 'tmin', 'tmax', 'prcp', 'wspd']
for feature in features_to_lag:
    for lag in range(1, 15):
        df[f"{feature}_t-{lag}"] = df[feature].shift(lag)

df.dropna(inplace=True)

# Prepare latest row (prediction input)
X = df.drop(columns=['time', 'tavg'])  # Match training input
X_new = X.tail(1)

# Load model
with open("model.pkl", "rb") as f:
    model = pickle.load(f)

# Predict
prediction = model.predict(X_new)[0]
print(f"🌡️ Predicted average temperature for tomorrow: {prediction:.2f}°C")

