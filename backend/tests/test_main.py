import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app

class TestMain(unittest.TestCase):
    
    def setUp(self):
        self.client = TestClient(app)
    
    def test_root_endpoint(self):
        """Test the root endpoint returns the expected message"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "Weather Prediction API is running"})
    
    @patch('subprocess.run')
    def test_manual_pipeline(self, mock_run):
        """Test the manual pipeline function"""
        from main import manual_pipeline
        
        # Configure the mock
        mock_run.return_value = MagicMock()
        
        # Set up file existence for the conditional logic
        with patch('os.path.exists', return_value=True):
            result = manual_pipeline()
            self.assertTrue(result)
            
            # Check that subprocess.run was called twice (once for each script)
            self.assertEqual(mock_run.call_count, 2)
    
    @patch('subprocess.run')
    def test_initialize_dvc(self, mock_run):
        """Test the DVC initialization function"""
        from main import initialize_dvc
        
        # First test when .dvc already exists
        with patch('os.path.exists', return_value=True):
            result = initialize_dvc()
            self.assertTrue(result)
            mock_run.assert_not_called()
        
        # Reset the mock for the next test
        mock_run.reset_mock()
        
        # Then test when .dvc doesn't exist
        with patch('os.path.exists', return_value=False):
            result = initialize_dvc()
            self.assertTrue(result)
            mock_run.assert_called_once()

if __name__ == '__main__':
    unittest.main()