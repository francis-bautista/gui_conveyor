import customtkinter as ctk
import time
from tkinter import ttk  # For combo boxes
import RPi.GPIO as GPIO   
import sys
class ConveyorController:
    def __init__(self):
        # Initialize the main application
        self.app = ctk.CTk()
        self.app.title("Conveyor Controller")
        self.app.geometry("500x500")
        
        # Set consistent button dimensions
        self.button_width = 180
        self.button_height = 40

        self.relay1 = 6   # Motor 1 Forward
        self.relay2 = 13   # Motor 1 Reverse
        self.relay3 = 19  # Motor 2 Forward
        self.relay4 = 26  # Motor 2 Reverse
        GPIO.setmode(GPIO.BCM)  # Use Broadcom pin numbering
        GPIO.setup(self.relay1, GPIO.OUT)
        GPIO.setup(self.relay2, GPIO.OUT)
        GPIO.setup(self.relay3, GPIO.OUT)
        GPIO.setup(self.relay4, GPIO.OUT)
        # Initialize relays to OFF state
        GPIO.output(self.relay1, GPIO.LOW)
        GPIO.output(self.relay2, GPIO.LOW)
        GPIO.output(self.relay3, GPIO.LOW)
        GPIO.output(self.relay4, GPIO.LOW)
        GPIO.setwarnings(False)
        # Initialize UI components
        self.init_ui()
    
    def stop_motors(self):
        GPIO.output(self.relay1, GPIO.LOW)
        GPIO.output(self.relay2, GPIO.LOW)
        GPIO.output(self.relay3, GPIO.LOW)
        GPIO.output(self.relay4, GPIO.LOW)
        print("Motors stopped!")

    def init_ui(self):
        """Initialize all UI components"""
        # Motor control buttons
        self.buttonCWC1 = ctk.CTkButton(
            self.app, 
            text="Clockwise C1", 
            width=self.button_width, 
            height=self.button_height, 
            fg_color="#1F6AA5"
        )
        self.buttonCWC1.configure(command=self.button_callback(self.buttonCWC1))
        self.buttonCWC1.grid(row=0, column=0, padx=20, pady=20)

        self.buttonCCWC1 = ctk.CTkButton(
            self.app, 
            text="Counter Clockwise C1", 
            width=self.button_width, 
            height=self.button_height, 
            fg_color="#1F6AA5"
        )
        self.buttonCCWC1.configure(command=self.button_callback(self.buttonCCWC1))
        self.buttonCCWC1.grid(row=0, column=1, padx=20, pady=20)

        self.buttonCWC2 = ctk.CTkButton(
            self.app, 
            text="Clockwise C2", 
            width=self.button_width, 
            height=self.button_height, 
            fg_color="#1F6AA5"
        )
        self.buttonCWC2.configure(command=self.button_callback(self.buttonCWC2))
        self.buttonCWC2.grid(row=1, column=0, padx=20, pady=20)

        self.buttonCCWC2 = ctk.CTkButton(
            self.app, 
            text="Counter Clockwise C2", 
            width=self.button_width, 
            height=self.button_height, 
            fg_color="#1F6AA5"
        )
        self.buttonCCWC2.configure(command=self.button_callback(self.buttonCCWC2))
        self.buttonCCWC2.grid(row=1, column=1, padx=20, pady=20)

        # Time input section
        self.label = ctk.CTkLabel(
            self.app, 
            text="Time to Move (in seconds?)", 
            fg_color="transparent"
        )
        self.label.grid(row=2, column=0, columnspan=2, padx=10, pady=10)

        self.textbox = ctk.CTkTextbox(
            self.app, 
            width=self.button_width * 2 + 40, 
            height=self.button_height
        )
        self.textbox.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="nswe")

        # Run button
        self.buttonRun = ctk.CTkButton(
            self.app, 
            text="Run C1/C2", 
            width=self.button_width * 2 + 40, 
            height=self.button_height, 
            fg_color="#1FA3A5", 
            hover_color="#177E80"
        )
        self.buttonRun.configure(command=lambda: self.button_run(self.buttonRun, self.textbox))
        self.buttonRun.grid(row=4, column=0, columnspan=2, padx=20, pady=20)

        # Camera control buttons
        self.buttonSide1 = ctk.CTkButton(
            self.app, 
            text="Capture Side 1", 
            width=self.button_width, 
            height=self.button_height, 
            fg_color="#1FA3A5", 
            hover_color="#177E80"
        )
        self.buttonSide1.configure(command=self.picture_side1)
        self.buttonSide1.grid(row=5, column=0, padx=20, pady=20)

        self.buttonSide2 = ctk.CTkButton(
            self.app, 
            text="Capture Side 2", 
            width=self.button_width, 
            height=self.button_height, 
            fg_color="#1FA3A5", 
            hover_color="#177E80",
            state="disabled"
        )
        self.buttonSide2.configure(command=self.picture_side2)
        self.buttonSide2.grid(row=5, column=1, padx=20, pady=20)

        self.buttonExit = ctk.CTkButton(
            self.app, 
            text="Exit", 
            width=self.button_width, 
            height=self.button_height, 
            fg_color="#FF0000", 
            hover_color="#CC0000",
        )
        self.buttonExit.configure(command=self.exit_program)
        self.buttonExit.grid(row=6, column=0, padx=20, pady=20)

    def exit_program(self):
        print("Goodbye")
        GPIO.cleanup()  # Reset GPIO settings
        sys.exit(0)

    def picture_side1(self):
        """Handle capturing side 1 image"""
        print("Process and pictured side 1")
        self.buttonSide1.configure(state="disabled")
        self.buttonSide2.configure(state="normal")
        
    def picture_side2(self):
        """Handle capturing side 2 image"""
        print("Process and pictured side 2")
        self.buttonSide1.configure(state="normal")
        self.buttonSide2.configure(state="disabled")
        
    def move_motor(self, motor_array):
        """Control motor movement based on array values"""
        GPIO.output(self.relay1, motor_array[0])  
        GPIO.output(self.relay2, motor_array[1])   
        GPIO.output(self.relay3, motor_array[2])  
        GPIO.output(self.relay4, motor_array[3])   
        
        if motor_array[0] == 1:
            print("Motor 1 is moving in Clockwise")
        if motor_array[1] == 1:
            print("Motor 1 is moving in Counter Clockwise")
        if motor_array[2] == 1:
            print("Motor 2 is moving in Clockwise")
        if motor_array[3] == 1:
            print("Motor 2 is moving in Counter Clockwise")

    def get_number_from_textbox(self, textbox):
        """Extract and validate number from textbox"""
        try:
            text = textbox.get("1.0", "end-1c").strip()
            if text:  # Check if not empty
                return float(text)  # or int(text) for integer
            else:
                return None  # default value for empty textbox
        except ValueError:
            print("Please enter a valid number")
            return None
        
    def countdown(self, start_count):
        """Countdown loop that prints the count and sleeps"""
        for i in range(start_count, 0, -1):
            print(i)
            time.sleep(1)
        
    def button_callback(self, button):
        """Create callback function for button color toggle"""
        def toggle_color():
            # Get current color
            current_color = button.cget("fg_color")
            # Toggle between blue and green
            if current_color == "#1F6AA5" or current_color == "#3B8ED0":  # Default blue
                button.configure(fg_color="green", hover_color="#0B662B")
            else:
                button.configure(fg_color="#1F6AA5", hover_color="#3B8ED0")
        return toggle_color

    def button_run(self, buttontorun, textbox):
        """Handle the run button functionality"""
        run_time = self.get_number_from_textbox(textbox)
        textbox.configure(state="disabled")  # configure textbox to be read-only
        
        button_color = [
            self.buttonCWC1.cget("fg_color"), 
            self.buttonCCWC1.cget("fg_color"), 
            self.buttonCWC2.cget("fg_color"), 
            self.buttonCCWC2.cget("fg_color")
        ]
        button_list = [self.buttonCWC1, self.buttonCCWC1, self.buttonCWC2, self.buttonCCWC2]
        
        if run_time is None:
            print("Input a value")
        elif 'green' in button_color:
            if ((button_color[0] == 'green' and button_color[1] == 'green') or 
                (button_color[2] == 'green' and button_color[3] == 'green')):
                print("ERROR Unselect one of the buttons for C1/C2")
            else:
                button_state_array = [1 if 'green' in color else 0 for color in button_color]
                self.move_motor(button_state_array)
                buttontorun.configure(text="Running...", state="disabled")
                self.countdown(int(run_time))
                
                buttontorun.configure(text="Run C1/C2", state="normal")
                print("Done Running!")
                self.stop_motors()
                for button in button_list:
                    button.configure(fg_color="#1F6AA5", hover_color="#3B8ED0")     
                textbox.delete("0.0", "end")  # delete all text
        else: 
            print("Select One of the Buttons") 
        textbox.configure(state="normal") 

    def run(self):
        """Start the application main loop"""
        self.app.mainloop()


# Create and run the application
if __name__ == "__main__":
    controller = ConveyorController()
    controller.run()