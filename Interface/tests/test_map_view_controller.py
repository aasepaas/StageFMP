import unittest
from unittest.mock import MagicMock
from AppMap.AppWidgets.MapViewController import MapViewController


class TestMapViewController(unittest.TestCase):
    """Test bbox calculations with real data."""
    def setUp(self):
        self.mock_map_widget = MagicMock()
        self.controller = MapViewController(self.mock_map_widget)
    
    def test_bbox_contains_basic_containment(self):
        """Test basic containment check."""
        outer = (52.0, 4.0, 52.2, 4.2)
        inner = (52.05, 4.05, 52.15, 4.15)
        
        self.assertTrue(MapViewController.bbox_contains(outer, inner))
    
    def test_bbox_contains_exact_match(self):
        """Test that a bbox contains itself."""
        bbox = (52.0, 4.0, 52.2, 4.2)
        self.assertTrue(MapViewController.bbox_contains(bbox, bbox))
    
    def test_bbox_contains_edge_touching(self):
        """Test bbox touching the edge is contained."""
        outer = (52.0, 4.0, 52.2, 4.2)
        inner = (52.0, 4.0, 52.2, 4.2)  # Exact match
        self.assertTrue(MapViewController.bbox_contains(outer, inner))
    
    def test_bbox_contains_extends_outside(self):
        """Test that extending outside is not contained."""
        outer = (52.0, 4.0, 52.2, 4.2)
        inner = (51.9, 4.05, 52.15, 4.15)  # Extends below
        self.assertFalse(MapViewController.bbox_contains(outer, inner))
    
    def test_bbox_contains_extends_right(self):
        """Test that extending to the right is not contained."""
        outer = (52.0, 4.0, 52.2, 4.2)
        inner = (52.05, 4.05, 52.15, 4.25)  # Extends right
        self.assertFalse(MapViewController.bbox_contains(outer, inner))
    
    def test_bbox_contains_multiple_violations(self):
        """Test bbox extending in multiple directions."""
        outer = (52.0, 4.0, 52.2, 4.2)
        inner = (51.95, 3.95, 52.25, 4.25)
        self.assertFalse(MapViewController.bbox_contains(outer, inner))
    
    def test_bbox_contains_much_larger_inner(self):
        """Test that much larger inner bbox is not contained."""
        outer = (52.0, 4.0, 52.1, 4.1)
        inner = (51.0, 3.0, 53.0, 5.0)
        self.assertFalse(MapViewController.bbox_contains(outer, inner))

    
    def test_set_tile_server_normal_map_sets_zoom_limit(self):
        """Test that normal map sets correct zoom limit."""
        self.controller.set_tile_server("Map normaal")
        self.assertEqual(self.controller.max_zoom, 20)
    
    def test_set_tile_server_satellite_map_sets_zoom_limit(self):
        """Test that satellite map sets correct zoom limit."""
        self.controller.set_tile_server("Map satelliet")
        self.assertEqual(self.controller.max_zoom, 21)
    
    def test_set_tile_server_calls_map_widget(self):
        """Test that map widget is updated."""
        self.controller.set_tile_server("Map normaal")
        self.mock_map_widget.set_tile_server.assert_called_once()
    
    def test_set_tile_server_normal_map_url(self):
        """Test that normal map uses correct URL."""
        self.controller.set_tile_server("Map normaal")
        call_args = self.mock_map_widget.set_tile_server.call_args
        url = call_args[0][0]
        self.assertIn("World_Street_Map", url)
    
    def test_set_tile_server_satellite_map_url(self):
        """Test that satellite map uses correct URL."""
        self.controller.set_tile_server("Map satelliet")
        call_args = self.mock_map_widget.set_tile_server.call_args
        url = call_args[0][0]
        self.assertIn("World_Imagery", url)
    
    def test_set_tile_server_passes_max_zoom_parameter(self):
        """Test that max_zoom is correctly passed to map widget."""
        self.controller.set_tile_server("Map normaal")
        call_kwargs = self.mock_map_widget.set_tile_server.call_args[1]
        self.assertEqual(call_kwargs["max_zoom"], 20)

    def test_enforce_zoom_within_limit_no_action(self):
        """Test that zoom within limit is not modified."""
        self.controller.max_zoom = 20
        self.mock_map_widget.zoom = 18
        
        self.controller.enforce_zoom()
        
        self.mock_map_widget.set_zoom.assert_not_called()
    
    def test_enforce_zoom_at_limit_no_action(self):
        """Test that zoom at limit is not modified."""
        self.controller.max_zoom = 20
        self.mock_map_widget.zoom = 20
        
        self.controller.enforce_zoom()
        
        self.mock_map_widget.set_zoom.assert_not_called()
    
    def test_enforce_zoom_exceeds_limit_resets(self):
        """Test that zoom exceeding limit is reduced."""
        self.controller.max_zoom = 20
        self.mock_map_widget.zoom = 22
        
        self.controller.enforce_zoom()
        
        self.mock_map_widget.set_zoom.assert_called_once_with(20)
    
    def test_enforce_zoom_greatly_exceeds_limit(self):
        """Test zoom much higher than limit."""
        self.controller.max_zoom = 20
        self.mock_map_widget.zoom = 30
        
        self.controller.enforce_zoom()
        
        self.mock_map_widget.set_zoom.assert_called_once_with(20)
    
    def test_go_to_coordinates_basic(self):
        """Test navigating to coordinates."""
        self.controller.go_to_coordinates(52.0, 4.0, zoom=19)
        
        self.mock_map_widget.set_position.assert_called_once_with(52.0, 4.0)
        self.mock_map_widget.set_zoom.assert_called_once_with(19)
    
    def test_go_to_coordinates_default_zoom(self):
        """Test that default zoom is 19."""
        self.controller.go_to_coordinates(52.5, 4.5)
        
        calls = self.mock_map_widget.set_zoom.call_args_list
        self.assertEqual(calls[-1][0][0], 19)
    
    def test_go_to_coordinates_custom_zoom(self):
        """Test custom zoom level."""
        self.controller.go_to_coordinates(52.0, 4.0, zoom=15)
        
        self.mock_map_widget.set_zoom.assert_called_with(15)
    
    def test_go_to_coordinates_sets_position_first(self):
        """Test that position is set before zoom."""
        self.controller.go_to_coordinates(52.1, 4.1, zoom=18)
        
        position_call = self.mock_map_widget.set_position.call_args
        zoom_call = self.mock_map_widget.set_zoom.call_args
        
        self.assertEqual(position_call[0], (52.1, 4.1))
        self.assertEqual(zoom_call[0], (18,))

    def test_get_viewport_bbox_invalid_width(self):
        """Test that invalid width returns None."""
        self.mock_map_widget.winfo_width.return_value = 5
        self.mock_map_widget.winfo_height.return_value = 100
        
        result = self.controller.get_viewport_bbox()
        
        self.assertIsNone(result)
    
    def test_get_viewport_bbox_invalid_height(self):
        """Test that invalid height returns None."""
        self.mock_map_widget.winfo_width.return_value = 100
        self.mock_map_widget.winfo_height.return_value = 5
        
        result = self.controller.get_viewport_bbox()
        
        self.assertIsNone(result)
    
    def test_get_viewport_bbox_conversion_error_returns_none(self):
        """Test that conversion errors return None."""
        self.mock_map_widget.winfo_width.return_value = 800
        self.mock_map_widget.winfo_height.return_value = 600
        self.mock_map_widget.convert_canvas_coords_to_decimal_coords.side_effect = Exception()
        
        result = self.controller.get_viewport_bbox()
        
        self.assertIsNone(result)
    
    def test_get_viewport_bbox_success_format(self):
        """Test successful bbox retrieval has correct format."""
        self.mock_map_widget.winfo_width.return_value = 800
        self.mock_map_widget.winfo_height.return_value = 600
        self.mock_map_widget.convert_canvas_coords_to_decimal_coords.side_effect = [
            (52.3, 3.8),  # top-left
            (52.0, 4.2)   # bottom-right
        ]
        
        result = self.controller.get_viewport_bbox()
        
        # bbox format: (lat_min, lon_min, lat_max, lon_max)
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 4)
        self.assertEqual(result[0], 52.0)  # min lat
        self.assertEqual(result[1], 3.8)   # min lon
        self.assertEqual(result[2], 52.3)  # max lat
        self.assertEqual(result[3], 4.2)   # max lon
    
    def test_get_viewport_bbox_min_max_values_correct(self):
        """Test that min/max values are computed correctly."""
        self.mock_map_widget.winfo_width.return_value = 800
        self.mock_map_widget.winfo_height.return_value = 600
        self.mock_map_widget.convert_canvas_coords_to_decimal_coords.side_effect = [
            (52.5, 3.5),  # top-left (higher lat, lower lon)
            (51.5, 4.5)   # bottom-right (lower lat, higher lon)
        ]
        
        result = self.controller.get_viewport_bbox()
        
        self.assertEqual(result[0], 51.5)  # min lat (smallest)
        self.assertEqual(result[1], 3.5)   # min lon (smallest)
        self.assertEqual(result[2], 52.5)  # max lat (largest)
        self.assertEqual(result[3], 4.5)   # max lon (largest)
    

if __name__ == '__main__':
    unittest.main()