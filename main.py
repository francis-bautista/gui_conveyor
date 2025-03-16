import torch
import torchvision.transforms as transforms
from efficientnet_pytorch import EfficientNet
from PIL import Image, ImageTk
import time
import tkinter as tk
import customtkinter as ctk
from tkinter import ttk, messagebox
from datetime import datetime
from scipy.spatial import distance as dist
import numpy as np
import cv2
import sys
import os
import imutils
import RPi.GPIO as GPIO
from picamera2 import Picamera2

# Constants
GPIO_MODE = GPIO.BCM
RELAY_PINS = {'motor1_forward': 6, 'motor1_reverse': 13, 
              'motor2_forward': 19, 'motor2_reverse': 26}
STEPPER_PINS = {'dir': 21, 'step': 20}
MOTOR_DELAY = 2  # seconds
STEPPER_PARAMS = {
    'steps_per_revolution': 200,
    'positions': [50, 100, 150],
    'step_delay': 0.001
}

CAMERA_RESOLUTION = (1920, 1080)
IMAGE_TRANSFORM = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

CLASS_LABELS = {
    'ripeness': ['green', 'yellow_green', 'yellow'],
    'bruises': ['bruised', 'unbruised'],
    'size': ['small', 'medium', 'large']
}

SCORING = {
    'ripeness': {'yellow': 1.0, 'yellow_green': 2.0, 'green': 3.0},
    'bruises': {'bruised': 1.5, 'unbruised': 3.0},
    'size': {'small': 1.0, 'medium': 2.0, 'large': 3.0}
}

SIZE_CALCULATION = {
    'focal_length': 2710,
    'distance': 40,
    'size_thresholds': {'small': 50, 'medium': 100}
}

class MotorController:
    """Handles motor control for both relay-based motors and stepper motor"""
    def __init__(self):
        self.current_position = 0
        self._setup_gpio()
        
    def _setup_gpio(self):
        """Initialize GPIO pins"""
        GPIO.setmode(GPIO_MODE)
        
        # Setup relays
        for pin in RELAY_PINS.values():
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)
            
        # Setup stepper
        for pin in STEPPER_PINS.values():
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)

    def move_relays(self, state):
        """Control relay-based motors"""
        GPIO.output(RELAY_PINS['motor1_forward'], state[0])
        GPIO.output(RELAY_PINS['motor1_reverse'], state[1])
        GPIO.output(RELAY_PINS['motor2_forward'], state[2])
        GPIO.output(RELAY_PINS['motor2_reverse'], state[3])

    def stop_motors(self):
        """Stop all motors"""
        self.move_relays([GPIO.LOW]*4)

    def move_stepper(self, target):
        """Move stepper motor to absolute position"""
        steps_needed = target - self.current_position
        if steps_needed == 0:
            return

        direction = GPIO.HIGH if steps_needed > 0 else GPIO.LOW
        GPIO.output(STEPPER_PINS['dir'], direction)

        for _ in range(abs(steps_needed)):
            GPIO.output(STEPPER_PINS['step'], GPIO.HIGH)
            time.sleep(STEPPER_PARAMS['step_delay'])
            GPIO.output(STEPPER_PINS['step'], GPIO.LOW)
            time.sleep(STEPPER_PARAMS['step_delay'])

        self.current_position = target

    def cleanup(self):
        """Cleanup GPIO resources"""
        self.stop_motors()
        GPIO.cleanup()

class CameraSystem:
    """Handles camera operations and image processing"""
    def __init__(self):
        self.picam2 = Picamera2()
        self._configure_camera()
        
    def _configure_camera(self):
        """Configure camera settings"""
        config = self.picam2.create_video_configuration(main={"size": CAMERA_RESOLUTION})
        self.picam2.configure(config)
        self.picam2.start()

    def capture_image(self):
        """Capture and return PIL Image"""
        time.sleep(1)  # Allow camera to adjust
        array = self.picam2.capture_array()
        return Image.fromarray(array).convert("RGB")

    def get_video_frame(self):
        """Get current frame for video feed"""
        array = self.picam2.capture_array()
        return Image.fromarray(array).convert("RGB")

    def stop(self):
        """Stop camera"""
        self.picam2.stop()

class FruitAnalyzer:
    """Handles fruit analysis using ML models and image processing"""
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.models = {
            'ripeness': self._load_model('ripeness.pth', len(CLASS_LABELS['ripeness'])),
            'bruises': self._load_model('bruises.pth', len(CLASS_LABELS['bruises']))
        }

    def _load_model(self, model_path, num_classes):
        """Load trained EfficientNet model"""
        model = EfficientNet.from_pretrained('efficientnet-b0', num_classes=num_classes)
        model.load_state_dict(torch.load(model_path, map_location=self.device))
        model.eval()
        return model.to(self.device)

    def classify_image(self, image, model_type):
        """Classify image using specified model"""
        model = self.models[model_type]
        transformed = IMAGE_TRANSFORM(image).unsqueeze(0).to(self.device)
        with torch.no_grad():
            outputs = model(transformed)
        _, predicted = torch.max(outputs, 1)
        return CLASS_LABELS[model_type][predicted.item()]

    @staticmethod
    def calculate_dimensions(foreground_path, background_path):
        """Calculate object dimensions using background subtraction"""
        try:
            fg = cv2.imread(foreground_path)
            bg = cv2.imread(background_path)
            
            if fg is None or bg is None:
                return 0, 0

            diff = cv2.absdiff(fg, bg)
            gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY)
            
            contours = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            contours = imutils.grab_contours(contours)
            contours = sorted(contours, key=cv2.contourArea, reverse=True)[:1]

            for c in contours:
                if cv2.contourArea(c) < 100:
                    continue
                box = cv2.minAreaRect(c)
                box = cv2.boxPoints(box)
                (tl, tr, br, bl) = imutils.perspective.order_points(box)
                
                width_px = dist.euclidean(tl, tr)
                length_px = dist.euclidean(tr, br)
                
                width = (2 * width_px * SIZE_CALCULATION['distance']) / SIZE_CALCULATION['focal_length']
                length = (2 * length_px * SIZE_CALCULATION['distance']) / SIZE_CALCULATION['focal_length']
                return width, length
                
            return 0, 0
        except Exception as e:
            print(f"Dimension calculation error: {e}")
            return 0, 0

class MangoGraderGUI(ctk.CTk):
    """Main application GUI"""
    def __init__(self):
        super().__init__()
        self.motor_controller = MotorController()
        self.camera_system = CameraSystem()
        self.analyzer = FruitAnalyzer()
        
        self.title("Carabao Mango Grader and Sorter")
        self.geometry("1200x800")
        self._setup_ui()
        self._running = True
        self.update_video_feed()

    def _setup_ui(self):
        """Configure GUI layout and widgets"""
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Left Panel - Results
        self.left_frame = ctk.CTkFrame(self, fg_color="#B3B792")
        self.left_frame.grid(row=0, column=0, sticky="nsew")
        self._create_result_sections()

        # Right Panel - Controls
        self.right_frame = ctk.CTkFrame(self, fg_color="#B3B792")
        self.right_frame.grid(row=0, column=1, sticky="nsew")
        self._create_control_sections()

    def _create_result_sections(self):
        """Create result display sections"""
        # Top result section
        self.top_label = ctk.CTkLabel(self.left_frame, text="Top Analysis")
        self.top_label.grid(row=0, column=0, pady=5)
        self.top_canvas = tk.Canvas(self.left_frame, width=300, height=200)
        self.top_canvas.grid(row=1, column=0)
        self.top_result = ctk.CTkLabel(self.left_frame, text="")
        self.top_result.grid(row=2, column=0)

        # Bottom result section
        self.bottom_label = ctk.CTkLabel(self.left_frame, text="Bottom Analysis")
        self.bottom_label.grid(row=3, column=0, pady=5)
        self.bottom_canvas = tk.Canvas(self.left_frame, width=300, height=200)
        self.bottom_canvas.grid(row=4, column=0)
        self.bottom_result = ctk.CTkLabel(self.left_frame, text="")
        self.bottom_result.grid(row=5, column=0)

    def _create_control_sections(self):
        """Create control widgets"""
        # Video feed
        self.video_canvas = tk.Canvas(self.right_frame, width=300, height=200)
        self.video_canvas.grid(row=0, column=0, columnspan=2, pady=10)

        # Control buttons
        controls = [
            ("Start", self.start_analysis, "#8AD879"),
            ("Stop", self.stop_program, "#F3533A"),
            ("Reset", self.reset_system, "#5CACF9"),
            ("Help", self.show_help, "#f85cf9")
        ]
        
        for i, (text, command, color) in enumerate(controls):
            btn = ctk.CTkButton(self.right_frame, text=text, 
                               fg_color=color, command=command)
            btn.grid(row=1, column=i%2, padx=5, pady=5)

        # Scoring inputs
        self._create_scoring_inputs()
        self._create_status_labels()

    def _create_scoring_inputs(self):
        """Create user input fields for scoring weights"""
        frame = ctk.CTkFrame(self.right_frame, fg_color="#809671")
        frame.grid(row=2, column=0, columnspan=2, pady=10, sticky="ew")
        
        inputs = [
            ("Ripeness Priority", "ripeness"),
            ("Bruises Priority", "bruises"),
            ("Size Priority", "size")
        ]
        
        self.scoring_vars = {}
        for i, (label, key) in enumerate(inputs):
            lbl = ctk.CTkLabel(frame, text=f"{label}:")
            lbl.grid(row=i, column=0, padx=5)
            
            combo = ttk.Combobox(frame, values=["0.0", "1.0", "2.0", "3.0"])
            combo.grid(row=i, column=1, padx=5)
            self.scoring_vars[key] = combo

        # Default values checkbox
        self.check_var = ctk.StringVar(value="off")
        ctk.CTkCheckBox(frame, text="Default Values", variable=self.check_var,
                       onvalue="on", offvalue="off", command=self.toggle_defaults).grid(row=3, columnspan=2)

    def _create_status_labels(self):
        """Create status display labels"""
        self.top_score = ctk.CTkLabel(self.right_frame, text="Top Score: -")
        self.top_score.grid(row=3, column=0)
        self.bottom_score = ctk.CTkLabel(self.right_frame, text="Bottom Score: -")
        self.bottom_score.grid(row=3, column=1)
        self.grade = ctk.CTkLabel(self.right_frame, text="Grade: -")
        self.grade.grid(row=4, columnspan=2)

    def toggle_defaults(self):
        """Toggle default values for scoring priorities"""
        if self.check_var.get() == "on":
            for var in self.scoring_vars.values():
                var.set("3.0")
        else:
            for var in self.scoring_vars.values():
                var.set("")

    def validate_inputs(self):
        """Validate user inputs"""
        return all(var.get().strip() != "" for var in self.scoring_vars.values())

    def start_analysis(self):
        """Main analysis routine"""
        if not self.validate_inputs():
            messagebox.showwarning("Input Error", "Please fill all priority fields!")
            return

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        
        try:
            # Capture and analyze top
            self.motor_controller.move_relays([1,0,1,0])
            time.sleep(2)
            self._analyze_part("top", timestamp)
            
            # Capture and analyze bottom
            self.motor_controller.move_relays([0,1,0,1])
            time.sleep(2)
            self._analyze_part("bottom", timestamp)
            
            # Calculate final grade
            self._calculate_final_grade()
            
        except Exception as e:
            messagebox.showerror("Error", f"Analysis failed: {str(e)}")
        finally:
            self.motor_controller.stop_motors()

    def _analyze_part(self, part, timestamp):
        """Analyze a single part (top/bottom) of the fruit"""
        # Capture image
        img = self.camera_system.capture_image()
        img_path = f"{timestamp}_{part}.png"
        img.save(img_path)
        
        # Classify
        ripeness = self.analyzer.classify_image(img, 'ripeness')
        bruises = self.analyzer.classify_image(img, 'bruises')
        
        # Calculate size
        width, length = self.analyzer.calculate_dimensions(img_path, f"{timestamp}_background.png")
        size = self._determine_size(width, length)
        
        # Update UI
        self._update_part_display(part, ripeness, bruises, width, length, img)
        
        # Calculate score
        score = self._calculate_part_score(ripeness, bruises, size)
        getattr(self, f"{part}_score").configure(text=f"{part.capitalize()} Score: {score:.2f}")

    def _update_part_display(self, part, ripeness, bruises, width, length, img):
        """Update GUI with analysis results"""
        canvas = getattr(self, f"{part}_canvas")
        result_label = getattr(self, f"{part}_result")
        
        photo = ImageTk.PhotoImage(img.resize((300, 200)))
        canvas.create_image(0, 0, anchor=tk.NW, image=photo)
        canvas.image = photo
        
        result_text = f"Ripeness: {ripeness}\nBruises: {bruises}\nSize: {width:.1f}cm x {length:.1f}cm"
        result_label.configure(text=result_text)

    def _calculate_part_score(self, ripeness, bruises, size):
        """Calculate score for a single part"""
        weights = {k: float(v.get()) for k, v in self.scoring_vars.items()}
        return (
            SCORING['ripeness'][ripeness] * weights['ripeness'] +
            SCORING['bruises'][bruises] * weights['bruises'] +
            SCORING['size'][size] * weights['size']
        )

    def _determine_size(self, width, length):
        """Determine size category based on dimensions"""
        area = width * length
        if area < SIZE_CALCULATION['size_thresholds']['small']:
            return 'small'
        elif area < SIZE_CALCULATION['size_thresholds']['medium']:
            return 'medium'
        return 'large'

    def _calculate_final_grade(self):
        """Determine final grade and move stepper"""
        top_score = float(self.top_score.cget("text").split(": ")[1])
        bottom_score = float(self.bottom_score.cget("text").split(": ")[1])
        avg_score = (top_score + bottom_score) / 2
        
        if avg_score >= 7:
            self.grade.configure(text="Grade: A")
            self.motor_controller.move_stepper(STEPPER_PARAMS['positions'][0])
        elif avg_score >= 4:
            self.grade.configure(text="Grade: B")
            self.motor_controller.move_stepper(STEPPER_PARAMS['positions'][1])
        else:
            self.grade.configure(text="Grade: C")
            self.motor_controller.move_stepper(STEPPER_PARAMS['positions'][2])

    def update_video_feed(self):
        """Update live video feed"""
        if self._running:
            frame = self.camera_system.get_video_frame().resize((300, 200))
            photo = ImageTk.PhotoImage(frame)
            self.video_canvas.create_image(0, 0, image=photo, anchor=tk.NW)
            self.video_canvas.image = photo
            self.after(10, self.update_video_feed)

    def show_help(self):
        """Display help information"""
        help_text = """Mango Grading System Help:\n
        1. Set priority weights (0-3) for each category\n
        2. Click Start to begin analysis\n
        3. View results in left panel\n
        4. Use Reset to restart\n
        5. Click Stop to exit"""
        messagebox.showinfo("Help", help_text)

    def reset_system(self):
        """Reset the application"""
        self.motor_controller.cleanup()
        self.destroy()
        os.execv(sys.executable, [sys.executable] + sys.argv)

    def stop_program(self):
        """Cleanup and exit"""
        self._running = False
        self.motor_controller.cleanup()
        self.camera_system.stop()
        self.destroy()
        sys.exit(0)

if __name__ == "__main__":
    try:
        app = MangoGraderGUI()
        app.mainloop()
    except KeyboardInterrupt:
        GPIO.cleanup()
        sys.exit(0)