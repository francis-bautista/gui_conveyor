import torch
import torchvision.transforms as transforms
from efficientnet_pytorch import EfficientNet
from PIL import Image, ImageTk
import time
import tkinter as tk
import customtkinter as ctk
from tkinter import ttk  # For combo boxes
from picamera2 import Picamera2
from datetime import datetime
from scipy.spatial import distance as dist
import sys
import os
from tkinter import ttk, messagebox
import RPi.GPIO as GPIO
import threading
from get_size import calculate_size, determine_size
from help_page import hp
class MangoGraderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Carabao Mango Grader and Sorter")
        self.root.fg_color = "#e5e0d8"
        
        # Initialize camera
        self.picam2 = Picamera2()
        self.camera_config = self.picam2.create_video_configuration(main={"size": (1920, 1080)})
        self.picam2.configure(self.camera_config)
        self.picam2.start()
        
        self.class_labels_ripeness = ['green', 'yellow_green', 'yellow']
        self.class_labels_bruises = ['bruised', 'unbruised']
        self.class_labels_size = ['small', 'medium', 'large']
        self.ripeness_scores = {'yellow': 1.0, 'yellow_green': 2.0, 'green': 3.0}
        self.bruiseness_scores = {'bruised': 1.5, 'unbruised': 3.0}
        self.size_scores = {'small': 1.0, 'medium': 2.0, 'large': 3.0}
        self.scores_dict = {}

        # Load Training and Testing Models
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        # Ripeness model
        self.model_ripeness = EfficientNet.from_pretrained('efficientnet-b0', num_classes=len(self.class_labels_ripeness))
        self.model_ripeness.load_state_dict(torch.load("ripeness.pth", map_location=self.device))
        self.model_ripeness.eval()
        self.model_ripeness.to(self.device)
        # Bruises model
        self.model_bruises = EfficientNet.from_pretrained('efficientnet-b0', num_classes=len(self.class_labels_bruises))
        self.model_bruises.load_state_dict(torch.load("bruises.pth", map_location=self.device))
        self.model_bruises.eval()
        self.model_bruises.to(self.device)
        # Define transformations
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])

        # Size calculation parameters
        self.FOCAL_LENGTH_PIXELS = 3500  # Example value, replace with your camera's focal length
        self.DISTANCE_CAMERA_TO_OBJECT = 40  # 20.5 cm according to don
        
        # Define the GPIO pins connected to the relays
        self.relay1 = 6   # Motor 1 Forward
        self.relay2 = 13   # Motor 1 Reverse
        self.relay3 = 19  # Motor 2 Forward
        self.relay4 = 26  # Motor 2 Reverse
        self.delay_time = 2  # 2 seconds delay between direction changes
        # Define pin connections (using BOARD numbering)
        self.dir_pin = 21    # Physical pin 21
        self.step_pin = 20   # Physical pin 20
        self.steps_per_revolution = 200
        # Define absolute positions (steps from home)
        self.position1 = 50
        self.position2 = 100
        self.position3 = 150
        self.current_position = 0  # Track current position
        self.step_delay = 0.001    # 1ms delay between steps (adjust for speed)
        # Setup GPIO
        GPIO.setmode(GPIO.BCM)  # Use Broadcom pin numbering
        GPIO.setup(self.relay1, GPIO.OUT)
        GPIO.setup(self.relay2, GPIO.OUT)
        GPIO.setup(self.relay3, GPIO.OUT)
        GPIO.setup(self.relay4, GPIO.OUT)
        GPIO.setup(self.dir_pin, GPIO.OUT)
        GPIO.setup(self.step_pin, GPIO.OUT)
        GPIO.output(self.dir_pin, GPIO.LOW)
        GPIO.output(self.step_pin, GPIO.LOW)
        # Initialize relays to OFF state
        GPIO.output(self.relay1, GPIO.LOW)
        GPIO.output(self.relay2, GPIO.LOW)
        GPIO.output(self.relay3, GPIO.LOW)
        GPIO.output(self.relay4, GPIO.LOW)
        
        # Processing state flags
        self.processing = False
        self.stop_requested = False
        
        # Configure grid layout
        self.root.grid_columnconfigure(0, weight=1)  # Left column (analysis results)
        self.root.grid_columnconfigure(1, weight=1)  # Right column (controls)
        self.root.grid_columnconfigure(2, weight=1)  # Video feed
        self.root.grid_rowconfigure(0, weight=1)
        
        # Create frames
        self.setup_analysis_frame()
        self.setup_control_frame()
        self.setup_video_frame()
        
        # Start the video feed
        self.update_video_feed()
    
    def setup_analysis_frame(self):
        """Setup the left frame for analysis results"""
        left_frame = ctk.CTkFrame(self.root, fg_color="#B3B792")
        left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        # Top part UI
        top_label = ctk.CTkLabel(left_frame, text="Top Image")
        top_label.grid(row=0, column=0, padx=10, pady=10, sticky="nswe")
        
        self.top_canvas = tk.Canvas(left_frame, width=300, height=200)
        self.top_canvas.grid(row=1, column=0, padx=10, pady=10, sticky="nswe")
        
        self.top_result_label = ctk.CTkLabel(left_frame, text="Ripeness: -\nBruises: - \nSize - ")
        self.top_result_label.grid(row=2, column=0, sticky="nswe")
        
        # Bottom part UI
        bottom_label = ctk.CTkLabel(left_frame, text="Bottom Image")
        bottom_label.grid(row=3, column=0)
        
        self.bottom_canvas = tk.Canvas(left_frame, width=300, height=200)
        self.bottom_canvas.grid(row=4, column=0)
        
        self.bottom_result_label = ctk.CTkLabel(left_frame, text="Ripeness: -\nBruises: - \nSize - ")
        self.bottom_result_label.grid(row=5, column=0)
    
    def setup_control_frame(self):
        """Setup the right frame for buttons and controls"""
        right_frame = ctk.CTkFrame(self.root, fg_color="#B3B792")
        right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
        # Action buttons
        self.start_button = ctk.CTkButton(right_frame, text="Start", fg_color="#8AD879", 
                                         command=self.start_processing)
        self.start_button.grid(row=0, column=0, padx=10, pady=10, sticky="ns")
        
        self.stop_button = ctk.CTkButton(right_frame, text="Exit", fg_color="#F3533A",
                                       command=self.stop_processing)
        self.stop_button.grid(row=0, column=1, padx=10, pady=10, sticky="ns")
        
        self.reset_button = ctk.CTkButton(right_frame, text="Reset", fg_color="#5CACF9",
                                        command=self.reset_system)
        self.reset_button.grid(row=1, column=0, padx=10, pady=10, sticky="ns")
        
        self.help_button = ctk.CTkButton(right_frame, text="Help", fg_color="#f85cf9",
                                       command=self.show_help)
        self.help_button.grid(row=1, column=1, padx=10, pady=10, sticky="ns")
        
        # Toggle Button
        self.check_var = ctk.StringVar(value="off")
        checkbox = ctk.CTkCheckBox(right_frame, text="Default", command=self.checkbox_event,
                                   variable=self.check_var, onvalue="on", offvalue="off")
        checkbox.grid(row=2, column=1, padx=10, pady=10, sticky="ns")
        
        # Score displays
        self.top_score = ctk.CTkLabel(right_frame, text="Top Score - ")
        self.top_score.grid(row=3, column=0)
        
        self.bottom_score = ctk.CTkLabel(right_frame, text="Bottom Score - ")
        self.bottom_score.grid(row=4, column=0)
        
        self.grade_score = ctk.CTkLabel(right_frame, text="Grade - ")
        self.grade_score.grid(row=5, column=0)
        
        # User priority section
        self.setup_user_priority_frame(right_frame)
    
    def setup_user_priority_frame(self, parent_frame):
        """Setup the user priority section with combo boxes"""
        frame_choices = ctk.CTkFrame(parent_frame, fg_color="#809671")
        frame_choices.grid(row=8, column=0, padx=10, pady=10, columnspan=2, sticky="nswe")
        frame_choices.columnconfigure(0, weight=2)
        
        # User Priority heading
        priority_label = ctk.CTkLabel(frame_choices, text="User Priority")
        priority_label.grid(row=0, column=0, padx=10, pady=10, columnspan=2, sticky="nswe")
        
        # Ripeness combo
        ripeness_label = ctk.CTkLabel(frame_choices, text="Ripeness Score (0-3):")
        ripeness_label.grid(row=1, column=0, padx=10, pady=10, columnspan=2, sticky="nswe")
        
        self.ripeness_combo = ttk.Combobox(frame_choices, values=[0.0, 1.0, 2.0, 3.0])
        self.ripeness_combo.grid(row=2, column=0)
        
        # Bruises combo
        bruises_label = ctk.CTkLabel(frame_choices, text="Bruises Score (0-3):")
        bruises_label.grid(row=3, column=0, padx=10, pady=10, columnspan=2, sticky="nswe")
        
        self.bruises_combo = ttk.Combobox(frame_choices, values=[0.0, 1.0, 2.0, 3.0])
        self.bruises_combo.grid(row=4, column=0)
        
        # Size combo
        size_label = ctk.CTkLabel(frame_choices, text="Size Score (0-3):")
        size_label.grid(row=5, column=0, padx=10, pady=10, columnspan=2, sticky="nswe")
        
        self.size_combo = ttk.Combobox(frame_choices, values=[0.0, 1.0, 2.0, 3.0])
        self.size_combo.grid(row=6, column=0, padx=10, pady=(0, 20))
    
    def setup_video_frame(self):
        """Setup the video feed frame"""
        video_frame = ctk.CTkFrame(self.root, fg_color="#B3B792")
        video_frame.grid(row=0, column=2, padx=10, pady=10, sticky="nsew")
        
        video_label = ctk.CTkLabel(video_frame, text="Live Video Feed")
        video_label.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="ns")
        
        self.video_canvas = tk.Canvas(video_frame, width=300, height=200)
        self.video_canvas.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="ns")

        # Progress bar
        self.progress_label = ctk.CTkLabel(video_frame, text="Progress:")
        self.progress_label.grid(row=2, column=0, sticky="w", padx=10)
        
        self.progress_bar = ctk.CTkProgressBar(video_frame, width=200, mode="determinate")
        self.progress_bar.grid(row=2, column=0, columnspan=2, padx=10, pady=(30, 10), sticky="ew")
        self.progress_bar.set(0)  # Initialize at 0
        
    def start_processing(self):
        """Start the processing with a loading bar"""
        if (self.ripeness_combo.get() == "" or self.bruises_combo.get() == "" or self.size_combo.get() == ""):
            messagebox.showerror("Error", "Please select values for Ripeness, Bruises, and Size")
            return
        if not self.processing:
            self.processing = True
            self.stop_requested = False
            # Disable input from user priority
            self.ripeness_combo.configure(state="disabled")  # or "readonly"
            self.bruises_combo.configure(state="disabled")
            self.size_combo.configure(state="disabled")
            
            # Update button states
            self.start_button.configure(state="disabled")
            # Change text to "Stop" during processing
            self.stop_button.configure(text="Stop", state="normal")
            self.reset_button.configure(state="disabled")
            
            # Reset progress bar
            self.progress_bar.set(0)
            
            # Start processing in a separate thread
            self.process_thread = threading.Thread(target=self.update_gui)
            self.process_thread.daemon = True
            self.process_thread.start()
    
    def update_gui(self):
        """Updates the GUI by capturing images and analyzing the mango."""
        try:
            # Get the current date and time
            now = datetime.now()
            formatted_date_time = now.strftime("%Y-%m-%d_%H-%M-%S")
            
            # Progress: 0% - Starting
            self.update_progress_safe(0.05, "Capturing background...")
            if self.stop_requested: return
            
            # Capture background
            top_background = self.capture_image(self.picam2)
            top_background.save(f"{formatted_date_time}_background.png")
            
            # Progress: 10% - Moving motor for top capture
            self.update_progress_safe(0.1, "Moving motor for top capture...")
            if self.stop_requested: return
            
            self.moveMotor(0, 1, 0, 1)
            
            # Progress from 10% to 20% during 5 second sleep
            for i in range(15):
                if self.stop_requested: return
                progress = 0.1 + (i * 0.01)
                self.update_progress_safe(progress, "Positioning for top capture...")
                time.sleep(0.5)  # Sleep for 0.5 seconds, 10 times = 5 seconds
            
            self.stopMotor()
            
            # Progress: 20% - Capturing top part
            self.update_progress_safe(0.2, "Capturing top part...")
            if self.stop_requested: return
            
            # self.root.after(0, lambda: self.top_label.configure(text="Capturing top part of the mango..."))
            top_image = self.capture_image(self.picam2)
            top_image.save(f"{formatted_date_time}_top.png")
            
            # Progress: 25% - Analyzing top part
            self.update_progress_safe(0.25, "Analyzing top part...")
            if self.stop_requested: return
            
            top_class_ripeness = self.classify_image(top_image, self.model_ripeness, self.class_labels_ripeness)
            top_class_bruises = self.classify_image(top_image, self.model_bruises, self.class_labels_bruises)
            top_width, top_length = calculate_size(f"{formatted_date_time}_top.png", 
                                                      f"{formatted_date_time}_background.png", 
                                                      formatted_date_time, True,
                                                      self.DISTANCE_CAMERA_TO_OBJECT, 
                                                      self.FOCAL_LENGTH_PIXELS
                                                      )
            print(f"Top Width: {top_width:.2f} cm, Top Length: {top_length:.2f} cm")
            top_size_class = determine_size(top_width, top_length) 
            # Update UI with top results
            self.update_top_results(top_image, top_class_ripeness, top_class_bruises, top_size_class)
            
            # Progress: 30% - Moving motor for bottom capture
            self.update_progress_safe(0.3, "Moving motor for bottom capture...")
            if self.stop_requested: return
            
            self.moveMotor(0, 1, 1, 0)
            
            # Progress from 30% to 40% during 5 second sleep
            for i in range(10):
                if self.stop_requested: return
                progress = 0.3 + (i * 0.01)
                self.update_progress_safe(progress, "Positioning for bottom capture...")
                time.sleep(0.5)  # Sleep for 0.5 seconds, 10 times = 5 seconds
            
            self.stopMotor()
            
            # Progress: 40% - Capturing bottom part
            self.update_progress_safe(0.4, "Capturing bottom part...")
            if self.stop_requested: return
            
            # self.root.after(0, lambda: self.bottom_label.configure(text="Capturing bottom part of the mango..."))
            bottom_image = self.capture_image(self.picam2)
            bottom_image.save(f"{formatted_date_time}_bottom.png")
            
            # Progress: 50% - Analyzing bottom part
            self.update_progress_safe(0.5, "Analyzing bottom part...")
            if self.stop_requested: return
            
            bottom_class_ripeness = self.classify_image(bottom_image, self.model_ripeness, self.class_labels_ripeness)
            bottom_class_bruises = self.classify_image(bottom_image, self.model_bruises, self.class_labels_bruises)
            bottom_width, bottom_length = calculate_size(f"{formatted_date_time}_bottom.png", 
                                                            f"{formatted_date_time}_background.png", 
                                                            formatted_date_time, False,
                                                            self.DISTANCE_CAMERA_TO_OBJECT, 
                                                            self.FOCAL_LENGTH_PIXELS
                                                            )
            print(f"Bottom Width: {bottom_width:.2f} cm, Bottom Length: {bottom_length:.2f} cm")
            bottom_size_class = determine_size(bottom_width, bottom_length)
            # Update UI with bottom results
            self.update_bottom_results(bottom_image, bottom_class_ripeness, bottom_class_bruises, bottom_size_class)
            
            # Progress: 60% - Computing scores
            self.update_progress_safe(0.6, "Computing scores...")
            if self.stop_requested: return
            
            # Progress: 70% - Computing grade
            self.update_progress_safe(0.7, "Computing grade...")
            if self.stop_requested: return
            
            top_final_grade = self.final_grade(top_class_ripeness, top_class_bruises, top_size_class)
            bottom_final_grade = self.final_grade(bottom_class_ripeness, bottom_class_bruises, bottom_size_class)
            average_final_grade = (top_final_grade + bottom_final_grade) / 2
            letter_grade = self.find_grade(average_final_grade)
            
            # Progress: 75% - Final motor movement
            self.update_progress_safe(0.75, "Final positioning...")
            if self.stop_requested: return
            
            self.moveMotor(1, 0, 0, 1)
            
            # Progress from 75% to 100% during 15 second sleep
            for i in range(15):
                if self.stop_requested: return
                progress = 0.75 + (i * 0.005)  # Increment by 0.5% each time (0.005 * 50 = 0.25 = 25%)
                self.update_progress_safe(progress, "Completing process...")
                time.sleep(0.3)  # Sleep for 0.3 seconds, 50 times = 15 seconds
            
            self.stopMotor()
            
            resultArray = [top_class_ripeness, top_class_bruises, 
                           top_size_class,
                           top_final_grade,
                            bottom_class_ripeness, bottom_class_bruises, 
                            bottom_size_class,
                            bottom_final_grade,
                            letter_grade
                           ]
            
            # Process complete
            self.update_progress_safe(1.0, "Process complete!")
            # Enable input from user priority
            self.ripeness_combo.configure(state="normal")  # or "readonly"
            self.bruises_combo.configure(state="normal")
            self.size_combo.configure(state="normal")
            
            self.root.after(0, self.processing_completed(resultArray))
            
        except Exception as e:
            print(f"Error in update_gui: {str(e)}")
            self.root.after(0, lambda: self.processing_stopped(f"Error: {str(e)}"))
            
    def update_progress_safe(self, progress, message):
        """Update progress from a background thread safely"""
        self.current_progress = progress
        self.root.after(0, lambda: self.update_progress_ui(progress, message))
    
    def update_progress_ui(self, progress, message):
        """Update the UI elements related to progress"""
        self.progress_bar.set(progress)
        # Format as percentage
        percent = int(progress * 100)
        self.progress_label.configure(text=f"{message} {percent}%")
        
    def update_top_results(self, image, ripeness, bruises, size):
        """Update the UI with top results"""
        def update():
            self.top_result_label.configure(
                text=f"Ripeness: {ripeness}\nBruises: {bruises}\nSize: {size}"
            )
            top_photo = ImageTk.PhotoImage(image.resize((300, 200)))
            self.top_canvas.create_image(0, 0, anchor=tk.NW, image=top_photo)
            self.top_canvas.image = top_photo  # Keep a reference
        self.root.after(0, update)
    
    def update_bottom_results(self, image, ripeness, bruises, size):
        """Update the UI with bottom results"""
        def update():
            self.bottom_result_label.configure(
                text=f"Ripeness: {ripeness}\nBruises: {bruises}\nSize: {size}"
            )
            bottom_photo = ImageTk.PhotoImage(image.resize((300, 200)))
            self.bottom_canvas.create_image(0, 0, anchor=tk.NW, image=bottom_photo)
            self.bottom_canvas.image = bottom_photo  # Keep a reference
        self.root.after(0, update)
    
    # Method stubs that would be implemented in the actual code
    def validate_inputs(self):
        # Check that combo boxes have selections
        if not self.ripeness_combo.get() or not self.bruises_combo.get() or not self.size_combo.get():
            # Show an error message
            tk.messagebox.showerror("Input Error", "Please select values for Ripeness, Bruises, and Size")
            return False
        return True
######################################################################################
    def capture_image(self, picam2):
        # This would be implemented to capture an image from the camera
        # Placeholder implementation
        image = picam2.capture_array()
        image = Image.fromarray(image).convert("RGB")
        return image
    
    def classify_image(self, image, model, class_labels):
        # This would be implemented to classify the image
        # Placeholder implementation
        image = self.transform(image).unsqueeze(0).to(self.device)
        output = model(image)
        _, predicted = torch.max(output, 1)
        return class_labels[predicted.item()]
    
    def final_grade(self,r,b,s):
        r_priority = float(self.ripeness_combo.get())
        b_priority = float(self.bruises_combo.get())
        s_priority = float(self.size_combo.get())
        resulting_grade = r_priority*self.ripeness_scores[r] + b_priority*self.bruiseness_scores[b] + s_priority*self.size_scores[s]
        print(f"Resulting Grade: {resulting_grade}")
        return resulting_grade
    
    def find_grade(self,input_grade):
        r_priority = float(self.ripeness_combo.get())
        b_priority = float(self.bruises_combo.get())
        s_priority = float(self.size_combo.get())
        max_gradeA = r_priority*self.ripeness_scores['green'] + b_priority*self.bruiseness_scores['unbruised'] + s_priority*self.size_scores['large']
        min_gradeC = r_priority*self.ripeness_scores['yellow'] + b_priority*self.bruiseness_scores['bruised'] + s_priority*self.size_scores['small']
        difference = (max_gradeA - min_gradeC)/3
        min_gradeA = max_gradeA - difference
        max_gradeB = min_gradeA
        min_gradeB = max_gradeB - difference
        max_gradeC = min_gradeB
        min_gradeC = max_gradeC - difference
        print("Calculated Grade Range")
        print(f"Max Grade A: {max_gradeA}, Min Grade A: {min_gradeA}, Difference: {max_gradeA-min_gradeA}")
        print(f"Max Grade B: {max_gradeB}, Min Grade B: {min_gradeB}, Difference: {max_gradeB-min_gradeB}")
        print(f"Max Grade C: {max_gradeC}, Min Grade C: {min_gradeC}, Difference: {max_gradeC-min_gradeC}")
        
        if (input_grade >= min_gradeA) and (input_grade <= max_gradeA):
            # self.grade_score.configure(text=f"Grade - A")
            self.move_to_position(self.position1)
            return "A"
        elif (input_grade >= min_gradeB) and (input_grade < max_gradeB):
            # self.grade_score.configure(text=f"Grade - B")
            self.move_to_position(self.position2)
            return "B"
        else:
            # self.grade_score.configure(text=f"Grade - C")
            self.move_to_position(self.position3)
            return "C"
    
    def move_to_position(self,target):
        steps_needed = target - self.current_position
        
        if steps_needed == 0:
            return  # Already at position
        
        # Set direction
        direction = GPIO.HIGH if steps_needed > 0 else GPIO.LOW
        GPIO.output(self.dir_pin, direction)
        
        # Move required steps
        for _ in range(abs(steps_needed)):
            GPIO.output(self.step_pin, GPIO.HIGH)
            time.sleep(self.step_delay)
            GPIO.output(self.step_pin, GPIO.LOW)
            time.sleep(self.step_delay)
        
        # Update current position
        self.current_position = target
    
    def moveMotor(self,val1=0,val2=0,val3=0,val4=0):
        GPIO.output(self.relay1, val1)  # Motor 1 Forward
        GPIO.output(self.relay2, val2)   # Motor 1 Reverse OFF
        GPIO.output(self.relay3, val3)  # Motor 2 Forward
        GPIO.output(self.relay4, val4)   # Motor 2 Reverse OFF

    def stopMotor(self):
        GPIO.output(self.relay1, GPIO.LOW)  # Motor 1 Forward
        GPIO.output(self.relay2, GPIO.LOW)   # Motor 1 Reverse OFF
        GPIO.output(self.relay3, GPIO.LOW)  # Motor 2 Forward
        GPIO.output(self.relay4, GPIO.LOW)   # Motor 2 Reverse OFF
######################################################################################
    def update_progress(self, progress):
        """Update the progress bar"""
        self.progress_bar.set(progress)
        
        # Format as percentage
        percent = int(progress * 100)
        self.progress_label.configure(text=f"Progress: {percent}%")
    
    def processing_completed(self, resultArray):
        """Called when processing completes successfully"""
        self.processing = False
        self.progress_label.configure(text="Processing completed")
        
        # Re-enable buttons
        self.start_button.configure(state="normal")
        self.stop_button.configure(text="Exit")  # Change text back to "Exit"
        self.reset_button.configure(state="normal")
            # resultArray = [top_class_ripeness, top_class_bruises, top_size_class,
            #                top_final_grade, bottom_class_ripeness, bottom_class_bruises, 
            #                 bottom_size_class, bottom_final_grade, letter_grade
            #                ]
        self.update_results(resultArray[0], resultArray[1], resultArray[2], 
                            resultArray[3], resultArray[4], resultArray[5], 
                            resultArray[6], resultArray[7], resultArray[8])
    def stop_processing(self):
        """Stop the processing or exit the program"""
        exit_text = self.stop_button.cget("text")  # Get the button text
        if exit_text == "Exit":
            print("Stopping processing...")
            self.exit_program()
        if self.processing:
            self.stopMotor()
            # If processing is active, stop it
            self.stop_requested = True
            self.reset_button.configure(state="normal")
            # Update button text back to "Exit" for when processing finishes
            self.stop_button.configure(text="Exit")
        else:
            # If not processing, exit the program
            self.exit_program()

    def processing_stopped(self):
        """Called when processing is stopped by user"""
        self.processing = False
        self.progress_label.configure(text="Processing stopped")
        
        # Re-enable buttons
        self.start_button.configure(state="normal")
        self.stop_button.configure(text="Exit")  # Change text back to "Exit"
        self.reset_button.configure(state="normal")
    
    def reset_system(self):
        GPIO.cleanup()  # Reset GPIO settings
        self.picam2.stop()
        os.execv(sys.executable, [sys.executable] + sys.argv)
    
    def update_results(self, top_ripeness, top_bruises, top_size, top_score_val,
                     bottom_ripeness, bottom_bruises, bottom_size, bottom_score_val, grade):
        """Update result labels with analysis data"""
        self.top_result_label.configure(text=f"Ripeness: {top_ripeness}\nBruises: {top_bruises}\nSize: {top_size}")
        self.bottom_result_label.configure(text=f"Ripeness: {bottom_ripeness}\nBruises: {bottom_bruises}\nSize: {bottom_size}")
        
        self.top_score.configure(text=f"Top Score - {top_score_val}")
        self.bottom_score.configure(text=f"Bottom Score - {bottom_score_val}")
        self.grade_score.configure(text=f"Grade - {grade}")
    
    def show_help(self):
        """Display help information in a scrollable, styled window"""
        help_window = ctk.CTkToplevel(self.root, fg_color="#e5e0d8")
        help_window.title("Help Guide")
        help_window.geometry("800x500")
        help_window.minsize(600, 400)
        help_window.grid_columnconfigure(0, weight=1)
        help_window.grid_rowconfigure(0, weight=1)

        # Create main frame for better layout control
        main_frame = ctk.CTkFrame(help_window, fg_color="#B3B792")
        main_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)

        # Add header
        header_label = ctk.CTkLabel(
            main_frame,
            text="Help Guide",
            font=("Arial Bold", 16),
            anchor="w"
        )
        header_label.grid(row=0, column=0, padx=10, pady=(5, 10), sticky="ew")

        # Create scrollable textbox
        help_textbox = ctk.CTkTextbox(
            main_frame,
            wrap="word",
            font=("Arial", 13),
            fg_color=("#d5dade"),
            scrollbar_button_color=("#3B8ED0", "#1F6AA5"),
            scrollbar_button_hover_color=("#36719F", "#184E73"),
            padx=10,
            pady=10
        )
        help_textbox.grid(row=1, column=0, sticky="nsew")

        # Insert help text
        help_text = hp()
        help_textbox.insert("1.0", help_text)
        help_textbox.configure(state="disabled")  # Make read-only

        # Add close button
        close_button = ctk.CTkButton(
            main_frame,
            text="Close",
            command=help_window.destroy,
            width=100,
            fg_color="#F3533A",
            hover_color="#db4b35"
        )
        close_button.grid(row=2, column=0, padx=10, pady=(15, 10), sticky="e")

        # Make window stay on top
        help_window.attributes('-topmost', True)
        help_window.after(200, lambda: help_window.attributes('-topmost', False))
        
    def checkbox_event(self):
        """Handle checkbox state changes"""
        state = self.check_var.get()
        if state == "on":
            # Set default priority values
            self.ripeness_combo.set(3.0)
            self.bruises_combo.set(3.0)
            self.size_combo.set(3.0)
        
    
    def update_video_feed(self):
        """Updates the video feed on the Tkinter canvas."""
        
        
        # Capture frame from the camera
        frame = self.picam2.capture_array()
        frame = Image.fromarray(frame).convert("RGB")  # Convert RGBA to RGB
        
        # Resize and convert to PhotoImage
        frame = frame.resize((300, 200))
        frame = ImageTk.PhotoImage(frame)
        
        # Update the video canvas with the new frame
        self.video_canvas.create_image(0, 0, anchor=tk.NW, image=frame)
        self.video_canvas.image = frame
        
        # Schedule the next update
        root.after(10, self.update_video_feed)
    
    def exit_program(self):
        """Clean up and exit the application"""
        if self.processing:
            self.stop_requested = True
        self.picam2.stop()
        self.root.destroy()
        GPIO.cleanup()  # Reset GPIO settings
        sys.exit(0)
# UML Diagram
# pyreverse -o html run.py
# pyreverse -o png run.py
# Main application
if __name__ == "__main__":
    root = ctk.CTk(fg_color="#e5e0d8")
    app = MangoGraderApp(root)
    # Make sure the exit_program is called when closing the window
    root.protocol("WM_DELETE_WINDOW", app.exit_program)
    root.mainloop()