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
import RPi.GPIO as GPIO
import threading
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
        
        self.stop_button = ctk.CTkButton(right_frame, text="Stop", fg_color="#F3533A",
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
        if not self.processing:
            self.processing = True
            self.stop_requested = False
            
            # Update button states
            self.start_button.configure(state="disabled")
            # Change text to "Stop" during processing
            self.stop_button.configure(text="Stop", state="normal")
            self.reset_button.configure(state="disabled")
            
            # Reset progress bar
            self.progress_bar.set(0)
            
            # Start processing in a separate thread
            self.process_thread = threading.Thread(target=self.run_processing)
            self.process_thread.daemon = True
            self.process_thread.start()
    
    def run_processing(self):
        """Run the 60-second processing with progress updates"""
        total_duration = 60  # 60 seconds
        interval = 0.1  # Update every 0.1 seconds
        steps = int(total_duration / interval)
        
        for i in range(steps + 1):
            if self.stop_requested:
                break
                
            # Calculate progress
            progress = i / steps
            
            # Update UI from the main thread
            self.root.after(0, self.update_progress, progress)
            
            # Sleep for the interval
            time.sleep(interval)
        
        # Done processing, update UI from main thread
        if not self.stop_requested:
            self.root.after(0, self.processing_completed)
        else:
            self.root.after(0, self.processing_stopped)
    
    def update_progress(self, progress):
        """Update the progress bar"""
        self.progress_bar.set(progress)
        
        # Format as percentage
        percent = int(progress * 100)
        self.progress_label.configure(text=f"Progress: {percent}%")
    
    def processing_completed(self):
        """Called when processing completes successfully"""
        self.processing = False
        self.progress_label.configure(text="Processing completed")
        
        # Re-enable buttons
        self.start_button.configure(state="normal")
        self.stop_button.configure(text="Exit")  # Change text back to "Exit"
        self.reset_button.configure(state="normal")
        
        # Simulate completed analysis (in a real app, this would come from the actual analysis)
        self.update_results("Ripe", "None", "Large", "Unripe", "Minor", "Medium", "Grade A")
    def stop_processing(self):
        """Stop the processing or exit the program"""
        if self.processing:
            # If processing is active, stop it
            self.stop_requested = True
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
    
    def processing_stopped(self):
        """Called when processing is stopped by user"""
        self.processing = False
        self.progress_label.configure(text="Processing stopped")
        
        # Re-enable buttons
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="normal")
        self.reset_button.configure(state="normal")
    
    def reset_system(self):
        GPIO.cleanup()  # Reset GPIO settings
        self.picam2.stop()
        os.execv(sys.executable, [sys.executable] + sys.argv)
    
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

# Main application
if __name__ == "__main__":
    root = ctk.CTk(fg_color="#e5e0d8")
    app = MangoGraderApp(root)
    # Make sure the exit_program is called when closing the window
    root.protocol("WM_DELETE_WINDOW", app.exit_program)
    root.mainloop()