import unittest
from unittest.mock import patch, MagicMock
from AppMap.AppWidgets.RoadDataManager import RoadDataManager


class TestRoadDataManager(unittest.TestCase):
    """Test real data parsing logic without mocking internal methods."""
    
    def setUp(self):
        self.manager = RoadDataManager()
    
    def test_parse_linestring_coordinates_conversion(self):
        """Test that coordinates are correctly converted from [lon,lat] to (lat,lon)."""
        features = [
            {
                "properties": {"dienstnaam": "RWS_A1"},
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[4.0, 52.0], [4.1, 52.1], [4.2, 52.2]]
                }
            }
        ]
        
        result = self.manager._parse_features(features)
        
        # Verify coordinates are swapped correctly
        self.assertEqual(result[0][0], (52.0, 4.0))
        self.assertEqual(result[0][1], (52.1, 4.1))
        self.assertEqual(result[0][2], (52.2, 4.2))
    
    def test_parse_multilinestring_creates_separate_polylines(self):
        """Test that MultiLineString creates separate polyline segments."""
        features = [
            {
                "properties": {"dienstnaam": "RWS_A2"},
                "geometry": {
                    "type": "MultiLineString",
                    "coordinates": [
                        [[4.0, 52.0], [4.1, 52.1]],
                        [[4.2, 52.2], [4.3, 52.3]],
                        [[4.4, 52.4], [4.5, 52.5]]
                    ]
                }
            }
        ]
        
        result = self.manager._parse_features(features)
        
        # Each segment becomes a separate polyline
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0], [(52.0, 4.0), (52.1, 4.1)])
        self.assertEqual(result[1], [(52.2, 4.2), (52.3, 4.3)])
        self.assertEqual(result[2], [(52.4, 4.4), (52.5, 4.5)])
    
    def test_parse_filters_non_rws_services(self):
        """Test that features without RWS prefix are filtered out."""
        features = [
            {
                "properties": {"dienstnaam": "RWS_valid"},
                "geometry": {"type": "LineString", "coordinates": [[4.0, 52.0], [4.1, 52.1]]}
            },
            {
                "properties": {"dienstnaam": "LOCAL_road"},
                "geometry": {"type": "LineString", "coordinates": [[4.2, 52.2], [4.3, 52.3]]}
            },
            {
                "properties": {"dienstnaam": "RWS_also_valid"},
                "geometry": {"type": "LineString", "coordinates": [[4.4, 52.4], [4.5, 52.5]]}
            }
        ]
        
        result = self.manager._parse_features(features)
        
        # Only RWS features should be included
        self.assertEqual(len(result), 2)
    
    def test_parse_ignores_single_point_polylines(self):
        """Test that polylines with less than 2 points are rejected."""
        features = [
            {
                "properties": {"dienstnaam": "RWS_test"},
                "geometry": {"type": "LineString", "coordinates": [[4.0, 52.0]]}
            }
        ]
        
        result = self.manager._parse_features(features)
        self.assertEqual(len(result), 0)
    
    def test_parse_handles_missing_geometry(self):
        """Test that features with no geometry are skipped."""
        features = [
            {
                "properties": {"dienstnaam": "RWS_test"},
                "geometry": None
            },
            {
                "properties": {"dienstnaam": "RWS_valid"},
                "geometry": {"type": "LineString", "coordinates": [[4.0, 52.0], [4.1, 52.1]]}
            }
        ]
        
        result = self.manager._parse_features(features)
        self.assertEqual(len(result), 1)
    
    def test_parse_ignores_invalid_geometry_types(self):
        """Test that non-LineString/MultiLineString geometries are ignored."""
        features = [
            {
                "properties": {"dienstnaam": "RWS_point"},
                "geometry": {"type": "Point", "coordinates": [4.0, 52.0]}
            },
            {
                "properties": {"dienstnaam": "RWS_polygon"},
                "geometry": {"type": "Polygon", "coordinates": [[[4.0, 52.0], [4.1, 52.1], [4.0, 52.0]]]}
            },
            {
                "properties": {"dienstnaam": "RWS_valid"},
                "geometry": {"type": "LineString", "coordinates": [[4.0, 52.0], [4.1, 52.1]]}
            }
        ]
        
        result = self.manager._parse_features(features)
        self.assertEqual(len(result), 1)

    
    def test_initial_state_empty(self):
        """Test that manager starts with empty state."""
        self.assertEqual(self.manager.road_polylines, [])
        self.assertIsNone(self.manager.road_fetch_bbox)
        self.assertFalse(self.manager.road_fetch_running)
    
    def test_has_data_reflects_polylines_state(self):
        """Test has_data() correctly reflects polyline presence."""
        self.assertFalse(self.manager.has_data())
        
        self.manager.road_polylines = [[(52.0, 4.0), (52.1, 4.1)]]
        self.assertTrue(self.manager.has_data())
        
        self.manager.road_polylines = []
        self.assertFalse(self.manager.has_data())
    
    def test_clear_cache_resets_all_data(self):
        """Test that clear_cache completely resets the manager."""
        self.manager.road_polylines = [[(52.0, 4.0), (52.1, 4.1)]]
        self.manager.road_fetch_bbox = (52.0, 4.0, 52.1, 4.1)
        
        self.manager.clear_cache()
        
        self.assertEqual(self.manager.road_polylines, [])
        self.assertIsNone(self.manager.road_fetch_bbox)

    
    @patch('requests.get')
    def test_fetch_roads_parses_valid_response(self, mock_get):
        """Test that valid WFS response is correctly parsed."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "features": [
                {
                    "properties": {"dienstnaam": "RWS_A1"},
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [[4.0, 52.0], [4.1, 52.1]]
                    }
                }
            ]
        }
        mock_get.return_value = mock_response
        
        bbox = (52.0, 4.0, 52.1, 4.1)
        self.manager.road_fetch_running = True
        self.manager.fetch_roads_thread(bbox)
        
        # Verify data was stored
        self.assertEqual(len(self.manager.road_polylines), 1)
        self.assertEqual(self.manager.road_polylines[0], [(52.0, 4.0), (52.1, 4.1)])
        self.assertEqual(self.manager.road_fetch_bbox, bbox)
    
    @patch('requests.get')
    def test_fetch_roads_handles_empty_response(self, mock_get):
        """Test handling of response with no features."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"features": []}
        mock_get.return_value = mock_response
        
        bbox = (52.0, 4.0, 52.1, 4.1)
        self.manager.road_fetch_running = True
        self.manager.fetch_roads_thread(bbox)
        
        self.assertEqual(self.manager.road_polylines, [])
    
    @patch('requests.get')
    def test_fetch_roads_handles_http_error(self, mock_get):
        """Test graceful handling of HTTP errors."""
        mock_get.side_effect = Exception("Connection timeout")
        
        bbox = (52.0, 4.0, 52.1, 4.1)
        self.manager.road_fetch_running = True
        self.manager.fetch_roads_thread(bbox)
        
        # Should set running to False even on error
        self.assertFalse(self.manager.road_fetch_running)
        self.assertEqual(self.manager.road_polylines, [])
    
    @patch('requests.get')
    def test_fetch_roads_sets_bbox(self, mock_get):
        """Test that bbox is correctly stored after fetch."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"features": []}
        mock_get.return_value = mock_response
        
        bbox = (52.5, 4.5, 52.8, 4.8)
        self.manager.road_fetch_running = True
        self.manager.fetch_roads_thread(bbox)
        
        self.assertEqual(self.manager.road_fetch_bbox, bbox)
    
    @patch('requests.get')
    def test_fetch_roads_resets_running_flag(self, mock_get):
        """Test that running flag is always reset after fetch."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"features": []}
        mock_get.return_value = mock_response
        
        self.manager.road_fetch_running = True
        self.manager.fetch_roads_thread((52.0, 4.0, 52.1, 4.1))
        
        self.assertFalse(self.manager.road_fetch_running)


if __name__ == '__main__':
    unittest.main()