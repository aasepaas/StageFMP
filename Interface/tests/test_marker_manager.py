import unittest
from unittest.mock import MagicMock, patch
from AppMap.AppWidgets.MarkerManager import MarkerManager


class TestMarkerManager(unittest.TestCase):
    """Test MarkerManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_map_widget = MagicMock()
        self.manager = MarkerManager(self.mock_map_widget)
    
    def test_initialization(self):
        """Test that manager initializes with empty dicts."""
        self.assertEqual(self.manager.markers_dict, {})
        self.assertEqual(self.manager.marker_lines, {})
    
    def test_add_marker(self):
        """Test adding a marker."""
        mock_marker = MagicMock()
        self.mock_map_widget.set_marker.return_value = mock_marker
        
        result = self.manager.add_marker((52.0, 4.0), direction=90, marker_text="test")
        
        self.assertEqual(result, mock_marker)
        self.mock_map_widget.set_marker.assert_called_once_with(52.0, 4.0, text="test")
        self.assertEqual(self.manager.markers_dict[mock_marker], "test")
        self.assertEqual(self.manager.marker_lines[mock_marker], ["test", 90])
    
    def test_add_marker_with_kwargs(self):
        """Test adding marker with additional kwargs."""
        mock_marker = MagicMock()
        self.mock_map_widget.set_marker.return_value = mock_marker
        
        self.manager.add_marker(
            (52.0, 4.0),
            direction=45,
            marker_text="marker1",
            marker_color_outside="#FF0000",
            text_color="#FFFFFF"
        )
        
        call_kwargs = self.mock_map_widget.set_marker.call_args[1]
        self.assertEqual(call_kwargs["marker_color_outside"], "#FF0000")
        self.assertEqual(call_kwargs["text_color"], "#FFFFFF")
    
    def test_has_markers_empty(self):
        """Test has_markers returns False when empty."""
        self.assertFalse(self.manager.has_markers())
    
    def test_has_markers_with_markers(self):
        """Test has_markers returns True when markers exist."""
        mock_marker = MagicMock()
        self.manager.markers_dict[mock_marker] = "test"
        
        self.assertTrue(self.manager.has_markers())
    
    def test_get_first_marker_empty(self):
        """Test getting first marker when none exist."""
        result = self.manager.get_first_marker()
        self.assertIsNone(result)
    
    def test_get_first_marker_exists(self):
        """Test getting first marker."""
        mock_marker = MagicMock()
        self.manager.markers_dict[mock_marker] = "marker1"
        
        result = self.manager.get_first_marker()
        self.assertEqual(result, mock_marker)
    
    def test_delete_markers_by_name(self):
        """Test deleting markers by name pattern."""
        marker1 = MagicMock()
        marker2 = MagicMock()
        marker3 = MagicMock()
        
        self.manager.markers_dict = {
            marker1: "calculated1",
            marker2: "calculated2",
            marker3: "original"
        }
        self.manager.marker_lines = {
            marker1: ["calculated1", 90],
            marker2: ["calculated2", 90],
            marker3: ["original", 90]
        }
        
        self.manager.delete_markers_by_name("calculated")
        
        # Should have deleted calculated markers
        self.assertNotIn(marker1, self.manager.markers_dict)
        self.assertNotIn(marker2, self.manager.markers_dict)
        self.assertIn(marker3, self.manager.markers_dict)
        
        marker1.delete.assert_called_once()
        marker2.delete.assert_called_once()
    
    def test_delete_all_markers(self):
        """Test deleting all markers."""
        marker1 = MagicMock()
        marker2 = MagicMock()
        
        self.manager.markers_dict = {
            marker1: "marker1",
            marker2: "marker2"
        }
        self.manager.marker_lines = {
            marker1: ["marker1", 90],
            marker2: ["marker2", 90]
        }
        
        self.manager.delete_all_markers()
        
        marker1.delete.assert_called_once()
        marker2.delete.assert_called_once()
        self.assertEqual(len(self.manager.markers_dict), 0)
        self.assertEqual(len(self.manager.marker_lines), 0)
    
    def test_get_calculated_positions(self):
        """Test getting calculated positions."""
        marker1 = MagicMock()
        marker1.position = (52.0, 4.0)
        marker2 = MagicMock()
        marker2.position = (52.1, 4.1)
        marker3 = MagicMock()
        marker3.position = (52.2, 4.2)
        
        self.manager.markers_dict = {
            marker1: "calculated1",
            marker2: "calculated2",
            marker3: "original"
        }
        
        result = self.manager.get_calculated_positions()
        
        self.assertEqual(result["calculated1"], (52.0, 4.0))
        self.assertEqual(result["calculated2"], (52.1, 4.1))
        self.assertIsNone(result["original"])
    
    def test_get_calculated_positions_no_markers(self):
        """Test getting calculated positions when none exist."""
        result = self.manager.get_calculated_positions()
        self.assertEqual(result, {})


if __name__ == '__main__':
    unittest.main()
