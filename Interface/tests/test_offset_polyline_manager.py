import unittest
import math
from AppMap.AppWidgets.OffsetPolylineManager import OffsetPolylineManager


class TestOffsetPolylineManager(unittest.TestCase):
    """Test OffsetPolylineManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.manager = OffsetPolylineManager()
        
        # Simple horizontal polyline
        self.horizontal_polyline = [
            (52.0, 4.0),
            (52.0, 4.1),
            (52.0, 4.2),
            (52.0, 4.3)
        ]
        
        # Vertical polyline
        self.vertical_polyline = [
            (52.0, 4.0),
            (52.1, 4.0),
            (52.2, 4.0),
            (52.3, 4.0)
        ]
        
        # Multiple polylines
        self.polylines = [self.horizontal_polyline, self.vertical_polyline]
    
    def test_initialization(self):
        """Test that manager initializes with None offset polyline."""
        self.assertIsNone(self.manager.offset_polyline_single)
    
    def test_find_nearest_polyline_empty_list(self):
        """Test finding nearest polyline with empty list returns None."""
        result = self.manager.find_nearest_polyline(52.0, 4.0, [])
        self.assertIsNone(result)
    
    def test_find_nearest_polyline_single_polyline(self):
        """Test finding nearest with single polyline returns that polyline."""
        result = self.manager.find_nearest_polyline(52.05, 4.05, [self.horizontal_polyline])
        self.assertEqual(result, self.horizontal_polyline)
    
    def test_find_nearest_polyline_multiple_polylines(self):
        """Test finding nearest polyline from multiple options."""
        # Point closer to horizontal polyline
        result = self.manager.find_nearest_polyline(52.0, 4.15, self.polylines)
        self.assertEqual(result, self.horizontal_polyline)
        
        # Point closer to vertical polyline
        result = self.manager.find_nearest_polyline(52.15, 4.0, self.polylines)
        self.assertEqual(result, self.vertical_polyline)
    
    def test_compute_offset_vector_returns_tuple(self):
        """Test that compute_offset_vector returns a tuple."""
        result = self.manager.compute_offset_vector(
            52.05, 4.05, self.horizontal_polyline
        )
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
    
    def test_compute_offset_vector_values_are_numeric(self):
        """Test that offset vector values are numeric."""
        offset_x, offset_y = self.manager.compute_offset_vector(
            52.05, 4.05, self.horizontal_polyline
        )
        self.assertIsInstance(offset_x, (int, float))
        self.assertIsInstance(offset_y, (int, float))
    
    def test_compute_offset_vector_on_line(self):
        """Test offset vector when point is on the polyline."""
        # Point on the horizontal line should have near-zero offset_y
        offset_x, offset_y = self.manager.compute_offset_vector(
            52.0, 4.1, self.horizontal_polyline
        )
        # Should be very close to zero (on the line)
        self.assertLess(abs(offset_y), 0.1)
    
    def test_build_offset_polylines_none_polylines(self):
        """Test building offset with empty polylines."""
        self.manager.build_offset_polylines(52.05, 4.05, [])
        self.assertIsNone(self.manager.offset_polyline_single)
    
    def test_build_offset_polylines_on_road(self):
        """Test that marker on road uses original polyline."""
        self.manager.build_offset_polylines(52.0, 4.1, [self.horizontal_polyline])
        # If marker is on the road (offset < 0.5), should use original
        self.assertIsNotNone(self.manager.offset_polyline_single)
    
    def test_snap_to_offset_polyline_none(self):
        """Test snapping when offset polyline is None."""
        lat, lon = self.manager.snap_to_offset_polyline(52.05, 4.05)
        # Should return original coordinates
        self.assertEqual(lat, 52.05)
        self.assertEqual(lon, 4.05)
    
    def test_snap_to_offset_polyline_returns_coordinates(self):
        """Test that snap returns valid coordinates."""
        self.manager.offset_polyline_single = self.horizontal_polyline
        lat, lon = self.manager.snap_to_offset_polyline(52.05, 4.15)
        
        self.assertIsInstance(lat, float)
        self.assertIsInstance(lon, float)
        self.assertTrue(-90 <= lat <= 90)
        self.assertTrue(-180 <= lon <= 180)
    
    def test_get_offset_polyline(self):
        """Test getting offset polyline."""
        self.assertIsNone(self.manager.get_offset_polyline())
        
        self.manager.offset_polyline_single = self.horizontal_polyline
        result = self.manager.get_offset_polyline()
        self.assertEqual(result, self.horizontal_polyline)
    
    def test_clear_offset_polyline(self):
        """Test clearing offset polyline."""
        self.manager.offset_polyline_single = self.horizontal_polyline
        self.manager.clear()
        self.assertIsNone(self.manager.offset_polyline_single)


if __name__ == '__main__':
    unittest.main()
