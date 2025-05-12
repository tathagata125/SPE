import pandas as pd

df = pd.read_csv("data/raw_weather.csv")

df = df.drop(columns=['snow', 'wdir', 'wpgt', 'pres', 'tsun'], errors='ignore')

df[['tavg', 'tmin', 'tmax']] = df[['tavg', 'tmin', 'tmax']].fillna(method='ffill')
df['prcp'] = df['prcp'].fillna(0)
df['wspd'] = df['wspd'].fillna(method='ffill')
df['wspd'] = df['wspd'].fillna(df['wspd'].median())

df.dropna(inplace=True)
df.to_csv("data/cleaned_weather.csv", index=False)
print("✅ Cleaned data saved to data/cleaned_weather.csv")

