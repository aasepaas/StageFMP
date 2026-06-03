import unittest
from AppMap.AppWidgets.PositionCalculator import PositionCalculator


class TestPositionCalculator(unittest.TestCase):
    """Test PositionCalculator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Simple straight line polyline (north to south)
        self.simple_polyline = [
            (52.0, 4.0),
            (52.1, 4.0),
            (52.2, 4.0),
            (52.3, 4.0)
        ]
        
        # More complex polyline
        self.complex_polyline = [
            (52.0, 4.0),
            (52.05, 4.05),
            (52.1, 4.1),
            (52.15, 4.05),
            (52.2, 4.0)
        ]
    
    def test_calculate_positions_returns_list(self):
        """Test that calculate_positions returns a list."""
        result = PositionCalculator.calculate_positions(
            marker_lat=52.05,
            marker_lon=4.0,
            direction=90,
            offset_polyline=self.simple_polyline,
            distance=10,
            amount=3
        )
        self.assertIsInstance(result, list)
    
    def test_calculate_positions_correct_amount(self):
        """Test that the correct number of positions are calculated."""
        amount = 5
        result = PositionCalculator.calculate_positions(
            marker_lat=52.05,
            marker_lon=4.0,
            direction=90,
            offset_polyline=self.simple_polyline,
            distance=10,
            amount=amount
        )
        self.assertEqual(len(result), amount)
    
    def test_calculate_positions_returns_tuples(self):
        """Test that each position is a tuple of (lat, lon, direction)."""
        result = PositionCalculator.calculate_positions(
            marker_lat=52.05,
            marker_lon=4.0,
            direction=45,
            offset_polyline=self.simple_polyline,
            distance=10,
            amount=2
        )
        
        for pos in result:
            self.assertIsInstance(pos, tuple)
            self.assertEqual(len(pos), 3)
            self.assertIsInstance(pos[0], float)  # lat
            self.assertIsInstance(pos[1], float)  # lon
            self.assertEqual(pos[2], 45)  # direction preserved
    
    def test_calculate_positions_preserves_direction(self):
        """Test that marker direction is preserved in all calculated positions."""
        direction = 135
        result = PositionCalculator.calculate_positions(
            marker_lat=52.05,
            marker_lon=4.0,
            direction=direction,
            offset_polyline=self.simple_polyline,
            distance=10,
            amount=3
        )
        
        for _, _, pos_direction in result:
            self.assertEqual(pos_direction, direction)
    
    def test_calculate_positions_zero_amount(self):
        """Test that zero amount returns empty list."""
        result = PositionCalculator.calculate_positions(
            marker_lat=52.05,
            marker_lon=4.0,
            direction=90,
            offset_polyline=self.simple_polyline,
            distance=10,
            amount=0
        )
        self.assertEqual(len(result), 0)
    
    def test_calculate_positions_none_polyline(self):
        """Test that None polyline returns empty list."""
        result = PositionCalculator.calculate_positions(
            marker_lat=52.05,
            marker_lon=4.0,
            direction=90,
            offset_polyline=None,
            distance=10,
            amount=3
        )
        self.assertEqual(len(result), 0)
    
    def test_calculate_positions_with_complex_polyline(self):
        """Test calculation with more complex polyline."""
        result = PositionCalculator.calculate_positions(
            marker_lat=52.1,
            marker_lon=4.1,
            direction=0,
            offset_polyline=self.complex_polyline,
            distance=5,
            amount=2
        )
        
        self.assertEqual(len(result), 2)
        # Verify positions are valid coordinates
        for lat, lon, direction in result:
            self.assertTrue(-90 <= lat <= 90)
            self.assertTrue(-180 <= lon <= 180)
            self.assertEqual(direction, 0)
    
    def test_calculate_positions_different_distances(self):
        """Test that different distances produce different positions."""
        result_dist_5 = PositionCalculator.calculate_positions(
            marker_lat=52.05,
            marker_lon=4.0,
            direction=90,
            offset_polyline=self.simple_polyline,
            distance=5,
            amount=1
        )
        
        result_dist_10 = PositionCalculator.calculate_positions(
            marker_lat=52.05,
            marker_lon=4.0,
            direction=90,
            offset_polyline=self.simple_polyline,
            distance=10,
            amount=1
        )
        
        # Different distances should produce different positions
        self.assertNotEqual(
            result_dist_5[0][:2],  # lat, lon
            result_dist_10[0][:2]
        )


if __name__ == '__main__':
    unittest.main()
