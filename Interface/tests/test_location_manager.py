import unittest
from unittest.mock import patch, MagicMock
from AppMap.AppWidgets.LocationManager import LocationManager


class TestLocationManager(unittest.TestCase):
    """Test LocationManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.manager = LocationManager()
    
    def test_initialization(self):
        """Test that manager initializes with None incident frame."""
        self.assertIsNone(self.manager.incident_frame)
        self.assertIsNotNone(self.manager.geolocator)
    
    @patch('AppMap.AppWidgets.LocationManager.Nominatim')
    def test_reverse_geocode_success(self, mock_nominatim_class):
        """Test successful reverse geocoding."""
        mock_location = MagicMock()
        mock_location.raw = {
            "address": {
                "road": "Test Street",
                "city": "Test City",
                "state": "Test State"
            }
        }
        
        mock_geolocator = MagicMock()
        mock_geolocator.reverse.return_value = mock_location
        mock_nominatim_class.return_value = mock_geolocator
        
        manager = LocationManager()
        result = manager.reverse_geocode(52.0, 4.0)
        
        self.assertEqual(result["road"], "Test Street")
        self.assertEqual(result["city"], "Test City")
        self.assertEqual(result["state"], "Test State")
    
    @patch('AppMap.AppWidgets.LocationManager.Nominatim')
    def test_reverse_geocode_error(self, mock_nominatim_class):
        """Test handling of geocoding errors."""
        mock_geolocator = MagicMock()
        mock_geolocator.reverse.side_effect = Exception("Geocoding failed")
        mock_nominatim_class.return_value = mock_geolocator
        
        manager = LocationManager()
        result = manager.reverse_geocode(52.0, 4.0)
        
        # Should return empty dict on error
        self.assertEqual(result, {})
    
    @patch('AppMap.AppWidgets.LocationManager.Nominatim')
    def test_reverse_geocode_missing_fields(self, mock_nominatim_class):
        """Test handling of incomplete address data."""
        mock_location = MagicMock()
        mock_location.raw = {"address": {}}
        
        mock_geolocator = MagicMock()
        mock_geolocator.reverse.return_value = mock_location
        mock_nominatim_class.return_value = mock_geolocator
        
        manager = LocationManager()
        result = manager.reverse_geocode(52.0, 4.0)
        
        # Should return empty dict
        self.assertEqual(result, {})
    
    def test_destroy_incident_frame_none(self):
        """Test destroying frame when none exists."""
        # Should not raise error
        self.manager.destroy_incident_frame()
        self.assertIsNone(self.manager.incident_frame)
    
    def test_destroy_incident_frame_exists(self):
        """Test destroying existing frame."""
        mock_frame = MagicMock()
        self.manager.incident_frame = mock_frame
        
        self.manager.destroy_incident_frame()
        
        mock_frame.grid_forget.assert_called_once()
        mock_frame.destroy.assert_called_once()
        self.assertIsNone(self.manager.incident_frame)
    
    @patch('AppMap.AppWidgets.LocationManager.UIBuilder')
    def test_create_incident_frame_first_time(self, mock_ui_builder):
        """Test creating incident frame for the first time."""
        mock_frame = MagicMock()
        mock_ui_builder.create_incident_location_frame.return_value = mock_frame
        
        master = MagicMock()
        location_dict = {
            "road": "Main Street",
            "city": "Amsterdam",
            "state": "North Holland"
        }
        go_to_callback = MagicMock()
        
        result = self.manager.create_incident_frame(master, location_dict, go_to_callback)
        
        self.assertEqual(result, mock_frame)
        self.assertEqual(self.manager.incident_frame, mock_frame)
    
    @patch('AppMap.AppWidgets.LocationManager.UIBuilder')
    def test_create_incident_frame_already_exists(self, mock_ui_builder):
        """Test that existing frame is not recreated."""
        existing_frame = MagicMock()
        self.manager.incident_frame = existing_frame
        
        master = MagicMock()
        location_dict = {"road": "Test", "city": "City", "state": "State"}
        go_to_callback = MagicMock()
        
        result = self.manager.create_incident_frame(master, location_dict, go_to_callback)
        
        # Should return existing frame without creating new one
        self.assertEqual(result, existing_frame)
        mock_ui_builder.create_incident_location_frame.assert_not_called()
    
    @patch('AppMap.AppWidgets.LocationManager.UIBuilder')
    def test_create_incident_frame_default_values(self, mock_ui_builder):
        """Test frame creation with missing location fields."""
        mock_frame = MagicMock()
        mock_ui_builder.create_incident_location_frame.return_value = mock_frame
        
        master = MagicMock()
        location_dict = {}  # Empty dict
        go_to_callback = MagicMock()
        
        result = self.manager.create_incident_frame(master, location_dict, go_to_callback)
        
        # Should handle missing fields with "Unknown"
        call_args = mock_ui_builder.create_incident_location_frame.call_args
        location_text = call_args[0][1]
        self.assertIn("Unknown", location_text)


if __name__ == '__main__':
    unittest.main()
