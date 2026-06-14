import unittest
from unittest.mock import patch, MagicMock
from AppMap.AppWidgets.PositionCalculator import PositionCalculator


class TestPositionCalculator(unittest.TestCase):
    """Test basic position calculation."""
    
    def setUp(self):
        # Simple test polylines
        self.poly_straight = [(52.0, 4.0), (52.1, 4.0), (52.2, 4.0), (52.3, 4.0)]
        self.poly_short = [(52.0, 4.0), (52.05, 4.0), (52.1, 4.0)]
        self.poly_straight = [(52.0, 4.0), (52.1, 4.0), (52.2, 4.0), (52.3, 4.0)]
        self.polyline_north_south = [
            (52.0, 4.0), (52.05, 4.0), (52.1, 4.0),
            (52.15, 4.0), (52.2, 4.0)
        ]
        self.polyline_diagonal = [
            (52.0, 4.0), (52.05, 4.05), (52.1, 4.1),
            (52.15, 4.15), (52.2, 4.2)
        ]
    
    @patch('AppMap.AppWidgets.PositionCalculator._project_onto_polyline')
    @patch('AppMap.AppWidgets.PositionCalculator._point_along_polyline')
    def test_calculate_positions_returns_list(self, mock_point, mock_project):
        """Test that function returns a list."""
        mock_project.return_value = (52.0, 4.0, 0.0, 0.0, 0.0)
        mock_point.return_value = (52.05, 4.0)
        
        result = PositionCalculator.calculate_positions(
            52.0, 4.0, 90, self.poly_straight, distance=10, amount=3
        )
        
        self.assertIsInstance(result, list)
    
    @patch('AppMap.AppWidgets.PositionCalculator._project_onto_polyline')
    @patch('AppMap.AppWidgets.PositionCalculator._point_along_polyline')
    def test_calculate_positions_correct_amount(self, mock_point, mock_project):
        """Test that correct number of positions are generated."""
        mock_project.return_value = (52.0, 4.0, 0.0, 0.0, 0.0)
        mock_point.side_effect = [
            (52.1, 4.0),
            (52.2, 4.0),
            (52.3, 4.0),
            (52.4, 4.0),
            (52.5, 4.0)
        ]
        
        result = PositionCalculator.calculate_positions(
            52.0, 4.0, 90, self.poly_straight, distance=10, amount=5
        )
        
        self.assertEqual(len(result), 5)
    
    @patch('AppMap.AppWidgets.PositionCalculator._project_onto_polyline')
    @patch('AppMap.AppWidgets.PositionCalculator._point_along_polyline')
    def test_calculate_positions_zero_amount(self, mock_point, mock_project):
        """Test that zero amount returns empty list."""
        mock_project.return_value = (52.0, 4.0, 0.0, 0.0, 0.0)
        
        result = PositionCalculator.calculate_positions(
            52.0, 4.0, 90, self.poly_straight, distance=10, amount=0
        )
        
        self.assertEqual(len(result), 0)
    
    def test_calculate_positions_none_polyline_returns_empty(self):
        """Test that None polyline returns empty list."""
        result = PositionCalculator.calculate_positions(
            52.0, 4.0, 90, None, distance=10, amount=3
        )
        
        self.assertEqual(result, [])
    
    @patch('AppMap.AppWidgets.PositionCalculator._project_onto_polyline')
    @patch('AppMap.AppWidgets.PositionCalculator._point_along_polyline')
    def test_calculate_positions_tuple_format(self, mock_point, mock_project):
        """Test that each position is a tuple of (lat, lon, direction)."""
        mock_project.return_value = (52.0, 4.0, 0.0, 0.0, 0.0)
        mock_point.return_value = (52.1, 4.0)
        
        result = PositionCalculator.calculate_positions(
            52.0, 4.0, 45, self.poly_straight, distance=10, amount=2
        )
        
        for pos in result:
            self.assertIsInstance(pos, tuple)
            self.assertEqual(len(pos), 3)
            self.assertIsInstance(pos[0], float)  # lat
            self.assertIsInstance(pos[1], float)  # lon
            self.assertEqual(pos[2], 45)  # direction
    
    @patch('AppMap.AppWidgets.PositionCalculator._project_onto_polyline')
    @patch('AppMap.AppWidgets.PositionCalculator._point_along_polyline')
    def test_calculate_positions_preserves_direction(self, mock_point, mock_project):
        """Test that direction is preserved in all positions."""
        mock_project.return_value = (52.0, 4.0, 0.0, 0.0, 0.0)
        mock_point.side_effect = [(52.1, 4.0), (52.2, 4.0)]
        
        direction = 135
        result = PositionCalculator.calculate_positions(
            52.0, 4.0, direction, self.poly_straight, distance=10, amount=2
        )
        
        for _, _, pos_direction in result:
            self.assertEqual(pos_direction, direction)
            
    @patch('AppMap.AppWidgets.PositionCalculator._project_onto_polyline')
    @patch('AppMap.AppWidgets.PositionCalculator._point_along_polyline')
    def test_calculate_with_different_distances(self, mock_point, mock_project):
        """Test that different distances produce different positions."""
        mock_project.return_value = (52.0, 4.0, 0.0, 0.0, 0.0)
        mock_point.side_effect = [(52.05, 4.0), (52.1, 4.0)]
        
        result_dist_5 = PositionCalculator.calculate_positions(
            52.0, 4.0, 90, self.polyline_north_south, distance=5, amount=1
        )
        
        mock_point.side_effect = [(52.1, 4.0), (52.2, 4.0)]
        result_dist_10 = PositionCalculator.calculate_positions(
            52.0, 4.0, 90, self.polyline_north_south, distance=10, amount=1
        )
        
        # Different distances should yield different results
        self.assertNotEqual(result_dist_5[0][:2], result_dist_10[0][:2])
    
    @patch('AppMap.AppWidgets.PositionCalculator._project_onto_polyline')
    @patch('AppMap.AppWidgets.PositionCalculator._point_along_polyline')
    def test_sequential_positions_are_different(self, mock_point, mock_project):
        """Test that sequential positions are unique."""
        mock_project.return_value = (52.0, 4.0, 0.0, 0.0, 0.0)
        mock_point.side_effect = [(52.1, 4.0), (52.2, 4.0), (52.3, 4.0)]
        
        result = PositionCalculator.calculate_positions(
            52.0, 4.0, 90, self.polyline_north_south, distance=10, amount=3
        )
        
        # Each position should be different
        self.assertNotEqual(result[0][:2], result[1][:2])
        self.assertNotEqual(result[1][:2], result[2][:2])
        self.assertNotEqual(result[0][:2], result[2][:2])


if __name__ == '__main__':
    unittest.main()