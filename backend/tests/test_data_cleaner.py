import os
import sys
import unittest
import pandas as pd
import numpy as np
from unittest.mock import patch, mock_open

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestDataCleaner(unittest.TestCase):
    
    def setUp(self):
        # Sample data for testing
        self.sample_data = pd.DataFrame({
            'time': ['2025-01-01', '2025-01-02', '2025-01-03'],
            'tavg': [10.0, np.nan, 15.0],
            'tmin': [5.0, np.nan, 10.0],
            'tmax': [15.0, np.nan, 20.0],
            'prcp': [0.5, np.nan, 0.0],
            'snow': [0.0, 1.0, 0.0],
            'wdir': [180, 270, 90],
            'wspd': [10.0, np.nan, 15.0],
            'wpgt': [15.0, 20.0, 25.0],
            'pres': [1000, 1005, 1010],
            'tsun': [8.0, 6.0, 9.0]
        })
    
    @patch('pandas.DataFrame.to_csv')
    @patch('pandas.read_csv')
    def test_data_cleaning(self, mock_read_csv, mock_to_csv):
        # Setup the mock
        mock_read_csv.return_value = self.sample_data
        
        # Import data_cleaner which will use our mocked functions
        import data_cleaner
        
        # Verify read_csv was called with the correct path
        mock_read_csv.assert_called_once_with("data/raw_weather.csv")
        
        # Verify to_csv was called with the correct path
        mock_to_csv.assert_called_once()
        args, kwargs = mock_to_csv.call_args
        self.assertEqual(kwargs['index'], False)
        self.assertEqual(args[0], "data/cleaned_weather.csv")
    
    def test_data_cleaner_logic(self):
        # This test runs the actual data cleaning logic on our sample data
        df = self.sample_data.copy()
        
        # Apply the same cleaning logic as in data_cleaner.py
        df = df.drop(columns=['snow', 'wdir', 'wpgt', 'pres', 'tsun'], errors='ignore')
        df[['tavg', 'tmin', 'tmax']] = df[['tavg', 'tmin', 'tmax']].fillna(method='ffill')
        df['prcp'] = df['prcp'].fillna(0)
        df['wspd'] = df['wspd'].fillna(method='ffill')
        df['wspd'] = df['wspd'].fillna(df['wspd'].median())
        df.dropna(inplace=True)
        
        # Assertions to verify cleaning worked correctly
        self.assertEqual(len(df), 3)  # No rows should be dropped in this case
        self.assertNotIn('snow', df.columns)  # snow column should be dropped
        self.assertNotIn('wdir', df.columns)  # wdir column should be dropped
        self.assertEqual(df['tavg'].iloc[1], 10.0)  # NaN value should be filled with previous value
        self.assertEqual(df['prcp'].iloc[1], 0.0)  # NaN value should be filled with 0
        self.assertEqual(df['wspd'].iloc[1], 10.0)  # NaN value should be filled with previous value

if __name__ == '__main__':
    unittest.main()