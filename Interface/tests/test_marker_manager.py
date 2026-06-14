import unittest
from unittest.mock import MagicMock
from AppMap.AppWidgets.MarkerManager import MarkerManager


class TestMarkerManager(unittest.TestCase):
    """Test marker addition and storage."""
    
    def setUp(self):
        self.mock_map_widget = MagicMock()
        self.manager = MarkerManager(self.mock_map_widget)
    
    def test_add_marker_stores_in_dict(self):
        """Test that added marker is stored in markers_dict."""
        mock_marker = MagicMock()
        self.mock_map_widget.set_marker.return_value = mock_marker
        
        result = self.manager.add_marker((52.0, 4.0), marker_text="test")
        
        self.assertIn(mock_marker, self.manager.markers_dict)
        self.assertEqual(self.manager.markers_dict[mock_marker], "test")
    
    def test_add_marker_stores_direction(self):
        """Test that marker direction is stored."""
        mock_marker = MagicMock()
        self.mock_map_widget.set_marker.return_value = mock_marker
        
        self.manager.add_marker((52.0, 4.0), direction=90, marker_text="robot1")
        
        self.assertIn(mock_marker, self.manager.marker_lines)
        self.assertEqual(self.manager.marker_lines[mock_marker][1], 90)
    
    def test_add_marker_unpacks_coordinates(self):
        """Test that coordinates are unpacked from tuple."""
        mock_marker = MagicMock()
        self.mock_map_widget.set_marker.return_value = mock_marker
        
        self.manager.add_marker((52.5, 4.5), marker_text="test")
        
        call_args = self.mock_map_widget.set_marker.call_args
        self.assertEqual(call_args[0], (52.5, 4.5))
    
    def test_add_marker_returns_marker(self):
        """Test that the marker object is returned."""
        mock_marker = MagicMock()
        self.mock_map_widget.set_marker.return_value = mock_marker
        
        result = self.manager.add_marker((52.0, 4.0), marker_text="test")
        
        self.assertEqual(result, mock_marker)
    
    def test_add_marker_passes_text_to_widget(self):
        """Test that marker text is passed to map widget."""
        mock_marker = MagicMock()
        self.mock_map_widget.set_marker.return_value = mock_marker
        
        self.manager.add_marker((52.0, 4.0), marker_text="incident_01")
        
        call_kwargs = self.mock_map_widget.set_marker.call_args[1]
        self.assertEqual(call_kwargs["text"], "incident_01")
    
    def test_add_marker_with_extra_kwargs(self):
        """Test that additional kwargs are passed to widget."""
        mock_marker = MagicMock()
        self.mock_map_widget.set_marker.return_value = mock_marker
        
        self.manager.add_marker(
            (52.0, 4.0),
            marker_text="test",
            marker_color="#FF0000",
            text_color="#FFFFFF"
        )
        
        call_kwargs = self.mock_map_widget.set_marker.call_args[1]
        self.assertEqual(call_kwargs["marker_color"], "#FF0000")
        self.assertEqual(call_kwargs["text_color"], "#FFFFFF")
    
    def test_add_multiple_markers_independent(self):
        """Test that multiple markers are stored independently."""
        marker1 = MagicMock()
        marker2 = MagicMock()
        
        self.mock_map_widget.set_marker.side_effect = [marker1, marker2]
        
        self.manager.add_marker((52.0, 4.0), marker_text="marker1")
        self.manager.add_marker((52.1, 4.1), marker_text="marker2")
        
        self.assertEqual(len(self.manager.markers_dict), 2)
        self.assertEqual(self.manager.markers_dict[marker1], "marker1")
        self.assertEqual(self.manager.markers_dict[marker2], "marker2")

    
    def test_delete_all_markers_removes_all(self):
        """Test that delete_all_markers removes all stored markers."""
        marker1 = MagicMock()
        marker2 = MagicMock()
        marker3 = MagicMock()
        
        self.manager.markers_dict = {marker1: "m1", marker2: "m2", marker3: "m3"}
        self.manager.marker_lines = {
            marker1: ["m1", 90],
            marker2: ["m2", 90],
            marker3: ["m3", 90]
        }
        
        self.manager.delete_all_markers()
        
        self.assertEqual(len(self.manager.markers_dict), 0)
        self.assertEqual(len(self.manager.marker_lines), 0)
    
    def test_delete_all_markers_calls_delete_on_each(self):
        """Test that delete() is called on each marker."""
        marker1 = MagicMock()
        marker2 = MagicMock()
        
        self.manager.markers_dict = {marker1: "m1", marker2: "m2"}
        self.manager.marker_lines = {marker1: ["m1", 90], marker2: ["m2", 90]}
        
        self.manager.delete_all_markers()
        
        marker1.delete.assert_called_once()
        marker2.delete.assert_called_once()
    
    def test_delete_markers_by_name_pattern(self):
        """Test deleting markers matching name pattern."""
        marker1 = MagicMock()
        marker2 = MagicMock()
        marker3 = MagicMock()
        
        self.manager.markers_dict = {
            marker1: "robot_calc_1",
            marker2: "robot_calc_2",
            marker3: "robot_original"
        }
        self.manager.marker_lines = {
            marker1: ["robot_calc_1", 90],
            marker2: ["robot_calc_2", 90],
            marker3: ["robot_original", 90]
        }
        
        self.manager.delete_markers_by_name("calc")
        
        # Only non-matching marker remains
        self.assertEqual(len(self.manager.markers_dict), 1)
        self.assertIn(marker3, self.manager.markers_dict)
        self.assertNotIn(marker1, self.manager.markers_dict)
        self.assertNotIn(marker2, self.manager.markers_dict)
    
    def test_delete_markers_by_name_empty_pattern(self):
        """Test deleting with empty pattern matches all."""
        marker1 = MagicMock()
        marker2 = MagicMock()
        
        self.manager.markers_dict = {marker1: "marker1", marker2: "marker2"}
        self.manager.marker_lines = {marker1: ["marker1", 90], marker2: ["marker2", 90]}
        
        self.manager.delete_markers_by_name("")  # Empty string in all strings
        
        # All markers should be deleted
        self.assertEqual(len(self.manager.markers_dict), 0)
    
    def test_delete_markers_by_name_no_match(self):
        """Test deleting with non-matching pattern leaves all."""
        marker1 = MagicMock()
        marker2 = MagicMock()
        
        self.manager.markers_dict = {marker1: "m1", marker2: "m2"}
        self.manager.marker_lines = {marker1: ["m1", 90], marker2: ["m2", 90]}
        
        self.manager.delete_markers_by_name("nonexistent")
        
        # No markers should be deleted
        self.assertEqual(len(self.manager.markers_dict), 2)
    
    def test_delete_markers_by_name_case_sensitive(self):
        """Test that deletion is case-sensitive."""
        marker1 = MagicMock()
        marker2 = MagicMock()
        
        self.manager.markers_dict = {
            marker1: "CALCULATED",
            marker2: "calculated"
        }
        self.manager.marker_lines = {
            marker1: ["CALCULATED", 90],
            marker2: ["calculated", 90]
        }
        
        self.manager.delete_markers_by_name("calc")  # lowercase
        
        # Only lowercase matches
        self.assertEqual(len(self.manager.markers_dict), 1)
        self.assertIn(marker1, self.manager.markers_dict)

    
    def test_has_markers_empty(self):
        """Test has_markers returns False when empty."""
        self.assertFalse(self.manager.has_markers())
    
    def test_has_markers_with_one_marker(self):
        """Test has_markers returns True with markers."""
        marker = MagicMock()
        self.manager.markers_dict[marker] = "test"
        
        self.assertTrue(self.manager.has_markers())
    
    def test_get_first_marker_empty(self):
        """Test get_first_marker returns None when empty."""
        result = self.manager.get_first_marker()
        self.assertIsNone(result)
    
    def test_get_first_marker_returns_first(self):
        """Test that first marker is returned."""
        marker = MagicMock()
        self.manager.markers_dict[marker] = "marker"
        
        result = self.manager.get_first_marker()
        self.assertEqual(result, marker)
    
    def test_get_first_marker_with_multiple(self):
        """Test that get_first_marker returns one of the markers."""
        marker1 = MagicMock()
        marker2 = MagicMock()
        
        self.manager.markers_dict[marker1] = "m1"
        self.manager.markers_dict[marker2] = "m2"
        
        result = self.manager.get_first_marker()
        
        self.assertIn(result, [marker1, marker2])

    
    def test_get_calculated_positions_filters_calc_markers(self):
        """Test that only 'calc' markers are returned with positions."""
        marker1 = MagicMock()
        marker1.position = (52.0, 4.0)
        marker2 = MagicMock()
        marker2.position = (52.1, 4.1)
        marker3 = MagicMock()
        marker3.position = (52.2, 4.2)
        
        self.manager.markers_dict = {
            marker1: "robot_calc_1",
            marker2: "robot_calc_2",
            marker3: "robot_original"
        }
        
        result = self.manager.get_calculated_positions()
        
        self.assertIn("robot_calc_1", result)
        self.assertIn("robot_calc_2", result)
        self.assertIn("robot_original", result)
    
    def test_get_calculated_positions_returns_correct_values(self):
        """Test that correct position values are returned."""
        marker1 = MagicMock()
        marker1.position = (52.5, 4.5)
        marker2 = MagicMock()
        
        self.manager.markers_dict = {
            marker1: "robot_calc_result",
            marker2: "robot_original"
        }
        
        result = self.manager.get_calculated_positions()
        
        self.assertEqual(result["robot_calc_result"], (52.5, 4.5))
        self.assertIsNone(result["robot_original"])
    
    def test_get_calculated_positions_empty(self):
        """Test get_calculated_positions with no markers."""
        result = self.manager.get_calculated_positions()
        self.assertEqual(result, {})
    
    def test_get_calculated_positions_none_in_non_calc(self):
        """Test that non-calc markers map to None."""
        marker = MagicMock()
        marker.position = (52.0, 4.0)
        
        self.manager.markers_dict = {
            marker: "robot_placement"
        }
        
        result = self.manager.get_calculated_positions()
        self.assertIsNone(result["robot_placement"])


if __name__ == '__main__':
    unittest.main()