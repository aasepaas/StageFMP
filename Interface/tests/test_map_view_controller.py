import unittest
from unittest.mock import MagicMock
from AppMap.AppWidgets.MapViewController import MapViewController


class TestMapViewController(unittest.TestCase):
    """Test MapViewController class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_map_widget = MagicMock()
        self.controller = MapViewController(self.mock_map_widget)
    
    def test_initialization(self):
        """Test that controller initializes with correct max zoom."""
        self.assertEqual(self.controller.max_zoom, 21)
        self.assertEqual(self.controller.map_widget, self.mock_map_widget)
    
    def test_set_tile_server_normal_map(self):
        """Test setting normal map tile server."""
        self.controller.set_tile_server("Map normaal")
        
        self.assertEqual(self.controller.max_zoom, 20)
        self.mock_map_widget.set_tile_server.assert_called_once()
        
        call_args = self.mock_map_widget.set_tile_server.call_args
        self.assertIn("World_Street_Map", call_args[0][0])
        self.assertEqual(call_args[1]["max_zoom"], 20)
    
    def test_set_tile_server_satellite_map(self):
        """Test setting satellite map tile server."""
        self.controller.set_tile_server("Map satelliet")
        
        self.assertEqual(self.controller.max_zoom, 21)
        self.mock_map_widget.set_tile_server.assert_called_once()
        
        call_args = self.mock_map_widget.set_tile_server.call_args
        self.assertIn("World_Imagery", call_args[0][0])
        self.assertEqual(call_args[1]["max_zoom"], 21)
    
    def test_enforce_zoom_within_limit(self):
        """Test enforce_zoom when zoom is within limit."""
        self.mock_map_widget.zoom = 18
        self.controller.max_zoom = 20
        
        self.controller.enforce_zoom()
        
        self.mock_map_widget.set_zoom.assert_not_called()
    
    def test_enforce_zoom_exceeds_limit(self):
        """Test enforce_zoom when zoom exceeds limit."""
        self.mock_map_widget.zoom = 22
        self.controller.max_zoom = 20
        
        self.controller.enforce_zoom()
        
        self.mock_map_widget.set_zoom.assert_called_once_with(20)
    
    def test_get_viewport_bbox_invalid_dimensions(self):
        """Test get_viewport_bbox with invalid widget dimensions."""
        self.mock_map_widget.winfo_width.return_value = 5
        self.mock_map_widget.winfo_height.return_value = 5
        
        result = self.controller.get_viewport_bbox()
        
        self.assertIsNone(result)
    
    def test_get_viewport_bbox_conversion_error(self):
        """Test get_viewport_bbox when coordinate conversion fails."""
        self.mock_map_widget.winfo_width.return_value = 100
        self.mock_map_widget.winfo_height.return_value = 100
        self.mock_map_widget.convert_canvas_coords_to_decimal_coords.side_effect = Exception()
        
        result = self.controller.get_viewport_bbox()
        
        self.assertIsNone(result)
    
    def test_get_viewport_bbox_success(self):
        """Test successful viewport bbox retrieval."""
        self.mock_map_widget.winfo_width.return_value = 800
        self.mock_map_widget.winfo_height.return_value = 600
        self.mock_map_widget.convert_canvas_coords_to_decimal_coords.side_effect = [
            (52.3, 3.8),  # top-left (0, 0)
            (52.0, 4.2)   # bottom-right (800, 600)
        ]
        
        result = self.controller.get_viewport_bbox()
        
        self.assertIsNotNone(result)
        self.assertEqual(result[0], 52.0)  # min lat
        self.assertEqual(result[1], 3.8)   # min lon
        self.assertEqual(result[2], 52.3)  # max lat
        self.assertEqual(result[3], 4.2)   # max lon
    
    def test_bbox_contains_inner_within_outer(self):
        """Test bbox_contains when inner is within outer."""
        outer = (52.0, 4.0, 52.2, 4.2)
        inner = (52.05, 4.05, 52.15, 4.15)
        
        result = MapViewController.bbox_contains(outer, inner)
        
        self.assertTrue(result)
    
    def test_bbox_contains_inner_outside_outer(self):
        """Test bbox_contains when inner extends outside outer."""
        outer = (52.0, 4.0, 52.2, 4.2)
        inner = (51.9, 3.9, 52.15, 4.15)
        
        result = MapViewController.bbox_contains(outer, inner)
        
        self.assertFalse(result)
    
    def test_bbox_contains_identical(self):
        """Test bbox_contains with identical boxes."""
        bbox = (52.0, 4.0, 52.2, 4.2)
        
        result = MapViewController.bbox_contains(bbox, bbox)
        
        self.assertTrue(result)
    
    def test_go_to_coordinates(self):
        """Test navigating to specific coordinates."""
        self.controller.go_to_coordinates(52.0, 4.0, zoom=19)
        
        self.mock_map_widget.set_position.assert_called_once_with(52.0, 4.0)
        self.mock_map_widget.set_zoom.assert_called_once_with(19)
    
    def test_go_to_coordinates_default_zoom(self):
        """Test go_to_coordinates with default zoom."""
        self.controller.go_to_coordinates(52.1, 4.1)
        
        self.mock_map_widget.set_position.assert_called_once_with(52.1, 4.1)
        self.mock_map_widget.set_zoom.assert_called_once_with(19)


if __name__ == '__main__':
    unittest.main()
