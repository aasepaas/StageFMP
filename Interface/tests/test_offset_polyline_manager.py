import unittest
import math
from unittest.mock import MagicMock, patch
from AppMap.AppWidgets.OffsetPolylineManager import OffsetPolylineManager


class TestOffsetPolylineManager(unittest.TestCase):
    """Test finding nearest polyline to a point."""
    
    def setUp(self):
        self.manager = OffsetPolylineManager()
        
        # Test polylines
        self.poly_horizontal = [(52.0, 4.0), (52.0, 4.1), (52.0, 4.2)]
        self.poly_vertical = [(52.0, 4.0), (52.1, 4.0), (52.2, 4.0)]
        self.poly_diagonal = [(52.0, 4.0), (52.1, 4.1), (52.2, 4.2)]
        self.poly_simple = [(52.0, 4.0), (52.0, 4.1), (52.0, 4.2)]
        self.poly_horizontal = [(52.0, 4.0), (52.0, 4.1), (52.0, 4.2)]
    
    def test_find_nearest_polyline_empty_list_returns_none(self):
        """Test that empty polyline list returns None."""
        result = self.manager.find_nearest_polyline(52.0, 4.0, [])
        self.assertIsNone(result)
    
    def test_find_nearest_polyline_single_polyline(self):
        """Test with single polyline returns that polyline."""
        result = self.manager.find_nearest_polyline(
            52.05, 4.05,
            [self.poly_horizontal]
        )
        self.assertEqual(result, self.poly_horizontal)
    
    def test_find_nearest_polyline_chooses_closest(self):
        """Test that the nearest polyline is selected."""
        # Point close to horizontal polyline
        result = self.manager.find_nearest_polyline(
            52.0, 4.15,
            [self.poly_horizontal, self.poly_vertical, self.poly_diagonal]
        )
        self.assertEqual(result, self.poly_horizontal)
    
    def test_find_nearest_polyline_vertical_preference(self):
        """Test selecting vertical polyline when it's closest."""
        # Point close to vertical line
        result = self.manager.find_nearest_polyline(
            52.15, 4.0,
            [self.poly_horizontal, self.poly_vertical, self.poly_diagonal]
        )
        self.assertEqual(result, self.poly_vertical)
    
    def test_find_nearest_polyline_returns_not_none(self):
        """Test that result is one of the input polylines."""
        polylines = [self.poly_horizontal, self.poly_vertical, self.poly_diagonal]
        result = self.manager.find_nearest_polyline(52.1, 4.1, polylines)
        self.assertIn(result, polylines)
    
    def test_compute_offset_vector_returns_tuple(self):
        """Test that offset vector is a tuple."""
        result = self.manager.compute_offset_vector(52.05, 4.05, self.poly_horizontal)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
    
    def test_compute_offset_vector_returns_numeric(self):
        """Test that offset values are numeric."""
        offset_x, offset_y = self.manager.compute_offset_vector(52.05, 4.05, self.poly_horizontal)
        self.assertIsInstance(offset_x, (int, float))
        self.assertIsInstance(offset_y, (int, float))
    
    def test_compute_offset_vector_on_line_near_zero(self):
        """Test that point on line has near-zero perpendicular offset."""
        # Point on the horizontal line (52.0 is on the line)
        offset_x, offset_y = self.manager.compute_offset_vector(52.0, 4.15, self.poly_horizontal)
        
        # Y offset should be near zero (on the line)
        self.assertLess(abs(offset_y), 0.01)
    
    def test_compute_offset_vector_off_line_non_zero(self):
        """Test that point off line has non-zero offset."""
        # Point clearly off the line
        offset_x, offset_y = self.manager.compute_offset_vector(52.1, 4.1, self.poly_horizontal)
        
        # Y offset should be significant (off the line)
        self.assertGreater(abs(offset_y), 0.001)
    
    def test_compute_offset_vector_magnitude_reasonable(self):
        """Test that offset magnitude is reasonable."""
        offset_x, offset_y = self.manager.compute_offset_vector(52.05, 4.05, self.poly_horizontal)
        
        magnitude = math.sqrt(offset_x**2 + offset_y**2)
        # Magnitude should be less than 10000 meters (reasonable for local coordinates)
        self.assertLess(magnitude, 10000)

    
    @patch.object(OffsetPolylineManager, 'find_nearest_polyline')
    @patch.object(OffsetPolylineManager, 'compute_offset_vector')
    def test_build_offset_polylines_none_nearest_returns_none(self, mock_offset, mock_nearest):
        """Test that None nearest polyline results in None offset."""
        mock_nearest.return_value = None
        
        self.manager.build_offset_polylines(52.05, 4.05, [self.poly_simple])
        
        self.assertIsNone(self.manager.offset_polyline_single)
    
    @patch.object(OffsetPolylineManager, 'find_nearest_polyline')
    @patch.object(OffsetPolylineManager, 'compute_offset_vector')
    def test_build_offset_polylines_on_road_uses_original(self, mock_offset, mock_nearest):
        """Test that marker on road uses original polyline."""
        mock_nearest.return_value = self.poly_simple
        # Small offset (less than 0.5)
        mock_offset.return_value = (0.1, 0.1)
        
        self.manager.build_offset_polylines(52.0, 4.1, [self.poly_simple])
        
        self.assertEqual(self.manager.offset_polyline_single, self.poly_simple)
    
    @patch('AppMap.AppWidgets.OffsetPolylineManager.offset_polyline')
    @patch.object(OffsetPolylineManager, 'find_nearest_polyline')
    @patch.object(OffsetPolylineManager, 'compute_offset_vector')
    def test_build_offset_polylines_large_offset_applies_offset(self, mock_offset_vec, 
                                                                 mock_nearest, mock_offset_func):
        """Test that large offset triggers offset_polyline function."""
        mock_nearest.return_value = self.poly_simple
        # Large offset (greater than 0.5)
        mock_offset_vec.return_value = (5.0, 5.0)
        
        mock_offset_func.return_value = [(52.05, 4.0), (52.05, 4.1)]
        
        self.manager.build_offset_polylines(52.05, 4.05, [self.poly_simple])
        
        # Should call offset_polyline function
        mock_offset_func.assert_called_once()

    
    def test_snap_to_offset_polyline_none_returns_original(self):
        """Test that snapping with None polyline returns original coords."""
        self.manager.offset_polyline_single = None
        
        lat, lon = self.manager.snap_to_offset_polyline(52.05, 4.05)
        
        self.assertEqual(lat, 52.05)
        self.assertEqual(lon, 4.05)
    
    @patch('AppMap.AppWidgets.OffsetPolylineManager._project_onto_polyline')
    def test_snap_to_offset_polyline_returns_coordinates(self, mock_project):
        """Test that snapping returns valid coordinates."""
        self.manager.offset_polyline_single = self.poly_simple
        mock_project.return_value = (52.0, 4.15, 15.0, 10.0, 0.5)
        
        lat, lon = self.manager.snap_to_offset_polyline(52.05, 4.05)
        
        self.assertEqual(lat, 52.0)
        self.assertEqual(lon, 4.15)

    
    def test_initial_offset_polyline_is_none(self):
        """Test that offset polyline starts as None."""
        self.assertIsNone(self.manager.offset_polyline_single)
    
    def test_get_offset_polyline_returns_current(self):
        """Test that get returns current polyline."""
        polyline = [(52.0, 4.0), (52.1, 4.1)]
        self.manager.offset_polyline_single = polyline
        
        result = self.manager.get_offset_polyline()
        self.assertEqual(result, polyline)
    
    def test_clear_resets_polyline(self):
        """Test that clear sets polyline to None."""
        self.manager.offset_polyline_single = [(52.0, 4.0), (52.1, 4.1)]
        
        self.manager.clear()
        
        self.assertIsNone(self.manager.offset_polyline_single)


if __name__ == '__main__':
    unittest.main()