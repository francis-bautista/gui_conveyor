import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the directory containing the main module to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock the customtkinter and tkinter modules before importing
sys.modules['customtkinter'] = Mock()
sys.modules['tkinter'] = Mock()
sys.modules['tkinter.ttk'] = Mock()

# Import the module to test
# Note: Rename your main file from 'paste.txt' to 'button_test.py'
# or update this import to match your filename
try:
    from paste import button_test
except ImportError:
    try:
        from controller import ConveyorController
    except ImportError:
        # If you have a different filename, update this import
        print("Please ensure your main file is named either:")
        print("1. paste.py (rename from paste.txt)")
        print("2. button_test.py")
        print("Or update the import statement in this test file")
        raise


class TestConveyorController(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Mock customtkinter components
        self.mock_ctk = Mock()
        self.mock_button = Mock()
        self.mock_textbox = Mock()
        self.mock_label = Mock()
        
        with patch('button_test.ctk.CTk', return_value=self.mock_ctk), \
             patch('button_test.ctk.CTkButton', return_value=self.mock_button), \
             patch('button_test.ctk.CTkTextbox', return_value=self.mock_textbox), \
             patch('button_test.ctk.CTkLabel', return_value=self.mock_label):
            self.controller = ConveyorController()
    
    def test_initialization(self):
        """Test that the controller initializes correctly."""
        self.assertIsNotNone(self.controller)
        self.assertEqual(self.controller.button_width, 180)
        self.assertEqual(self.controller.button_height, 40)
        
        # Check that the app was configured
        self.mock_ctk.title.assert_called_with("Conveyor Controller")
        self.mock_ctk.geometry.assert_called_with("500x500")
    
    def test_get_number_from_textbox_valid_input(self):
        """Test getting valid number from textbox."""
        mock_textbox = Mock()
        mock_textbox.get.return_value = "5.5"
        
        result = self.controller.get_number_from_textbox(mock_textbox)
        
        self.assertEqual(result, 5.5)
        mock_textbox.get.assert_called_with("1.0", "end-1c")
    
    def test_get_number_from_textbox_integer_input(self):
        """Test getting integer from textbox."""
        mock_textbox = Mock()
        mock_textbox.get.return_value = "10"
        
        result = self.controller.get_number_from_textbox(mock_textbox)
        
        self.assertEqual(result, 10.0)
    
    def test_get_number_from_textbox_empty_input(self):
        """Test handling empty textbox input."""
        mock_textbox = Mock()
        mock_textbox.get.return_value = ""
        
        with patch('builtins.print') as mock_print:
            result = self.controller.get_number_from_textbox(mock_textbox)
            
            self.assertIsNone(result)
            mock_print.assert_called_with("Please enter a number")
    
    def test_get_number_from_textbox_invalid_input(self):
        """Test handling invalid textbox input."""
        mock_textbox = Mock()
        mock_textbox.get.return_value = "invalid_number"
        
        with patch('builtins.print') as mock_print:
            result = self.controller.get_number_from_textbox(mock_textbox)
            
            self.assertIsNone(result)
            mock_print.assert_called_with("Please enter a valid number")
    
    def test_get_number_from_textbox_whitespace_input(self):
        """Test handling whitespace-only textbox input."""
        mock_textbox = Mock()
        mock_textbox.get.return_value = "   "
        
        with patch('builtins.print') as mock_print:
            result = self.controller.get_number_from_textbox(mock_textbox)
            
            self.assertIsNone(result)
            mock_print.assert_called_with("Please enter a number")
    
    @patch('time.sleep')
    def test_countdown(self, mock_sleep):
        """Test countdown functionality."""
        with patch('builtins.print') as mock_print:
            self.controller.countdown(3)
            
            # Check that print was called with countdown numbers
            expected_calls = [unittest.mock.call(3), unittest.mock.call(2), unittest.mock.call(1)]
            mock_print.assert_has_calls(expected_calls)
            
            # Check that sleep was called 3 times with 1 second
            self.assertEqual(mock_sleep.call_count, 3)
            mock_sleep.assert_called_with(1)
    
    def test_move_motor_clockwise_c1(self):
        """Test motor movement for clockwise C1."""
        with patch('builtins.print') as mock_print:
            self.controller.move_motor([1, 0, 0, 0])
            mock_print.assert_called_with("Motor 1 is moving in Clockwise")
    
    def test_move_motor_counter_clockwise_c1(self):
        """Test motor movement for counter-clockwise C1."""
        with patch('builtins.print') as mock_print:
            self.controller.move_motor([0, 1, 0, 0])
            mock_print.assert_called_with("Motor 1 is moving in Counter Clockwise")
    
    def test_move_motor_clockwise_c2(self):
        """Test motor movement for clockwise C2."""
        with patch('builtins.print') as mock_print:
            self.controller.move_motor([0, 0, 1, 0])
            mock_print.assert_called_with("Motor 2 is moving in Clockwise")
    
    def test_move_motor_counter_clockwise_c2(self):
        """Test motor movement for counter-clockwise C2."""
        with patch('builtins.print') as mock_print:
            self.controller.move_motor([0, 0, 0, 1])
            mock_print.assert_called_with("Motor 2 is moving in Counter Clockwise")
    
    def test_move_motor_multiple_motors(self):
        """Test motor movement with multiple motors active."""
        with patch('builtins.print') as mock_print:
            self.controller.move_motor([1, 0, 1, 0])
            
            expected_calls = [
                unittest.mock.call("Motor 1 is moving in Clockwise"),
                unittest.mock.call("Motor 2 is moving in Clockwise")
            ]
            mock_print.assert_has_calls(expected_calls, any_order=True)
    
    def test_picture_side1(self):
        """Test capturing side 1 image."""
        # Mock the buttons
        self.controller.buttonSide1 = Mock()
        self.controller.buttonSide2 = Mock()
        
        with patch('builtins.print') as mock_print:
            self.controller.picture_side1()
            
            mock_print.assert_called_with("Process and pictured side 1")
            self.controller.buttonSide1.configure.assert_called_with(state="disabled")
            self.controller.buttonSide2.configure.assert_called_with(state="normal")
    
    def test_picture_side2(self):
        """Test capturing side 2 image."""
        # Mock the buttons
        self.controller.buttonSide1 = Mock()
        self.controller.buttonSide2 = Mock()
        
        with patch('builtins.print') as mock_print:
            self.controller.picture_side2()
            
            mock_print.assert_called_with("Process and pictured side 2")
            self.controller.buttonSide1.configure.assert_called_with(state="normal")
            self.controller.buttonSide2.configure.assert_called_with(state="disabled")
    
    def test_button_callback_toggle_to_green(self):
        """Test button callback toggles from blue to green."""
        mock_button = Mock()
        mock_button.cget.return_value = "#1F6AA5"  # Default blue
        
        callback = self.controller.button_callback(mock_button)
        callback()
        
        mock_button.configure.assert_called_with(fg_color="green", hover_color="#0B662B")
    
    def test_button_callback_toggle_to_blue(self):
        """Test button callback toggles from green to blue."""
        mock_button = Mock()
        mock_button.cget.return_value = "green"
        
        callback = self.controller.button_callback(mock_button)
        callback()
        
        mock_button.configure.assert_called_with(fg_color="#1F6AA5", hover_color="#3B8ED0")
    
    @patch('button_test.ConveyorController.countdown')
    @patch('button_test.ConveyorController.move_motor')
    @patch('button_test.ConveyorController.get_number_from_textbox')
    def test_button_run_successful_execution(self, mock_get_number, mock_move_motor, mock_countdown):
        """Test successful button run execution."""
        # Setup mocks
        mock_get_number.return_value = 5.0
        mock_textbox = Mock()
        mock_button = Mock()
        
        # Mock the button colors and states
        self.controller.buttonCWC1 = Mock()
        self.controller.buttonCCWC1 = Mock()
        self.controller.buttonCWC2 = Mock()
        self.controller.buttonCCWC2 = Mock()
        
        self.controller.buttonCWC1.cget.return_value = "green"
        self.controller.buttonCCWC1.cget.return_value = "#1F6AA5"
        self.controller.buttonCWC2.cget.return_value = "#1F6AA5"
        self.controller.buttonCCWC2.cget.return_value = "#1F6AA5"
        
        with patch('builtins.print') as mock_print:
            self.controller.button_run(mock_button, mock_textbox)
            
            # Verify the sequence of operations
            mock_textbox.configure.assert_any_call(state="disabled")
            mock_move_motor.assert_called_once_with([1, 0, 0, 0])
            mock_countdown.assert_called_once_with(5)
            mock_button.configure.assert_any_call(text="Running...", state="disabled")
            mock_button.configure.assert_any_call(text="Run C1/C2", state="normal")
            mock_print.assert_called_with("Done Running!")
    
    @patch('button_test.ConveyorController.get_number_from_textbox')
    def test_button_run_no_input_value(self, mock_get_number):
        """Test button run with no input value."""
        mock_get_number.return_value = None
        mock_textbox = Mock()
        mock_button = Mock()
        
        with patch('builtins.print') as mock_print:
            self.controller.button_run(mock_button, mock_textbox)
            
            mock_print.assert_called_with("Input a value")
    
    @patch('button_test.ConveyorController.get_number_from_textbox')
    def test_button_run_conflicting_buttons_c1(self, mock_get_number):
        """Test button run with conflicting C1 button selection."""
        mock_get_number.return_value = 5.0
        mock_textbox = Mock()
        mock_button = Mock()
        
        # Mock conflicting button states for C1
        self.controller.buttonCWC1 = Mock()
        self.controller.buttonCCWC1 = Mock()
        self.controller.buttonCWC2 = Mock()
        self.controller.buttonCCWC2 = Mock()
        
        self.controller.buttonCWC1.cget.return_value = "green"
        self.controller.buttonCCWC1.cget.return_value = "green"
        self.controller.buttonCWC2.cget.return_value = "#1F6AA5"
        self.controller.buttonCCWC2.cget.return_value = "#1F6AA5"
        
        with patch('builtins.print') as mock_print:
            self.controller.button_run(mock_button, mock_textbox)
            
            mock_print.assert_called_with("ERROR Unselect one of the buttons for C1/C2")
            mock_textbox.configure.assert_called_with(state="normal")
    
    @patch('button_test.ConveyorController.get_number_from_textbox')
    def test_button_run_no_buttons_selected(self, mock_get_number):
        """Test button run with no buttons selected."""
        mock_get_number.return_value = 5.0
        mock_textbox = Mock()
        mock_button = Mock()
        
        # Mock no buttons selected
        self.controller.buttonCWC1 = Mock()
        self.controller.buttonCCWC1 = Mock()
        self.controller.buttonCWC2 = Mock()
        self.controller.buttonCCWC2 = Mock()
        
        self.controller.buttonCWC1.cget.return_value = "#1F6AA5"
        self.controller.buttonCCWC1.cget.return_value = "#1F6AA5"
        self.controller.buttonCWC2.cget.return_value = "#1F6AA5"
        self.controller.buttonCCWC2.cget.return_value = "#1F6AA5"
        
        with patch('builtins.print') as mock_print:
            self.controller.button_run(mock_button, mock_textbox)
            
            mock_print.assert_called_with("Select One of the Buttons")
            mock_textbox.configure.assert_called_with(state="normal")


class TestConveyorControllerIntegration(unittest.TestCase):
    """Integration tests for the ConveyorController."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        with patch('button_test.ctk.CTk'), \
             patch('button_test.ctk.CTkButton'), \
             patch('button_test.ctk.CTkTextbox'), \
             patch('button_test.ctk.CTkLabel'):
            self.controller = ConveyorController()
    
    @patch('time.sleep')
    def test_full_workflow_simulation(self, mock_sleep):
        """Test a complete workflow simulation."""
        # Mock UI components
        self.controller.buttonCWC1 = Mock()
        self.controller.buttonCCWC1 = Mock()
        self.controller.buttonCWC2 = Mock()
        self.controller.buttonCCWC2 = Mock()
        self.controller.buttonSide1 = Mock()
        self.controller.buttonSide2 = Mock()
        
        mock_textbox = Mock()
        mock_button = Mock()
        
        # Simulate button selection
        self.controller.buttonCWC1.cget.return_value = "green"
        self.controller.buttonCCWC1.cget.return_value = "#1F6AA5"
        self.controller.buttonCWC2.cget.return_value = "#1F6AA5"
        self.controller.buttonCCWC2.cget.return_value = "#1F6AA5"
        
        # Simulate textbox input
        mock_textbox.get.return_value = "3"
        
        with patch('builtins.print') as mock_print:
            # Run the operation
            self.controller.button_run(mock_button, mock_textbox)
            
            # Capture images
            self.controller.picture_side1()
            self.controller.picture_side2()
            
            # Verify the workflow executed correctly
            self.assertTrue(mock_print.called)
            self.assertEqual(mock_sleep.call_count, 3)


if __name__ == '__main__':
    # Create a test suite
    test_suite = unittest.TestSuite()
    
    # Add all test methods from TestConveyorController
    test_suite.addTest(unittest.makeSuite(TestConveyorController))
    test_suite.addTest(unittest.makeSuite(TestConveyorControllerIntegration))
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\nTests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")