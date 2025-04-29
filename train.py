import pandas as pd
import pickle
import numpy as np
import json
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error

df = pd.read_csv("data/cleaned_weather.csv")

features_to_lag = ['tavg', 'tmin', 'tmax', 'prcp', 'wspd']
for feature in features_to_lag:
    for lag in range(1, 15):
        df[f"{feature}_t-{lag}"] = df[feature].shift(lag)

df.dropna(inplace=True)

X = df.drop(columns=['time', 'tavg'])  # Exclude original target and date
y = df['tavg']                         # Predict today's tavg


X_train, X_test, y_train, y_test = train_test_split(X, y, shuffle=False, test_size=0.2)


model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
mae = mean_absolute_error(y_test, y_pred)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))

print(f"MAE: {mae:.2f}")
print(f"RMSE: {rmse:.2f}")

with open("model.pkl", "wb") as f:
    pickle.dump(model, f)

metrics = {
    "mae": round(mae, 2),
    "rmse": round(rmse, 2)
}
with open("metrics.json", "w") as f:
    json.dump(metrics, f)

print("✅ Model and metrics saved.")

