import unittest
from unittest.mock import MagicMock
from AppMap.TextInterpreter import InputInterpreter


class TestInputInterpreter(unittest.TestCase):

    def setUp(self):
        self.callback = MagicMock(return_value=["robot1", "robot2"])
        self.interpreter = InputInterpreter(self.callback)

    # --- check_if_robot_exists ---

    def test_robot_exists_returns_true(self):
        self.assertTrue(self.interpreter.check_if_robot_exists("robot1"))

    def test_robot_not_exists_returns_false(self):
        self.assertFalse(self.interpreter.check_if_robot_exists("robot99"))

    # --- parse_message ---

    def test_parse_position_message_returns_list(self):
        result = self.interpreter.parse_message("52.0,4.0,90", "Commands/robot1/Position")
        self.assertIsInstance(result, list)

    def test_parse_position_message_returns_correct_fields(self):
        result = self.interpreter.parse_message("52.0,4.0,90", "Commands/robot1/Position")
        self.assertEqual(result[0], "robot1")
        self.assertEqual(result[1], "Position")
        self.assertEqual(result[2], 52.0)
        self.assertEqual(result[3], 4.0)
        self.assertEqual(result[4], 90.0)

    def test_parse_status_message_returns_correct_fields(self):
        result = self.interpreter.parse_message("online", "Commands/robot1/Status")
        self.assertEqual(result[0], "robot1")
        self.assertEqual(result[1], "Status")
        self.assertEqual(result[2], "online")

    def test_parse_invalid_position_returns_empty(self):
        result = self.interpreter.parse_message("invalid", "Commands/robot1/Position")
        self.assertEqual(result, [])

    # --- _position_check ---

    def test_position_check_valid_returns_floats(self):
        result = self.interpreter._position_check("52.5,4.5,180")
        self.assertEqual(result, [52.5, 4.5, 180.0])

    def test_position_check_missing_field_returns_false(self):
        self.assertFalse(self.interpreter._position_check("52.5,4.5"))

    def test_position_check_non_numeric_returns_false(self):
        self.assertFalse(self.interpreter._position_check("abc,4.5,90"))

    def test_position_check_invalid_direction_returns_false(self):
        self.assertFalse(self.interpreter._position_check("52.5,4.5,400"))

    # --- _is_fLoat ---

    def test_is_float_valid_number(self):
        self.assertEqual(self.interpreter._is_fLoat("3.14"), 3.14)

    def test_is_float_invalid_returns_false(self):
        self.assertFalse(self.interpreter._is_fLoat("abc"))

    # --- _is_direction ---

    def test_direction_valid_boundaries(self):
        self.assertEqual(self.interpreter._is_direction(0), 0)
        self.assertEqual(self.interpreter._is_direction(360), 360)

    def test_direction_invalid_returns_false(self):
        self.assertFalse(self.interpreter._is_direction(361))
        self.assertFalse(self.interpreter._is_direction(-1))


if __name__ == "__main__":
    unittest.main()