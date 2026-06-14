import unittest
from unittest.mock import patch, MagicMock
from AppMap.AppWidgets.LocationManager import LocationManager


class TestLocationManager(unittest.TestCase):
    """Test geocoding logic with minimal mocking."""
    
    def setUp(self):
        self.manager = LocationManager()
    
    @patch('AppMap.AppWidgets.LocationManager.Nominatim')
    def test_reverse_geocode_extracts_address_fields(self, mock_nominatim_class):
        """Test that reverse_geocode correctly extracts address components."""
        mock_location = MagicMock()
        mock_location.raw = {
            "address": {
                "road": "Delftseweg",
                "city": "Delft",
                "state": "South Holland",
                "postcode": "2629 JD"
            }
        }
        
        mock_geolocator = MagicMock()
        mock_geolocator.reverse.return_value = mock_location
        mock_nominatim_class.return_value = mock_geolocator
        
        manager = LocationManager()
        result = manager.reverse_geocode(52.0, 4.0)
        
        # Verify all fields are extracted
        self.assertEqual(result["road"], "Delftseweg")
        self.assertEqual(result["city"], "Delft")
        self.assertEqual(result["state"], "South Holland")
        self.assertEqual(result["postcode"], "2629 JD")
    
    @patch('AppMap.AppWidgets.LocationManager.Nominatim')
    def test_reverse_geocode_handles_partial_address(self, mock_nominatim_class):
        """Test that partial addresses are handled gracefully."""
        mock_location = MagicMock()
        mock_location.raw = {
            "address": {
                "road": "Main Street",
                # city and state missing
            }
        }
        
        mock_geolocator = MagicMock()
        mock_geolocator.reverse.return_value = mock_location
        mock_nominatim_class.return_value = mock_geolocator
        
        manager = LocationManager()
        result = manager.reverse_geocode(52.0, 4.0)
        
        self.assertEqual(result["road"], "Main Street")
        # Missing fields should not cause errors
        self.assertNotIn("city", result)
    
    @patch('AppMap.AppWidgets.LocationManager.Nominatim')
    def test_reverse_geocode_returns_empty_on_exception(self, mock_nominatim_class):
        """Test that exceptions during geocoding return empty dict."""
        mock_geolocator = MagicMock()
        mock_geolocator.reverse.side_effect = Exception("Service unavailable")
        mock_nominatim_class.return_value = mock_geolocator
        
        manager = LocationManager()
        result = manager.reverse_geocode(52.0, 4.0)
        
        self.assertEqual(result, {})
    
    @patch('AppMap.AppWidgets.LocationManager.Nominatim')
    def test_reverse_geocode_returns_empty_when_no_address(self, mock_nominatim_class):
        """Test handling of response with no address data."""
        mock_location = MagicMock()
        mock_location.raw = {}  # No address key
        
        mock_geolocator = MagicMock()
        mock_geolocator.reverse.return_value = mock_location
        mock_nominatim_class.return_value = mock_geolocator
        
        manager = LocationManager()
        result = manager.reverse_geocode(52.0, 4.0)
        
        self.assertEqual(result, {})

    
    @patch('AppMap.AppWidgets.LocationManager.UIBuilder')
    def test_create_incident_frame_builds_text_correctly(self, mock_ui_builder):
        """Test that location text is formatted correctly."""
        mock_frame = MagicMock()
        mock_ui_builder.create_incident_location_frame.return_value = mock_frame
        
        master = MagicMock()
        location_dict = {
            "road": "A1 highway",
            "city": "Amsterdam",
            "state": "North Holland"
        }
        callback = MagicMock()
        
        self.manager.create_incident_frame(master, location_dict, callback)
        
        # Verify the correct text format was passed
        call_args = mock_ui_builder.create_incident_location_frame.call_args
        location_text = call_args[0][1]
        self.assertEqual(location_text, "A1 highway, Amsterdam, North Holland")
    
    @patch('AppMap.AppWidgets.LocationManager.UIBuilder')
    def test_create_incident_frame_uses_unknown_for_missing_fields(self, mock_ui_builder):
        """Test that missing fields are replaced with 'Unknown'."""
        mock_frame = MagicMock()
        mock_ui_builder.create_incident_location_frame.return_value = mock_frame
        
        master = MagicMock()
        location_dict = {"road": "Main Street"}  # city and state missing
        callback = MagicMock()
        
        self.manager.create_incident_frame(master, location_dict, callback)
        
        call_args = mock_ui_builder.create_incident_location_frame.call_args
        location_text = call_args[0][1]
        self.assertEqual(location_text, "Main Street, Unknown, Unknown")
    
    @patch('AppMap.AppWidgets.LocationManager.UIBuilder')
    def test_create_incident_frame_returns_frame(self, mock_ui_builder):
        """Test that the created frame is returned."""
        mock_frame = MagicMock()
        mock_ui_builder.create_incident_location_frame.return_value = mock_frame
        
        master = MagicMock()
        location_dict = {"road": "Test", "city": "City", "state": "State"}
        callback = MagicMock()
        
        result = self.manager.create_incident_frame(master, location_dict, callback)
        
        self.assertEqual(result, mock_frame)
        self.assertEqual(self.manager.incident_frame, mock_frame)
    
    @patch('AppMap.AppWidgets.LocationManager.UIBuilder')
    def test_create_incident_frame_returns_existing_without_rebuild(self, mock_ui_builder):
        """Test that existing frame is returned without rebuilding."""
        existing_frame = MagicMock()
        self.manager.incident_frame = existing_frame
        
        master = MagicMock()
        location_dict = {"road": "Test", "city": "City", "state": "State"}
        callback = MagicMock()
        
        result = self.manager.create_incident_frame(master, location_dict, callback)
        
        self.assertEqual(result, existing_frame)
        # Should not create a new frame
        mock_ui_builder.create_incident_location_frame.assert_not_called()
    
    def test_destroy_incident_frame_when_none(self):
        """Test destroying when no frame exists."""
        # Should not raise any error
        self.manager.destroy_incident_frame()
        self.assertIsNone(self.manager.incident_frame)
    
    def test_destroy_incident_frame_when_exists(self):
        """Test properly destroying existing frame."""
        mock_frame = MagicMock()
        self.manager.incident_frame = mock_frame
        
        self.manager.destroy_incident_frame()
        
        # Verify cleanup calls
        mock_frame.grid_forget.assert_called_once()
        mock_frame.destroy.assert_called_once()
        self.assertIsNone(self.manager.incident_frame)
    
    def test_destroy_incident_frame_idempotent(self):
        """Test that destroying twice doesn't cause errors."""
        mock_frame = MagicMock()
        self.manager.incident_frame = mock_frame
        
        self.manager.destroy_incident_frame()
        self.manager.destroy_incident_frame()  # Second call should be safe
        
        self.assertIsNone(self.manager.incident_frame)


if __name__ == '__main__':
    unittest.main()