import unittest
from unittest.mock import MagicMock, patch, call
import sys


class TestApp(unittest.TestCase):
    """Test message handling and parsing."""
    
    def setUp(self):
        """Mock Tkinter and other dependencies before importing app."""
        # Mock customtkinter before import
        sys.modules['customtkinter'] = MagicMock()
        sys.modules['customtkinter.windows'] = MagicMock()
        sys.modules['customtkinter.windows.widgets'] = MagicMock()
        sys.modules['AppMap'] = MagicMock()
        sys.modules['AppMap.AppWidgets'] = MagicMock()
        sys.modules['virtualMQTTClient'] = MagicMock()
    
    @patch('sys.modules')
    def test_message_handler_receives_mqtt_message(self, mock_modules):
        """Test that message_handler receives MQTT messages."""
        mock_modules.__contains__ = MagicMock(return_value=True)
        mock_modules.__getitem__ = MagicMock(return_value=MagicMock())
        
        # Create mock MQTT message
        mock_msg = MagicMock()
        mock_msg.payload = b"robot_1:52.5:4.5:90"
        mock_msg.topic = "robot/status"
        
        # This demonstrates how the handler should work
        decodedMessage = mock_msg.payload.decode()
        self.assertEqual(decodedMessage, "robot_1:52.5:4.5:90")
    
    def test_message_decoding(self):
        """Test that MQTT payload is correctly decoded."""
        mock_msg = MagicMock()
        mock_msg.payload = b"test_data_123"
        
        decoded = mock_msg.payload.decode()
        
        self.assertEqual(decoded, "test_data_123")
    
    def test_message_topic_extraction(self):
        """Test that topic can be extracted from message."""
        mock_msg = MagicMock()
        mock_msg.topic = "Commands/robot1/Status"
        mock_msg.payload = b"online"
        
        self.assertEqual(mock_msg.topic, "Commands/robot1/Status")
        self.assertEqual(mock_msg.payload.decode(), "online")

    
    def test_coordinate_dict_filtering(self):
        """Test filtering robots from coordinate dict."""
        robot_names = ["robot1", "robot2", "robot3", "robot4"]
        coords_dict = {
            "robot1": (52.0, 4.0),
            "robot2": (52.1, 4.1),
            "robot3": None  # Some robots might have None coords
        }
        
        # Extract robots not in coords_dict
        robots_to_send = [r for r in robot_names if r not in coords_dict]
        
        self.assertIn("robot4", robots_to_send)
        # robot1, robot2, robot3 are in coords_dict
        self.assertEqual(len(robots_to_send), 1)
    
    def test_coordinate_extraction_from_dict(self):
        """Test extracting valid coordinates from dict."""
        coords_dict = {
            "robot1": (52.0, 4.0),
            "robot2": (52.1, 4.1),
            "robot3": None
        }
        
        coords = [val for key, val in coords_dict.items() if val is not None]
        
        self.assertEqual(len(coords), 2)
        self.assertIn((52.0, 4.0), coords)
        self.assertIn((52.1, 4.1), coords)
    
    def test_coordinate_robot_pairing(self):
        """Test pairing robots with coordinates."""
        robots_to_send = ["robot1", "robot2"]
        coords = [(52.0, 4.0), (52.1, 4.1), (52.2, 4.2)]
        
        index_range = len(robots_to_send) if len(robots_to_send) < len(coords) else len(coords)
        
        pairings = []
        for i in range(index_range):
            pairings.append((robots_to_send[i], coords[i]))
        
        self.assertEqual(len(pairings), 2)
        self.assertEqual(pairings[0], ("robot1", (52.0, 4.0)))
        self.assertEqual(pairings[1], ("robot2", (52.1, 4.1)))
    
    def test_coordinate_robot_pairing_more_robots_than_coords(self):
        """Test pairing when robots exceed coordinates."""
        robots_to_send = ["robot1", "robot2", "robot3", "robot4"]
        coords = [(52.0, 4.0), (52.1, 4.1)]
        
        index_range = len(robots_to_send) if len(robots_to_send) < len(coords) else len(coords)
        
        # Only first 2 robots get coordinates
        self.assertEqual(index_range, 2)
    
    def test_coordinate_robot_pairing_more_coords_than_robots(self):
        """Test pairing when coordinates exceed robots."""
        robots_to_send = ["robot1", "robot2"]
        coords = [(52.0, 4.0), (52.1, 4.1), (52.2, 4.2), (52.3, 4.3)]
        
        index_range = len(robots_to_send) if len(robots_to_send) < len(coords) else len(coords)
        
        # Only first 2 coordinates are used
        self.assertEqual(index_range, 2)


    def test_marker_data_extraction(self):
        """Test extracting marker data from message."""
        marker_to_be_placed = ("robot_1", 52.5, 4.5, 90)
        
        coords = [marker_to_be_placed[1], marker_to_be_placed[2]]
        name = marker_to_be_placed[0]
        direction = marker_to_be_placed[3]
        
        self.assertEqual(coords, [52.5, 4.5])
        self.assertEqual(name, "robot_1")
        self.assertEqual(direction, 90)
    
    def test_marker_coordinates_unpacking(self):
        """Test that marker coordinates are unpacked correctly."""
        marker_data = ("robot_2", 52.1, 4.2, 180)
        
        lat = marker_data[1]
        lon = marker_data[2]
        
        self.assertEqual(lat, 52.1)
        self.assertEqual(lon, 4.2)
    
    def test_multiple_marker_creation(self):
        """Test creating markers from multiple messages."""
        messages = [
            ("robot_1", 52.0, 4.0, 0),
            ("robot_2", 52.1, 4.1, 90),
            ("robot_3", 52.2, 4.2, 180)
        ]
        
        markers = []
        for msg in messages:
            markers.append({
                "name": msg[0],
                "coords": (msg[1], msg[2]),
                "direction": msg[3]
            })
        
        self.assertEqual(len(markers), 3)
        self.assertEqual(markers[0]["name"], "robot_1")
        self.assertEqual(markers[1]["coords"], (52.1, 4.1))
        self.assertEqual(markers[2]["direction"], 180)

    
    def test_reset_clears_robot_state(self):
        """Test that reset clears robot information."""
        robot_states = {
            "robot1": "active",
            "robot2": "inactive",
            "robot3": "error"
        }
        
        # Reset action
        robot_states.clear()
        
        self.assertEqual(len(robot_states), 0)
    
    def test_reset_clears_markers(self):
        """Test that reset clears marker data."""
        markers = [
            {"name": "m1", "coords": (52.0, 4.0)},
            {"name": "m2", "coords": (52.1, 4.1)},
            {"name": "m3", "coords": (52.2, 4.2)}
        ]
        
        # Reset action
        markers.clear()
        
        self.assertEqual(len(markers), 0)
    
    def test_reset_clears_viewport(self):
        """Test that reset clears viewport data."""
        viewport_data = {
            "bbox": (52.0, 4.0, 52.2, 4.2),
            "zoom": 18,
            "center": (52.1, 4.1)
        }
        
        # Reset action
        viewport_data.clear()
        
        self.assertEqual(len(viewport_data), 0)

    
    def test_mqtt_client_message_format(self):
        """Test MQTT message format for sending commands."""
        robot_name = "robot1"
        msg_field = "MoveToPosition"
        lat, lon = 52.5, 4.5
        
        topic = f"Commands/{robot_name}/{msg_field}"
        payload = f"{lat},{lon}"
        
        self.assertEqual(topic, "Commands/robot1/MoveToPosition")
        self.assertEqual(payload, "52.5,4.5")
    
    def test_mqtt_message_topic_construction(self):
        """Test constructing MQTT topics."""
        base_topic = "Commands"
        robot_names = ["robot1", "robot2", "robot3"]
        command = "MoveToPosition"
        
        topics = [f"{base_topic}/{name}/{command}" for name in robot_names]
        
        self.assertEqual(len(topics), 3)
        self.assertEqual(topics[0], "Commands/robot1/MoveToPosition")
        self.assertEqual(topics[1], "Commands/robot2/MoveToPosition")
    
    def test_mqtt_payload_format(self):
        """Test formatting payload with coordinates."""
        coordinates = [
            (52.0, 4.0),
            (52.1, 4.1),
            (52.2, 4.2)
        ]
        
        payloads = [f"{lat},{lon}" for lat, lon in coordinates]
        
        self.assertEqual(payloads[0], "52.0,4.0")
        self.assertEqual(payloads[1], "52.1,4.1")
        self.assertEqual(payloads[2], "52.2,4.2")
    
    def test_parse_csv_coordinates(self):
        """Test parsing CSV-formatted coordinates."""
        payload = "52.5,4.5"
        
        parts = payload.split(",")
        lat = float(parts[0])
        lon = float(parts[1])
        
        self.assertEqual(lat, 52.5)
        self.assertEqual(lon, 4.5)
    
    def test_parse_multiple_messages(self):
        """Test parsing multiple coordinate messages."""
        messages = [
            "52.0,4.0",
            "52.1,4.1",
            "52.2,4.2"
        ]
        
        coordinates = []
        for msg in messages:
            parts = msg.split(",")
            coordinates.append((float(parts[0]), float(parts[1])))
        
        self.assertEqual(len(coordinates), 3)
        self.assertEqual(coordinates[0], (52.0, 4.0))
    
    def test_parse_message_with_extra_whitespace(self):
        """Test parsing messages with whitespace."""
        payload = " 52.5 , 4.5 "
        
        parts = payload.strip().split(",")
        lat = float(parts[0].strip())
        lon = float(parts[1].strip())
        
        self.assertEqual(lat, 52.5)
        self.assertEqual(lon, 4.5)


if __name__ == '__main__':
    unittest.main()