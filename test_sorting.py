import unittest
from unittest.mock import patch, MagicMock, call
import sys
from io import StringIO

# Import the module under test
from sorting import SorterController


class TestSorterController(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Mock GPIO to avoid actual GPIO operations during testing
        self.gpio_patcher = patch('sorting.GPIO')
        self.mock_gpio = self.gpio_patcher.start()
        
        # Create a fresh instance for each test
        self.controller = SorterController()
    
    def tearDown(self):
        """Clean up after each test method."""
        self.gpio_patcher.stop()
    
    def test_init(self):
        """Test that the controller initializes correctly."""
        expected_relays = {'r1': 4, 'r2': 17, 'r3': 27, 'r4': 22}
        self.assertEqual(self.controller.relays, expected_relays)
        
        # Verify setup_gpio was called during initialization
        self.mock_gpio.cleanup.assert_called()
        self.mock_gpio.setmode.assert_called_with(self.mock_gpio.BCM)
    
    def test_setup_gpio(self):
        """Test GPIO setup configuration."""
        # Reset mock to clear calls from __init__
        self.mock_gpio.reset_mock()
        
        # Call setup_gpio
        self.controller.setup_gpio()
        
        # Verify GPIO cleanup and mode setting
        self.mock_gpio.cleanup.assert_called_once()
        self.mock_gpio.setmode.assert_called_once_with(self.mock_gpio.BCM)
        
        # Verify each pin is set up as output and set to LOW
        expected_pins = [4, 17, 27, 22]
        
        # Check setup calls for each pin
        setup_calls = self.mock_gpio.setup.call_args_list
        self.assertEqual(len(setup_calls), 8)  # 2 calls per pin (OUT and LOW)
        
        # Verify setwarnings is disabled
        self.mock_gpio.setwarnings.assert_called_with(False)
    
    def test_clean_gpio(self):
        """Test GPIO cleanup."""
        self.mock_gpio.reset_mock()
        
        self.controller.clean_gpio()
        
        self.mock_gpio.cleanup.assert_called_once()
    
    def test_set_motors_all_off(self):
        """Test setting all motors to off (all zeros)."""
        self.mock_gpio.reset_mock()
        
        # Capture printed output
        captured_output = StringIO()
        with patch('sys.stdout', captured_output):
            self.controller.set_motors([0, 0, 0, 0])
        
        # Verify GPIO outputs are set correctly
        expected_calls = [
            call(4, 0),
            call(17, 0), 
            call(27, 0),
            call(22, 0)
        ]
        self.mock_gpio.output.assert_has_calls(expected_calls)
        
        # Verify no motor messages are printed (all motors off)
        output = captured_output.getvalue()
        self.assertEqual(output.strip(), "")
    
    def test_set_motors_all_on(self):
        """Test setting all motors to on (all ones)."""
        self.mock_gpio.reset_mock()
        
        # Capture printed output
        captured_output = StringIO()
        with patch('sys.stdout', captured_output):
            self.controller.set_motors([1, 1, 1, 1])
        
        # Verify GPIO outputs are set correctly
        expected_calls = [
            call(4, 1),
            call(17, 1),
            call(27, 1),
            call(22, 1)
        ]
        self.mock_gpio.output.assert_has_calls(expected_calls)
        
        # Verify all motor messages are printed
        output = captured_output.getvalue()
        expected_messages = [
            "Motor 3 is moving in Clockwise",
            "Motor 3 is moving in Counter Clockwise",
            "Motor 4 is moving in Clockwise", 
            "Motor 4 is moving in Counter Clockwise"
        ]
        
        for message in expected_messages:
            self.assertIn(message, output)
    
    def test_set_motors_selective(self):
        """Test setting motors selectively."""
        self.mock_gpio.reset_mock()
        
        # Test with only first and third motors on
        captured_output = StringIO()
        with patch('sys.stdout', captured_output):
            self.controller.set_motors([1, 0, 1, 0])
        
        # Verify GPIO outputs
        expected_calls = [
            call(4, 1),   # r1 on
            call(17, 0),  # r2 off
            call(27, 1),  # r3 on
            call(22, 0)   # r4 off
        ]
        self.mock_gpio.output.assert_has_calls(expected_calls)
        
        # Verify only corresponding messages are printed
        output = captured_output.getvalue()
        self.assertIn("Motor 3 is moving in Clockwise", output)
        self.assertIn("Motor 4 is moving in Clockwise", output)
        self.assertNotIn("Counter Clockwise", output)
    
    def test_stop_motors(self):
        """Test stopping all motors."""
        self.mock_gpio.reset_mock()
        
        # Capture printed output
        captured_output = StringIO()
        with patch('sys.stdout', captured_output):
            self.controller.stop_motors()
        
        # Verify all pins are set to LOW
        expected_calls = [
            call(4, self.mock_gpio.LOW),
            call(17, self.mock_gpio.LOW),
            call(27, self.mock_gpio.LOW),
            call(22, self.mock_gpio.LOW)
        ]
        self.mock_gpio.output.assert_has_calls(expected_calls, any_order=True)
        
        # Verify stop message is printed
        output = captured_output.getvalue()
        self.assertIn("Motors stopped!", output)
    
    def test_motor_array_edge_cases(self):
        """Test edge cases for motor array input."""
        self.mock_gpio.reset_mock()
        
        # Test with boolean values instead of integers
        captured_output = StringIO()
        with patch('sys.stdout', captured_output):
            self.controller.set_motors([True, False, True, False])
        
        # Should work the same as [1, 0, 1, 0]
        expected_calls = [
            call(4, True),
            call(17, False),
            call(27, True),
            call(22, False)
        ]
        self.mock_gpio.output.assert_has_calls(expected_calls)
    
    def test_relay_pin_mapping(self):
        """Test that relay names map to correct pin numbers."""
        expected_mapping = {
            'r1': 4,
            'r2': 17, 
            'r3': 27,
            'r4': 22
        }
        self.assertEqual(self.controller.relays, expected_mapping)
        
        # Verify the order matches what set_motors expects
        pin_values = list(self.controller.relays.values())
        expected_order = [4, 17, 27, 22]
        self.assertEqual(pin_values, expected_order)


class TestSorterControllerIntegration(unittest.TestCase):
    """Integration tests that test multiple methods together."""
    
    def setUp(self):
        self.gpio_patcher = patch('sorting.GPIO')
        self.mock_gpio = self.gpio_patcher.start()
        self.controller = SorterController()
    
    def tearDown(self):
        self.gpio_patcher.stop()
    
    def test_typical_usage_workflow(self):
        """Test a typical workflow of using the controller."""
        self.mock_gpio.reset_mock()
        
        # Test typical usage pattern
        captured_output = StringIO()
        with patch('sys.stdout', captured_output):
            # Start some motors
            self.controller.set_motors([1, 0, 1, 0])
            
            # Change motor configuration
            self.controller.set_motors([0, 1, 0, 1])
            
            # Stop all motors
            self.controller.stop_motors()
            
            # Clean up
            self.controller.clean_gpio()
        
        # Verify the sequence of operations
        output = captured_output.getvalue()
        self.assertIn("Motor 3 is moving in Clockwise", output)
        self.assertIn("Motor 3 is moving in Counter Clockwise", output)
        self.assertIn("Motors stopped!", output)
        
        # Verify cleanup was called
        self.mock_gpio.cleanup.assert_called()


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)