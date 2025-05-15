import os
import sys
import unittest
import pandas as pd
import numpy as np
import pickle
from unittest.mock import patch, mock_open, MagicMock

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import predict

class TestPredict(unittest.TestCase):
    
    def setUp(self):
        # Sample data for testing
        self.sample_data = pd.DataFrame({
            'time': ['2025-01-01', '2025-01-02', '2025-01-03', '2025-01-04', '2025-01-05'],
            'tavg': [10.0, 12.0, 15.0, 13.0, 11.0],
            'tmin': [5.0, 7.0, 10.0, 8.0, 6.0],
            'tmax': [15.0, 17.0, 20.0, 18.0, 16.0],
            'prcp': [0.5, 0.0, 0.0, 0.2, 0.1],
            'wspd': [10.0, 12.0, 15.0, 11.0, 9.0]
        })
        
        # With lag features added (for the last row)
        self.sample_data_with_lags = self.sample_data.copy()
        features_to_lag = ['tavg', 'tmin', 'tmax', 'prcp', 'wspd']
        for feature in features_to_lag:
            for lag in range(1, 4):
                self.sample_data_with_lags[f"{feature}_t-{lag}"] = self.sample_data_with_lags[feature].shift(lag)
        
        self.sample_data_with_lags.dropna(inplace=True)
        
        # Mock model
        self.mock_model = MagicMock()
        self.mock_model.predict.return_value = np.array([12.5])  # Predicted temperature
        
        # Set feature names attribute
        feature_columns = list(self.sample_data_with_lags.drop(columns=['time', 'tavg']).columns)
        self.mock_model.feature_names_in_ = feature_columns
    
    @patch('pickle.load')
    @patch('pandas.read_csv')
    @patch('builtins.open', new_callable=mock_open)
    def test_predict_next_day(self, mock_file, mock_read_csv, mock_pickle_load):
        # Setup mocks
        mock_read_csv.return_value = self.sample_data_with_lags
        mock_pickle_load.return_value = self.mock_model
        
        # Call the predict function
        result = predict.predict_next_day()
        
        # Assert function returned expected prediction
        self.assertEqual(result, 12.5)
        
        # Verify read_csv was called with the correct path
        mock_read_csv.assert_called_once_with(predict.DATA_PATH)
        
        # Verify model was loaded correctly
        mock_file.assert_called_once_with(predict.MODEL_PATH, "rb")
        
        # Verify predict was called once
        self.mock_model.predict.assert_called_once()
    
    @patch('pandas.read_csv')
    def test_predict_missing_data_file(self, mock_read_csv):
        # Simulate missing data file
        mock_read_csv.side_effect = FileNotFoundError()
        
        # Call the predict function
        result = predict.predict_next_day()
        
        # Assert function returned None due to missing file
        self.assertIsNone(result)
    
    @patch('pickle.load')
    @patch('pandas.read_csv')
    @patch('builtins.open', new_callable=mock_open)
    def test_predict_missing_model_file(self, mock_file, mock_read_csv, mock_pickle_load):
        # Setup mocks, simulate missing model file
        mock_read_csv.return_value = self.sample_data_with_lags
        mock_pickle_load.side_effect = FileNotFoundError()
        
        # Call the predict function
        result = predict.predict_next_day()
        
        # Assert function returned None due to missing model
        self.assertIsNone(result)
    
    @patch('pickle.load')
    @patch('pandas.read_csv')
    @patch('builtins.open', new_callable=mock_open)
    def test_predict_feature_mismatch(self, mock_file, mock_read_csv, mock_pickle_load):
        # Setup mocks
        mock_read_csv.return_value = self.sample_data  # Using data without lags to cause feature mismatch
        
        # Create a model with different feature names
        different_model = MagicMock()
        different_model.feature_names_in_ = ['feature1', 'feature2']  # Different features than our data
        mock_pickle_load.return_value = different_model
        
        # Call the predict function
        result = predict.predict_next_day()
        
        # Assert function returned None due to feature mismatch
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()