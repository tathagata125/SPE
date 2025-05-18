# metrics.py - Prometheus metrics for Weather_Ops backend
from prometheus_client import Counter, Histogram, Summary

# Define metrics
# Counter for tracking total prediction requests
PREDICTION_REQUESTS = Counter(
    'weather_prediction_requests_total', 
    'Total number of weather prediction requests',
    ['prediction_type', 'status']
)

# Histogram for tracking prediction latency
PREDICTION_LATENCY = Histogram(
    'weather_prediction_latency_seconds', 
    'Latency of weather predictions in seconds',
    ['prediction_type']
)

# Summary for tracking prediction result values
PREDICTION_VALUES = Summary(
    'weather_prediction_values',
    'Summary of predicted weather values',
    ['prediction_type', 'metric']
)

# Data processing metrics
DATA_PROCESSING_DURATION = Histogram(
    'weather_data_processing_seconds',
    'Duration of data processing operations',
    ['operation_type']
)

# Model metrics
MODEL_LOAD_DURATION = Histogram(
    'weather_model_load_seconds',
    'Time taken to load machine learning models',
    ['model_type']
)

# Data metrics
DATA_ROWS_PROCESSED = Counter(
    'weather_data_rows_processed_total',
    'Total number of data rows processed',
    ['data_type']
)
