import torch
import torchvision.transforms as transforms
from efficientnet_pytorch import EfficientNet
from PIL import Image, ImageTk
import time
import tkinter as tk
import customtkinter as ctk
from tkinter import ttk  # For combo boxes
# from picamera2 import Picamera2
from datetime import datetime
import numpy as np
from scipy.spatial import distance as dist
from imutils import perspective
from imutils import contours
import imutils
import cv2
import sys
import os
import csv
from tkinter import ttk, messagebox
import threading
# import RPi.GPIO as GPIO

class MangoGraderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Carabao Mango Grader and Sorter")
        self.root.fg_color = "#e5e0d8"
        
        # Initialize camera
        # self.picam2 = Picamera2()
        # self.camera_config = self.picam2.create_video_configuration(main={"size": (1920, 1080)})
        # self.picam2.configure(self.camera_config)
        # self.picam2.start()
        
        # Processing state flags
        self.processing = False
        self.stop_requested = False
        self.current_progress = 0
        
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
        
        self.stop_button = ctk.CTkButton(right_frame, text="Stop", fg_color="#F3533A",
                                       command=self.stop_processing, state="disabled")
        self.stop_button.grid(row=0, column=1, padx=10, pady=10, sticky="ns")
        
        self.reset_button = ctk.CTkButton(right_frame, text="Reset", fg_color="#5CACF9",
                                        command=self.reset_system)
        self.reset_button.grid(row=1, column=0, padx=10, pady=10, sticky="ns")
        
        self.help_button = ctk.CTkButton(right_frame, text="Help", fg_color="#f85cf9",
                                       command=self.show_help)
        self.help_button.grid(row=1, column=1, padx=10, pady=10, sticky="ns")
        
        # Progress bar
        self.progress_label = ctk.CTkLabel(right_frame, text="Progress:")
        self.progress_label.grid(row=2, column=0, sticky="w", padx=10)
        
        self.progress_bar = ctk.CTkProgressBar(right_frame, width=200, mode="determinate")
        self.progress_bar.grid(row=2, column=0, columnspan=2, padx=10, pady=(30, 10), sticky="ew")
        self.progress_bar.set(0)  # Initialize at 0
        
        # Toggle Button
        self.check_var = ctk.StringVar(value="off")
        checkbox = ctk.CTkCheckBox(right_frame, text="Default", command=self.checkbox_event,
                                   variable=self.check_var, onvalue="on", offvalue="off")
        checkbox.grid(row=3, column=1, padx=10, pady=10, sticky="ns")
        
        # Score displays
        self.top_score = ctk.CTkLabel(right_frame, text="Top Score - ")
        self.top_score.grid(row=4, column=0)
        
        self.bottom_score = ctk.CTkLabel(right_frame, text="Bottom Score - ")
        self.bottom_score.grid(row=5, column=0)
        
        self.grade_score = ctk.CTkLabel(right_frame, text="Grade - ")
        self.grade_score.grid(row=6, column=0)
        
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
    
    def start_processing(self):
        """Start the processing with a loading bar"""
        if not self.processing:
            if not self.validate_inputs():
                return  # Stop execution if validation fails
                
            self.processing = True
            self.stop_requested = False
            
            # Update button states
            self.start_button.configure(state="disabled")
            self.stop_button.configure(state="normal")
            self.reset_button.configure(state="disabled")
            
            # Reset progress bar
            self.progress_bar.set(0)
            self.current_progress = 0
            
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
            
            self.moveMotor(0, 1, 1, 0)
            
            # Progress from 10% to 20% during 5 second sleep
            for i in range(10):
                if self.stop_requested: return
                progress = 0.1 + (i * 0.01)
                self.update_progress_safe(progress, "Positioning for top capture...")
                time.sleep(0.5)  # Sleep for 0.5 seconds, 10 times = 5 seconds
            
            self.stopMotor()
            
            # Progress: 20% - Capturing top part
            self.update_progress_safe(0.2, "Capturing top part...")
            if self.stop_requested: return
            
            self.root.after(0, lambda: self.top_label.configure(text="Capturing top part of the mango..."))
            top_image = self.capture_image(self.picam2)
            top_image.save(f"{formatted_date_time}_top.png")
            
            # Progress: 25% - Analyzing top part
            self.update_progress_safe(0.25, "Analyzing top part...")
            if self.stop_requested: return
            
            top_class_ripeness = self.classify_image(top_image, self.model_ripeness, self.class_labels_ripeness)
            top_class_bruises = self.classify_image(top_image, self.model_bruises, self.class_labels_bruises)
            top_width, top_length = self.calculate_size(f"{formatted_date_time}_top.png", 
                                                      f"{formatted_date_time}_background.png", 
                                                      formatted_date_time, 
                                                      top=True)
            
            # Update UI with top results
            self.update_top_results(top_image, top_class_ripeness, top_class_bruises, top_width, top_length)
            
            # Progress: 30% - Moving motor for bottom capture
            self.update_progress_safe(0.3, "Moving motor for bottom capture...")
            if self.stop_requested: return
            
            self.moveMotor(0, 1, 0, 1)
            
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
            
            self.root.after(0, lambda: self.bottom_label.configure(text="Capturing bottom part of the mango..."))
            bottom_image = self.capture_image(self.picam2)
            bottom_image.save(f"{formatted_date_time}_bottom.png")
            
            # Progress: 50% - Analyzing bottom part
            self.update_progress_safe(0.5, "Analyzing bottom part...")
            if self.stop_requested: return
            
            bottom_class_ripeness = self.classify_image(bottom_image, self.model_ripeness, self.class_labels_ripeness)
            bottom_class_bruises = self.classify_image(bottom_image, self.model_bruises, self.class_labels_bruises)
            bottom_width, bottom_length = self.calculate_size(f"{formatted_date_time}_bottom.png", 
                                                            f"{formatted_date_time}_background.png", 
                                                            formatted_date_time, 
                                                            top=False)
            
            # Update UI with bottom results
            self.update_bottom_results(bottom_image, bottom_class_ripeness, bottom_class_bruises, bottom_width, bottom_length)
            
            # Progress: 60% - Computing scores
            self.update_progress_safe(0.6, "Computing scores...")
            if self.stop_requested: return
            
            top_size_class = self.determine_size(top_width, top_length)
            self.calculate_total_score(
                self.ripeness_scores[top_class_ripeness], 
                self.bruiseness_scores[top_class_bruises], 
                self.size_scores[top_size_class], 
                r=top_class_ripeness, 
                b=top_class_bruises, 
                s=top_size_class, 
                top=True
            )
            
            bottom_size_class = self.determine_size(bottom_width, bottom_length)
            self.calculate_total_score(
                self.ripeness_scores[bottom_class_ripeness], 
                self.bruiseness_scores[bottom_class_bruises], 
                self.size_scores[bottom_size_class], 
                r=bottom_class_ripeness, 
                b=bottom_class_bruises, 
                s=bottom_size_class, 
                top=False
            )
            
            # Progress: 70% - Computing grade
            self.update_progress_safe(0.7, "Computing grade...")
            if self.stop_requested: return
            
            top_final_grade = self.final_grade(top_class_ripeness, top_class_bruises, top_size_class)
            bottom_final_grade = self.final_grade(bottom_class_ripeness, bottom_class_bruises, bottom_size_class)
            average_final_grade = (top_final_grade + bottom_final_grade) / 2
            self.find_grade(average_final_grade)
            
            # Progress: 75% - Final motor movement
            self.update_progress_safe(0.75, "Final positioning...")
            if self.stop_requested: return
            
            self.moveMotor(1, 0, 1, 0)
            
            # Progress from 75% to 100% during 15 second sleep
            for i in range(50):
                if self.stop_requested: return
                progress = 0.75 + (i * 0.005)  # Increment by 0.5% each time (0.005 * 50 = 0.25 = 25%)
                self.update_progress_safe(progress, "Completing process...")
                time.sleep(0.3)  # Sleep for 0.3 seconds, 50 times = 15 seconds
            
            self.stopMotor()
            
            # Process complete
            self.update_progress_safe(1.0, "Process complete!")
            self.root.after(0, self.processing_completed)
            
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
    
    def update_top_results(self, image, ripeness, bruises, width, length):
        """Update the UI with top results"""
        def update():
            self.top_result_label.configure(
                text=f"Ripeness: {ripeness}\nBruises: {bruises}\nSize: {width:.2f} cm (W) x {length:.2f} cm (L)"
            )
            top_photo = ImageTk.PhotoImage(image.resize((300, 200)))
            self.top_canvas.create_image(0, 0, anchor=tk.NW, image=top_photo)
            self.top_canvas.image = top_photo  # Keep a reference
        self.root.after(0, update)
    
    def update_bottom_results(self, image, ripeness, bruises, width, length):
        """Update the UI with bottom results"""
        def update():
            self.bottom_result_label.configure(
                text=f"Ripeness: {ripeness}\nBruises: {bruises}\nSize: {width:.2f} cm (W) x {length:.2f} cm (L)"
            )
            bottom_photo = ImageTk.PhotoImage(image.resize((300, 200)))
            self.bottom_canvas.create_image(0, 0, anchor=tk.NW, image=bottom_photo)
            self.bottom_canvas.image = bottom_photo  # Keep a reference
        self.root.after(0, update)
    
    def stop_processing(self):
        """Stop the processing"""
        if self.processing:
            self.stop_requested = True
            self.root.after(0, lambda: self.processing_stopped("Processing stopped by user"))
        else:
            # GPIO.cleanup()
            sys.exit(0)
    
    def processing_completed(self):
        """Called when processing completes successfully"""
        self.processing = False
        
        # Re-enable buttons
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="normal")
        self.reset_button.configure(state="normal")
    
    def processing_stopped(self, message="Processing stopped"):
        """Called when processing is stopped by user or error"""
        self.processing = False
        self.progress_label.configure(text=message)
        
        # Re-enable buttons
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="normal")
        self.reset_button.configure(state="normal")
    
        """BEGIN

        FIX ALL THIS BELOW
            
        """
    # Method stubs that would be implemented in the actual code
    def validate_inputs(self):
        # Check that combo boxes have selections
        if not self.ripeness_combo.get() or not self.bruises_combo.get() or not self.size_combo.get():
            # Show an error message
            tk.messagebox.showerror("Input Error", "Please select values for Ripeness, Bruises, and Size")
            return False
        return True
    
    def capture_image(self, camera):
        # This would be implemented to capture an image from the camera
        # Placeholder implementation
        return Image.new('RGB', (300, 200), color='gray')
    
    def classify_image(self, image, model, class_labels):
        # This would be implemented to classify the image
        # Placeholder implementation
        return class_labels[0]
    
    def calculate_size(self, image_path, background_path, timestamp, top=True):
        # This would be implemented to calculate the size
        # Placeholder implementation
        return 5.0, 7.0
    
    def determine_size(self, width, length):
        # This would be implemented to determine the size class
        # Placeholder implementation
        return "Medium"
    
    def calculate_total_score(self, ripeness_score, bruises_score, size_score, r, b, s, top=True):
        # This would be implemented to calculate the total score
        # Placeholder implementation
        score = ripeness_score + bruises_score + size_score
        if top:
            self.top_score.configure(text=f"Top Score - {score}")
        else:
            self.bottom_score.configure(text=f"Bottom Score - {score}")
    
    def final_grade(self, ripeness, bruises, size):
        # This would be implemented to calculate the final grade
        # Placeholder implementation
        return 85
    
    def find_grade(self, average_score):
        # This would be implemented to determine the grade
        # Placeholder implementation
        grade = "A"
        self.grade_score.configure(text=f"Grade - {grade}")
    
    def moveMotor(self, m1, m2, m3, m4):
        # This would be implemented to move the motor
        # Placeholder implementation
        pass
    
    def stopMotor(self):
        # This would be implemented to stop the motor
        # Placeholder implementation
        pass
    
        """END

        FIX ALL THIS ABOVE
            
        """
    
    def update_progress(self, progress):
        """Update the progress bar"""
        self.progress_bar.set(progress)
        
        # Format as percentage
        percent = int(progress * 100)
        self.progress_label.configure(text=f"Progress: {percent}%")
    
    def stop_processing(self):
        """Stop the processing"""
        if self.processing:
            self.stop_requested = True
            # The processing_stopped method will be called from run_processing
    
    def processing_completed(self):
        """Called when processing completes successfully"""
        self.processing = False
        self.progress_label.configure(text="Processing completed")
        
        # Re-enable buttons
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.reset_button.configure(state="normal")
        
        # Simulate completed analysis (in a real app, this would come from the actual analysis)
        self.update_results("Ripe", "None", "Large", "Unripe", "Minor", "Medium", "Grade A")
    
    def processing_stopped(self):
        """Called when processing is stopped by user"""
        self.processing = False
        self.progress_label.configure(text="Processing stopped")
        
        # Re-enable buttons
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.reset_button.configure(state="normal")
    
    def reset_system(self):
        """Reset the system to initial state"""
        # Reset progress bar and label
        self.progress_bar.set(0)
        self.progress_label.configure(text="Progress:")
        
        # Reset result labels
        self.top_result_label.configure(text="Ripeness: -\nBruises: -\nSize: -")
        self.bottom_result_label.configure(text="Ripeness: -\nBruises: -\nSize: -")
        self.top_score.configure(text="Top Score - ")
        self.bottom_score.configure(text="Bottom Score - ")
        self.grade_score.configure(text="Grade - ")
    
    def update_results(self, top_ripeness, top_bruises, top_size, 
                     bottom_ripeness, bottom_bruises, bottom_size, grade):
        """Update result labels with analysis data"""
        self.top_result_label.configure(text=f"Ripeness: {top_ripeness}\nBruises: {top_bruises}\nSize: {top_size}")
        self.bottom_result_label.configure(text=f"Ripeness: {bottom_ripeness}\nBruises: {bottom_bruises}\nSize: {bottom_size}")
        
        # Calculate scores (in a real app this would be based on actual analysis)
        top_score_val = 85
        bottom_score_val = 70
        
        self.top_score.configure(text=f"Top Score - {top_score_val}")
        self.bottom_score.configure(text=f"Bottom Score - {bottom_score_val}")
        self.grade_score.configure(text=f"Grade - {grade}")
    
    def show_help(self):
        """Display help information"""
        help_window = ctk.CTkToplevel(self.root)
        help_window.title("Help")
        help_window.geometry("400x300")
        
        help_text = """
        Carabao Mango Grader and Sorter
        ------------------------------
        
        Start: Begin the grading process
        Stop: Stop the current process
        Reset: Reset all values to default
        
        User Priority: Set your preferences for
        ripeness, bruises, and size scoring.
        """
        
        help_label = ctk.CTkLabel(help_window, text=help_text, justify="left")
        help_label.pack(padx=20, pady=20)
    
    def checkbox_event(self):
        """Handle checkbox state changes"""
        state = self.check_var.get()
        if state == "on":
            # Set default priority values
            self.ripeness_combo.set(2.0)
            self.bruises_combo.set(1.0)
            self.size_combo.set(2.0)
        else:
            # Clear priority values
            self.ripeness_combo.set("")
            self.bruises_combo.set("")
            self.size_combo.set("")
    
    def update_video_feed(self):
        """Update the video feed from the camera"""
        # In a real implementation, this would capture frames from the camera
        # and update the video_canvas
        
        # For now, just draw a placeholder rectangle
        self.video_canvas.delete("all")
        self.video_canvas.create_rectangle(50, 50, 250, 150, fill="gray")
        self.video_canvas.create_text(150, 100, text="Live Camera Feed", fill="white")
        
        # Schedule the next update
        self.root.after(100, self.update_video_feed)
    
    def exit_program(self):
        """Clean up and exit the application"""
        if self.processing:
            self.stop_requested = True
        self.picam2.stop()
        self.root.destroy()

# Main application
if __name__ == "__main__":
    root = ctk.CTk(fg_color="#e5e0d8")
    app = MangoGraderApp(root)
    # Make sure the exit_program is called when closing the window
    root.protocol("WM_DELETE_WINDOW", app.exit_program)
    root.mainloop()