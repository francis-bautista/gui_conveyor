import customtkinter as ctk
import time, sys, os, threading
from tkinter import ttk  # For combo boxes
import RPi.GPIO as GPIO   
from picamera2 import Picamera2
from PIL import Image, ImageTk
class ConveyorController:
    def __init__(self, app):
        # Initialize the main application
        self.app = app
        self.app.title("Conveyor Controller")
        self.app.geometry("1100x630")
        self.app.fg_color = "#e5e0d8"
        
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

        # Initialize camera
        self.picam2 = Picamera2()
        self.camera_config = self.picam2.create_video_configuration(main={"size": (1920, 1080)})
        self.picam2.configure(self.camera_config)
        self.picam2.start()
        
        self.init_ui()
    
    def stop_motors(self):
        GPIO.output(self.relay1, GPIO.LOW)
        GPIO.output(self.relay2, GPIO.LOW)
        GPIO.output(self.relay3, GPIO.LOW)
        GPIO.output(self.relay4, GPIO.LOW)
        print("Motors stopped!")

    def init_ui(self):
        """Initialize all UI components"""
        # Configure grid layout
        self.app.grid_columnconfigure(0, weight=1)  # Control column (analysis results)
        self.app.grid_columnconfigure(1, weight=1)  # Right column (controls)
        # self.app.grid_columnconfigure(2, weight=1)
        
        self.main_frame = ctk.CTkFrame(self.app, fg_color="#B3B792")
        self.main_frame.grid(row=0, column=1, padx=7, pady=7, sticky="nswe")
        
        self.user_priority_frame(self.main_frame)
        self.control_frame(self.main_frame)
        self.video_frame()
        self.video_feed()
        

    def control_frame(self, main_frame):
        left_frame = ctk.CTkFrame(main_frame)
        left_frame.grid(row=0, column=0, padx=7, pady=7)
        button_padx=7
        button_pady=7
        row_index=0
        self.buttonExit = ctk.CTkButton(
            left_frame, 
            text="Exit", 
            width=self.button_width, 
            height=self.button_height, 
            fg_color="#FF4C4C", 
            hover_color="#CC0000",
        )
        self.buttonExit.configure(command=self.exit_program)
        self.buttonExit.grid(row=row_index, column=0, padx=button_padx, pady=button_pady, sticky="nswe")

        self.buttonReset = ctk.CTkButton(
            left_frame, 
            text="Reset", 
            width=self.button_width, 
            height=self.button_height, 
            fg_color="#FF4C4C", 
            hover_color="#CC0000",  
        )
        self.buttonReset.configure(command=self.reset_program)
        self.buttonReset.grid(row=row_index, column=1, padx=button_padx, pady=button_pady, sticky="nswe")

        row_index += 1

        # Motor control buttons
        self.buttonCWC1 = ctk.CTkButton(
            left_frame, 
            text="Clockwise C1", 
            width=self.button_width, 
            height=self.button_height, 
            fg_color="#1F6AA5"
        )
        self.buttonCWC1.configure(command=self.button_callback(self.buttonCWC1))
        self.buttonCWC1.grid(row=row_index, column=0, padx=button_padx, pady=button_pady, sticky="nswe")

        self.buttonCCWC1 = ctk.CTkButton(
            left_frame, 
            text="Counter Clockwise C1", 
            width=self.button_width, 
            height=self.button_height, 
            fg_color="#1F6AA5"
        )
        self.buttonCCWC1.configure(command=self.button_callback(self.buttonCCWC1))
        self.buttonCCWC1.grid(row=row_index, column=1, padx=button_padx, pady=button_pady, sticky="nswe")

        row_index += 1

        self.buttonCWC2 = ctk.CTkButton(
            left_frame, 
            text="Clockwise C2", 
            width=self.button_width, 
            height=self.button_height, 
            fg_color="#1F6AA5"
        )
        self.buttonCWC2.configure(command=self.button_callback(self.buttonCWC2))
        self.buttonCWC2.grid(row=row_index, column=0, padx=button_padx, pady=button_pady, sticky="nswe")

        self.buttonCCWC2 = ctk.CTkButton(
            left_frame, 
            text="Counter Clockwise C2", 
            width=self.button_width, 
            height=self.button_height, 
            fg_color="#1F6AA5"
        )
        self.buttonCCWC2.configure(command=self.button_callback(self.buttonCCWC2))
        self.buttonCCWC2.grid(row=row_index, column=1, padx=button_padx, pady=button_pady, sticky="nswe")

        row_index += 1

        # Time input section
        self.label = ctk.CTkLabel(
            left_frame, 
            text="Time to Move (in seconds?)", 
            fg_color="transparent"
        )
        self.label.grid(row=row_index, column=0, columnspan=2, padx=button_padx, pady=button_pady, sticky="nswe")
        row_index += 1
        self.textbox = ctk.CTkTextbox(
            left_frame, 
            width=self.button_width * 2 + 40, 
            height=self.button_height
        )
        self.textbox.grid(row=row_index, column=0, columnspan=2, padx=button_padx, pady=button_pady, sticky="nswe")

        row_index += 1

        # Run button
        self.buttonRun = ctk.CTkButton(
            left_frame, 
            text="Run C1/C2", 
            width=self.button_width * 2 + 40, 
            height=self.button_height, 
            fg_color="#1FA3A5", 
            hover_color="#177E80"
        )
        self.buttonRun.configure(command=lambda: self.button_run(self.buttonRun, self.textbox))
        self.buttonRun.grid(row=row_index, column=0, columnspan=2, padx=button_padx, pady=button_pady, sticky="nswe")

        row_index += 1

        # Camera control buttons
        self.buttonSide1 = ctk.CTkButton(
            left_frame, 
            text="Capture Side 1", 
            width=self.button_width, 
            height=self.button_height, 
            fg_color="#1FA3A5", 
            hover_color="#177E80"
        )
        self.buttonSide1.configure(command=self.picture_side1)
        self.buttonSide1.grid(row=row_index, column=0, padx=button_padx, pady=button_pady, sticky="nswe")

        self.buttonSide2 = ctk.CTkButton(
            left_frame, 
            text="Capture Side 2", 
            width=self.button_width, 
            height=self.button_height, 
            fg_color="#1FA3A5", 
            hover_color="#177E80",
            state="disabled"
        )
        self.buttonSide2.configure(command=self.picture_side2)
        self.buttonSide2.grid(row=row_index, column=1, padx= button_padx, pady=button_pady, sticky="nswe")
        

    def video_frame(self):
        """Setup the video feed frame"""
        row_index=0
        paddingx=7
        paddingy=7
        video_frame = ctk.CTkFrame(self.app, fg_color="#B3B792")
        video_frame.grid(row=row_index, column=0, padx=paddingx, pady=paddingy, sticky="nsew")
        
        video_label = ctk.CTkLabel(video_frame, text="Live Video Feed")
        video_label.grid(row=row_index, column=0, padx=paddingx, pady=paddingy, sticky="ns")
        
        results_label = ctk.CTkLabel(video_frame, text="Overall Results")
        results_label.grid(row=row_index, column=1, padx=paddingx, pady=paddingy, sticky="ns")
        
        row_index += 1
        self.video_canvas = ctk.CTkCanvas(video_frame, width=300, height=200)
        self.video_canvas.grid(row=row_index, column=0, padx=paddingx, pady=paddingy, sticky="ns")
        results_data = ctk.CTkLabel(video_frame, text="Average Score: \nPredicted Grade:")
        results_data.grid(row=row_index, column=1, padx=paddingx, pady=paddingy, sticky="ns")
        
        
        row_index += 1
        self.side1_label = ctk.CTkLabel(video_frame, text="Side 1")
        self.side1_label.grid(row=row_index, column=0, padx=paddingx, pady=paddingy, sticky="nswe")
        self.side2_label = ctk.CTkLabel(video_frame, text="Side 2")
        self.side2_label.grid(row=row_index, column=1, padx=paddingx, pady=paddingy, sticky="nswe")
        
        row_index += 1
        self.side1_box = ctk.CTkCanvas(video_frame, width=300, height=200)
        self.side1_box.grid(row=row_index, column=0, padx=paddingx, pady=paddingy, sticky="nswe")
        self.side1_box = ctk.CTkCanvas(video_frame, width=300, height=200)
        self.side1_box.grid(row=row_index, column=1, padx=paddingx, pady=paddingy, sticky="nswe")
        
        row_index += 1
        self.side1_results = ctk.CTkLabel(video_frame, text="Ripeness: \nBruises: \nSize: \nScore: ")
        self.side1_results.grid(row=row_index, column=0, padx=paddingx, pady=paddingy,  sticky="nswe")
        self.side2_results = ctk.CTkLabel(video_frame, text="Ripeness: \nBruises: \nSize: \nScore: ")
        self.side2_results.grid(row=row_index, column=1, padx=paddingx, pady=paddingy, sticky="nswe")
        
        
        
        return video_frame
    
    def user_priority_frame(self, main_frame):
        """Setup the user priority section with combo boxes"""
        index_row=6
        padding=7
        width_combobox=120
        col=0
        frame_choices = ctk.CTkFrame(main_frame)
        frame_choices.grid(row=index_row, column=0, padx=padding, pady=padding, sticky="nswe")
        frame_choices.columnconfigure(0, weight=1)
        frame_choices.columnconfigure(1, weight=1) 
        frame_choices.columnconfigure(2, weight=1)
        # User Priority heading
        priority_label = ctk.CTkLabel(frame_choices, text="User Priority")
        priority_label.grid(row=6, column=col, padx=padding, pady=padding, sticky="nswe", columnspan=3)
        index_row+=1
        
        # Ripeness combo
        ripeness_label = ctk.CTkLabel(frame_choices, text="Ripeness:")
        ripeness_label.grid(row=index_row, column=col, padx=padding, pady=padding, sticky="ew")
        
        # col+=1
        self.ripeness_combo = ctk.CTkComboBox(frame_choices, values=["0.0", "1.0", "2.0", "3.0"], width=width_combobox)
        self.ripeness_combo.set("0.0")  # Set default value
        self.ripeness_combo.grid(row=index_row+1, column=col, padx=padding, pady=padding, sticky="nswe")

        # Bruises combo
        col+=1
        bruises_label = ctk.CTkLabel(frame_choices, text="Bruises:")
        bruises_label.grid(row=index_row, column=col, padx=padding, pady=padding, sticky="ew")
        
        # col+=1
        self.bruises_combo = ctk.CTkComboBox(frame_choices, values=["0.0", "1.0", "2.0", "3.0"], width=width_combobox)
        self.bruises_combo.set("0.0")  # Set default value
        self.bruises_combo.grid(row=index_row+1, column=col, padx=padding, pady=padding, sticky="nswe")
        
        # Size combo
        col+=1
        size_label = ctk.CTkLabel(frame_choices, text="Size:")
        size_label.grid(row=index_row, column=col, padx=padding, pady=padding, sticky="ew")
        
        # index_row+=1
        self.size_combo = ctk.CTkComboBox(frame_choices, values=["0.0", "1.0", "2.0", "3.0"], width=width_combobox)
        self.size_combo.set("0.0")  # Set default value
        self.size_combo.grid(row=index_row+1, column=col, padx=padding, pady=padding, sticky="nswe")
        
        self.button_enter = ctk.CTkButton(frame_choices, text="Enter", command=self.enter_priority)
        self.button_enter.grid(row=index_row+2, column=0, padx=padding, pady=padding, sticky="nswe", columnspan=3)
        
        self.button_help = ctk.CTkButton(frame_choices, text="Help", command=self.help_page)
        self.button_help.grid(row=index_row+3, column=0, padx=padding, pady=padding, sticky="nswe", columnspan=3)
        
        return frame_choices
    def help_page(self):
        print("Help page")
    def enter_priority(self):
        ripeness = self.ripeness_combo.get()
        bruises = self.bruises_combo.get()
        size = self.size_combo.get()
        print(f"Ripeness: {ripeness}, Bruises: {bruises}, Size: {size}")
        self.ripeness_combo.configure(state="disabled")
        self.bruises_combo.configure(state="disabled")
        self.size_combo.configure(state="disabled")
        
    def reset_program(self):
        print("Resetting")
        GPIO.cleanup()  # Reset GPIO settings
        self.picam2.stop()
        os.execv(sys.executable, [sys.executable] + sys.argv)

    def exit_program(self):
        print("Goodbye")
        GPIO.cleanup()  # Reset GPIO settings
        self.picam2.stop()
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
        
    def countdown_thread(self, start_count, buttontorun, textbox):
        """Countdown in separate thread"""
        button_list = [self.buttonCWC1, self.buttonCCWC1, self.buttonCWC2, self.buttonCCWC2]
        
        for i in range(start_count, 0, -1):
            print(i)
            time.sleep(1)

        # Use app.after to safely update GUI from thread
        self.app.after(0, lambda: self._finish_motor_run_threaded(buttontorun, textbox, button_list))

    def _finish_motor_run_threaded(self, buttontorun, textbox, button_list):
        """Finish motor run - called from main thread"""
        buttontorun.configure(text="Run C1/C2", state="normal")
        print("Done Running!")
        self.stop_motors()
        
        for button in button_list:
            button.configure(fg_color="#1F6AA5", hover_color="#3B8ED0")
        
        textbox.delete("0.0", "end")
        textbox.configure(state="normal")

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
        """Handle the run button functionality with threading"""
        run_time = self.get_number_from_textbox(textbox)
        textbox.configure(state="disabled")
        
        button_color = [
            self.buttonCWC1.cget("fg_color"), 
            self.buttonCCWC1.cget("fg_color"), 
            self.buttonCWC2.cget("fg_color"), 
            self.buttonCCWC2.cget("fg_color")
        ]
        
        if run_time is None:
            print("Input a value")
            textbox.configure(state="normal")
        elif 'green' in button_color:
            if ((button_color[0] == 'green' and button_color[1] == 'green') or 
                (button_color[2] == 'green' and button_color[3] == 'green')):
                print("ERROR Unselect one of the buttons for C1/C2")
                textbox.configure(state="normal")
            else:
                button_state_array = [1 if 'green' in color else 0 for color in button_color]
                self.move_motor(button_state_array)
                buttontorun.configure(text="Running...", state="disabled")
                
                # Start countdown in separate thread
                countdown_thread = threading.Thread(
                    target=self.countdown_thread, 
                    args=(int(run_time), buttontorun, textbox)
                )
                countdown_thread.daemon = True  # Thread will close when main program closes
                countdown_thread.start()
                textbox.configure(state="normal")
                textbox.delete("0.0", "end")  # delete all text
        else: 
            print("Select One of the Buttons")
            textbox.configure(state="normal")

    def video_feed(self):
        """Updates the video feed on the Tkinter canvas."""
        
        # Capture frame from the camera
        frame = self.picam2.capture_array()
        frame = Image.fromarray(frame).convert("RGB")  # Convert RGBA to RGB
        
        # Resize and convert to PhotoImage
        frame = frame.resize((300, 200))
        frame = ImageTk.PhotoImage(frame)
        
        # Update the video canvas with the new frame
        self.video_canvas.create_image(0, 0, anchor=ctk.NW, image=frame)
        self.video_canvas.image = frame
        
        # Schedule the next update
        app.after(10, self.video_feed)

    def run(self):
        """Start the application main loop"""
        self.app.mainloop()


# Create and run the application
if __name__ == "__main__":
    app = ctk.CTk(fg_color="#e5e0d8")
    controller = ConveyorController(app)
    controller.run()