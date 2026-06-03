import unittest
from unittest.mock import patch, MagicMock
import json
from AppMap.AppWidgets.RoadDataManager import RoadDataManager


class TestRoadDataManager(unittest.TestCase):
    """Test RoadDataManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.manager = RoadDataManager()
    
    def test_initialization(self):
        """Test that manager initializes with empty data."""
        self.assertEqual(self.manager.road_polylines, [])
        self.assertIsNone(self.manager.road_fetch_bbox)
        self.assertFalse(self.manager.road_fetch_running)
    
    def test_has_data_empty(self):
        """Test has_data returns False when no data."""
        self.assertFalse(self.manager.has_data())
    
    def test_has_data_with_polylines(self):
        """Test has_data returns True when polylines exist."""
        self.manager.road_polylines = [[(52.0, 4.0), (52.1, 4.1)]]
        self.assertTrue(self.manager.has_data())
    
    def test_clear_cache(self):
        """Test clearing cached data."""
        self.manager.road_polylines = [[(52.0, 4.0), (52.1, 4.1)]]
        self.manager.road_fetch_bbox = (52.0, 4.0, 52.1, 4.1)
        
        self.manager.clear_cache()
        
        self.assertEqual(self.manager.road_polylines, [])
        self.assertIsNone(self.manager.road_fetch_bbox)
    
    def test_parse_features_empty(self):
        """Test parsing empty features list."""
        result = self.manager._parse_features([])
        self.assertEqual(result, [])
    
    def test_parse_features_linestring(self):
        """Test parsing LineString geometry."""
        features = [
            {
                "properties": {"dienstnaam": "RWS_TEST"},
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[4.0, 52.0], [4.1, 52.1], [4.2, 52.2]]
                }
            }
        ]
        
        result = self.manager._parse_features(features)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], [(52.0, 4.0), (52.1, 4.1), (52.2, 4.2)])
    
    def test_parse_features_multilinestring(self):
        """Test parsing MultiLineString geometry."""
        features = [
            {
                "properties": {"dienstnaam": "RWS_TEST"},
                "geometry": {
                    "type": "MultiLineString",
                    "coordinates": [
                        [[4.0, 52.0], [4.1, 52.1]],
                        [[4.2, 52.2], [4.3, 52.3]]
                    ]
                }
            }
        ]
        
        result = self.manager._parse_features(features)
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], [(52.0, 4.0), (52.1, 4.1)])
        self.assertEqual(result[1], [(52.2, 4.2), (52.3, 4.3)])
    
    def test_parse_features_filters_non_rws(self):
        """Test that non-RWS features are filtered out."""
        features = [
            {
                "properties": {"dienstnaam": "RWS_TEST"},
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[4.0, 52.0], [4.1, 52.1]]
                }
            },
            {
                "properties": {"dienstnaam": "OTHER_ROAD"},
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[4.2, 52.2], [4.3, 52.3]]
                }
            }
        ]
        
        result = self.manager._parse_features(features)
        
        self.assertEqual(len(result), 1)  # Only RWS feature
    
    def test_parse_features_ignores_invalid_geometry(self):
        """Test that invalid geometries are ignored."""
        features = [
            {
                "properties": {"dienstnaam": "RWS_TEST"},
                "geometry": None
            },
            {
                "properties": {"dienstnaam": "RWS_TEST"},
                "geometry": {
                    "type": "Point",
                    "coordinates": [4.0, 52.0]
                }
            }
        ]
        
        result = self.manager._parse_features(features)
        
        self.assertEqual(len(result), 0)
    
    def test_parse_features_requires_minimum_points(self):
        """Test that polylines with < 2 points are ignored."""
        features = [
            {
                "properties": {"dienstnaam": "RWS_TEST"},
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[4.0, 52.0]]  # Only 1 point
                }
            }
        ]
        
        result = self.manager._parse_features(features)
        
        self.assertEqual(len(result), 0)
    
    @patch('requests.get')
    def test_fetch_roads_thread_success(self, mock_get):
        """Test successful road data fetch."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "features": [
                {
                    "properties": {"dienstnaam": "RWS_TEST"},
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
        
        self.assertEqual(len(self.manager.road_polylines), 1)
        self.assertEqual(self.manager.road_fetch_bbox, bbox)
        self.assertFalse(self.manager.road_fetch_running)
    
    @patch('requests.get')
    def test_fetch_roads_thread_network_error(self, mock_get):
        """Test handling of network errors."""
        mock_get.side_effect = Exception("Network error")
        
        bbox = (52.0, 4.0, 52.1, 4.1)
        self.manager.road_fetch_running = True
        self.manager.fetch_roads_thread(bbox)
        
        # Should handle error gracefully
        self.assertFalse(self.manager.road_fetch_running)
        self.assertEqual(self.manager.road_polylines, [])
    
    @patch('requests.get')
    def test_fetch_roads_thread_invalid_response(self, mock_get):
        """Test handling of invalid API response."""
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_get.return_value = mock_response
        
        bbox = (52.0, 4.0, 52.1, 4.1)
        self.manager.road_fetch_running = True
        self.manager.fetch_roads_thread(bbox)
        
        # Should handle gracefully with no features
        self.assertEqual(self.manager.road_polylines, [])
        self.assertFalse(self.manager.road_fetch_running)


if __name__ == '__main__':
    unittest.main()
