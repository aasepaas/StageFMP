# run_tests.py
import sys
import unittest

def run_all_tests():
    """Run all unit tests."""
    from tests.test_position_calculator import TestPositionCalculator
    from tests.test_position_calculator import TestPositionCalculator
    from tests.test_offset_polyline_manager import TestOffsetPolylineManager
    from tests.test_road_data_manager import TestRoadDataManager
    from tests.test_location_manager import TestLocationManager
    from tests.test_marker_manager import TestMarkerManager
    from tests.test_map_view_controller import TestMapViewController
    from tests.test_mqtt import TestMQTTClient
    from tests.test_app import TestApp
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestPositionCalculator,
        TestOffsetPolylineManager,
        TestRoadDataManager,
        TestLocationManager,
        TestMarkerManager,
        TestMapViewController,
        TestMQTTClient,
        TestApp
    ]
    
    for test_class in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(test_class))
    
    # Run with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    print("="*70)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)