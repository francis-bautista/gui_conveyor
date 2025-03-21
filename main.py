import torch
import torchvision.transforms as transforms
from efficientnet_pytorch import EfficientNet
from PIL import Image, ImageTk
import time
import tkinter as tk
import customtkinter as ctk
from tkinter import ttk, messagebox
from picamera2 import Picamera2
from datetime import datetime
import numpy as np
from scipy.spatial import distance as dist
from imutils import perspective, contours
import imutils
import cv2
import sys
import os
import RPi.GPIO as GPIO

# Constants
FOCAL_LENGTH_PIXELS = 2710
DISTANCE_CAMERA_TO_OBJECT = 40  # cm
STEPS_PER_REVOLUTION = 200
STEP_DELAY = 0.001

class MotorController:
    def __init__(self):
        self.relay_pins = [6, 13, 19, 26]
        self.stepper_pins = (21, 20)
        self.positions = [50, 100, 150]
        self.current_position = 0
        
        GPIO.setmode(GPIO.BCM)
        self._setup_gpio()
        
    def _setup_gpio(self):
        for pin in self.relay_pins:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)
            
        GPIO.setup(self.stepper_pins[0], GPIO.OUT)
        GPIO.setup(self.stepper_pins[1], GPIO.OUT)
        GPIO.output(self.stepper_pins[0], GPIO.LOW)
        GPIO.output(self.stepper_pins[1], GPIO.LOW)

    def move_to_position(self, target_idx):
        target = self.positions[target_idx]
        steps_needed = target - self.current_position
        if steps_needed == 0: return
        
        direction = GPIO.HIGH if steps_needed > 0 else GPIO.LOW
        GPIO.output(self.stepper_pins[0], direction)
        
        for _ in range(abs(steps_needed)):
            GPIO.output(self.stepper_pins[1], GPIO.HIGH)
            time.sleep(STEP_DELAY)
            GPIO.output(self.stepper_pins[1], GPIO.LOW)
            time.sleep(STEP_DELAY)
            
        self.current_position = target

    def control_motors(self, *states):
        for pin, state in zip(self.relay_pins, states):
            GPIO.output(pin, state)

    def cleanup(self):
        GPIO.cleanup()

class MangoClassifier:
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.class_labels = {
            'ripeness': ['green', 'yellow_green', 'yellow'],
            'bruises': ['bruised', 'unbruised'],
            'size': ['small', 'medium', 'large']
        }
        self.scores = {
            'ripeness': {'yellow': 1.0, 'yellow_green': 2.0, 'green': 3.0},
            'bruises': {'bruised': 1.5, 'unbruised': 3.0},
            'size': {'small': 1.0, 'medium': 2.0, 'large': 3.0}
        }
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])
        
        self.models = {
            'ripeness': self._load_model("ripeness.pth", len(self.class_labels['ripeness'])),
            'bruises': self._load_model("bruises.pth", len(self.class_labels['bruises']))
        }

    def _load_model(self, path, num_classes):
        model = EfficientNet.from_pretrained('efficientnet-b0', num_classes=num_classes)
        model.load_state_dict(torch.load(path, map_location=self.device))
        model.eval()
        return model.to(self.device)

    def classify(self, image, model_type):
        image_tensor = self.transform(image).unsqueeze(0).to(self.device)
        with torch.no_grad():
            outputs = self.models[model_type](image_tensor)
        return self.class_labels[model_type][torch.argmax(outputs).item()]

    @staticmethod
    def calculate_dimensions(image_path, bg_path, timestamp, is_top=True):
        suffix = "top" if is_top else "bottom"
        try:
            fg = cv2.imread(image_path)
            bg = cv2.imread(bg_path)
            if fg is None or bg is None: return 0, 0

            diff = cv2.absdiff(fg, bg)
            gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY)
            
            cnts = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cnts = imutils.grab_contours(cnts)
            if not cnts: return 0, 0
            
            largest = max(cnts, key=cv2.contourArea)
            if cv2.contourArea(largest) < 100: return 0, 0
            
            box = cv2.minAreaRect(largest)
            box = cv2.boxPoints(box)
            (tl, tr, br, bl) = imutils.perspective.order_points(box)
            
            width_px = dist.euclidean(tl, tr)
            length_px = dist.euclidean(tr, br)
            
            return (
                (width_px * DISTANCE_CAMERA_TO_OBJECT) / FOCAL_LENGTH_PIXELS,
                (length_px * DISTANCE_CAMERA_TO_OBJECT) / FOCAL_LENGTH_PIXELS
            )
        except Exception as e:
            print(f"Size calculation error: {e}")
            return 0, 0

    def determine_size(self, width, length):
        area = width * length
        if area < (11.5 * 8.5): return 'small'
        if area < (12.5 * 8.5): return 'medium'
        return 'large'

class CameraHandler:
    def __init__(self):
        self.picam2 = Picamera2()
        config = self.picam2.create_video_configuration(main={"size": (1920, 1080)})
        self.picam2.configure(config)
        self.picam2.start()

    def capture(self):
        return Image.fromarray(self.picam2.capture_array()).convert("RGB")

    def stop(self):
        self.picam2.stop()

class MangoGraderApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Carabao Mango Grader")
        self.geometry("1200x800")
        self.configure_grid()
        
        self.motor = MotorController()
        self.classifier = MangoClassifier()
        self.camera = CameraHandler()
        
        self.scores = {}
        self.current_images = {}
        self.background = None
        
        self._create_widgets()
        self.after(10, self.update_video)

    def configure_grid(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

    def _create_widgets(self):
        # Left Panel - Results
        left_frame = ctk.CTkFrame(self, fg_color="#B3B792")
        left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        # Right Panel - Controls
        right_frame = ctk.CTkFrame(self, fg_color="#B3B792")
        right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
        # Video Panel
        video_frame = ctk.CTkFrame(self, fg_color="#B3B792")
        video_frame.grid(row=0, column=2, padx=10, pady=10, sticky="nsew")
        
        # Initialize components
        self._create_result_ui(left_frame)
        self._create_control_ui(right_frame)
        self._create_video_ui(video_frame)

    def _create_result_ui(self, parent):
        # Implementation of result UI components
        pass

    def _create_control_ui(self, parent):
        # Implementation of control UI components
        pass

    def _create_video_ui(self, parent):
        # Implementation of video UI components
        pass

    def update_video(self):
        frame = self.camera.capture()
        # Update video feed canvas
        self.after(10, self.update_video)

    def capture_images(self):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.background = self.camera.capture()
        self.background.save(f"{timestamp}_background.png")
        
        # Capture top
        self.motor.control_motors(0,1,1,0)
        time.sleep(15)
        self.current_images['top'] = self.camera.capture()
        
        # Capture bottom
        self.motor.control_motors(0,1,0,1)
        time.sleep(15)
        self.current_images['bottom'] = self.camera.capture()
        
        # Process images
        self.process_images(timestamp)

    def process_images(self, timestamp):
        # Classification and size calculation
        pass

    def calculate_score(self):
        # Score calculation logic
        pass

    def cleanup(self):
        self.motor.cleanup()
        self.camera.stop()
        self.destroy()

if __name__ == "__main__":
    app = MangoGraderApp()
    app.mainloop()
    app.cleanup()