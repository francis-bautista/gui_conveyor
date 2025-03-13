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

# Define the GPIO pins connected to the relays
relay1 = 6   # Motor 1 Forward
relay2 = 13   # Motor 1 Reverse
relay3 = 19  # Motor 2 Forward
relay4 = 26  # Motor 2 Reverse
delay_time = 2  # 2 seconds delay between direction changes

# Set up the GPIO mode
GPIO.setmode(GPIO.BCM)  # Use Broadcom pin numbering
GPIO.setup(relay1, GPIO.OUT)
GPIO.setup(relay2, GPIO.OUT)
GPIO.setup(relay3, GPIO.OUT)
GPIO.setup(relay4, GPIO.OUT)

# Initialize relays to OFF state
GPIO.output(relay1, GPIO.LOW)
GPIO.output(relay2, GPIO.LOW)
GPIO.output(relay3, GPIO.LOW)
GPIO.output(relay4, GPIO.LOW)

def clockwiseM2(delay):
	GPIO.output(relay1, GPIO.HIGH)  # Motor 1 Forward
	GPIO.output(relay2, GPIO.LOW)   # Motor 1 Reverse OFF
	time.sleep(delay)
	GPIO.output(relay1, GPIO.LOW)
	GPIO.output(relay2, GPIO.LOW)

def clockwiseM1(delay):
	GPIO.output(relay3, GPIO.HIGH)  # Motor 2 Forward
	GPIO.output(relay4, GPIO.LOW)   # Motor 2 Reverse OFF
	time.sleep(delay)
	GPIO.output(relay3, GPIO.LOW)
	GPIO.output(relay4, GPIO.LOW)

def counterclockwiseM2(delay):
	GPIO.output(relay1, GPIO.LOW)  # Motor 1 Forward OFF
	GPIO.output(relay2, GPIO.HIGH)   # Motor 1 Reverse 
	time.sleep(delay)
	GPIO.output(relay1, GPIO.LOW)
	GPIO.output(relay2, GPIO.LOW)

def counterclockwiseM1(delay):
	GPIO.output(relay3, GPIO.LOW)  # Motor 2 Forward OFF
	GPIO.output(relay4, GPIO.HIGH)   # Motor 2 Reverse 
	time.sleep(delay)
	GPIO.output(relay3, GPIO.LOW)
	GPIO.output(relay4, GPIO.LOW)

def topSideCapture(delay):
    GPIO.output(relay3, GPIO.HIGH)  # Motor 2 Forward
    GPIO.output(relay4, GPIO.LOW)   # Motor 2 Reverse OFF
    GPIO.output(relay1, GPIO.HIGH)  # Motor 1 Forward
    GPIO.output(relay2, GPIO.LOW)   # Motor 1 Reverse OFF
    time.sleep(delay)
    GPIO.output(relay1, GPIO.LOW)
    GPIO.output(relay2, GPIO.LOW)
    GPIO.output(relay3, GPIO.LOW)
    GPIO.output(relay4, GPIO.LOW)
    
def bottomSideCapture(delay):
    GPIO.output(relay3, GPIO.LOW)  # Motor 2 Forward
    GPIO.output(relay4, GPIO.HIGH)   # Motor 2 Reverse OFF
    GPIO.output(relay1, GPIO.HIGH)  # Motor 1 Forward
    GPIO.output(relay2, GPIO.LOW)   # Motor 1 Reverse OFF
    time.sleep(delay)
    GPIO.output(relay1, GPIO.LOW)
    GPIO.output(relay2, GPIO.LOW)
    GPIO.output(relay3, GPIO.LOW)
    GPIO.output(relay4, GPIO.LOW)
    
def exitAndEnterMango(delay):
    GPIO.output(relay3, GPIO.HIGH)  # Motor 2 Forward
    GPIO.output(relay4, GPIO.LOW)   # Motor 2 Reverse OFF
    GPIO.output(relay1, GPIO.LOW)  # Motor 1 Forward
    GPIO.output(relay2, GPIO.HIGH)   # Motor 1 Reverse OFF
    time.sleep(delay)
    GPIO.output(relay1, GPIO.LOW)
    GPIO.output(relay2, GPIO.LOW)
    GPIO.output(relay3, GPIO.LOW)
    GPIO.output(relay4, GPIO.LOW)

# Define classification mapping
class_labels_ripeness = ['green', 'yellow_green', 'yellow']
class_labels_bruises = ['bruised', 'unbruised']
class_labels_size = ['small', 'medium', 'large']
ripeness_scores = {'yellow': 1.0, 'yellow_green': 2.0, 'green': 3.0}
bruiseness_scores = {'bruised': 1.5, 'unbruised': 3.0}
size_scores = {'small': 1.0, 'medium': 2.0, 'large': 3.0}
scores_dict = {}

# Load the models
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Ripeness model
model_ripeness = EfficientNet.from_pretrained('efficientnet-b0', num_classes=len(class_labels_ripeness))
model_ripeness.load_state_dict(torch.load("ripeness.pth", map_location=device))
model_ripeness.eval()
model_ripeness.to(device)

# Bruises model
model_bruises = EfficientNet.from_pretrained('efficientnet-b0', num_classes=len(class_labels_bruises))
model_bruises.load_state_dict(torch.load("bruises.pth", map_location=device))
model_bruises.eval()
model_bruises.to(device)

# Define transformations
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

# Size calculation parameters
FOCAL_LENGTH_PIXELS = 2710  # Example value, replace with your camera's focal length
DISTANCE_CAMERA_TO_OBJECT = 40  # cm

def midpoint(ptA, ptB):
    """
    Calculate the midpoint of two points.
    :param ptA: First point.
    :param ptB: Second point.
    :return: Midpoint of the two points.
    """
    return ((ptA[0] + ptB[0]) * 0.5, (ptA[1] + ptB[1]) * 0.5)

def calculate_real_world_dimension(pixel_dimension, distance_camera_to_object, focal_length_pixels):
    """
    Calculate the real-world dimension of an object.
    :param pixel_dimension: Dimension of the object in pixels (width or length).
    :param distance_camera_to_object: Distance from the camera to the object in cm.
    :param focal_length_pixels: Focal length of the camera in pixels.
    :return: Real world dimension in cm.
    """
    return (2 * pixel_dimension * distance_camera_to_object) / focal_length_pixels

def calculate_size(fg, bg, formatted_date_time, top):
    """
    Calculate the real-world width and length of an object in an image.
    :param fg: Path to the foreground image file.
    :param bg: Path to the background image file.
    :param formatted_date_time: Formatted date and time string for saving intermediate images.
    :param top: Boolean indicating whether the image is the top part (True) or bottom part (False).
    :return: Real-world width and length in cm.
    """ 
    try:
        # Determine the suffix based on the `top` parameter
        suffix = "top" if top else "bottom"

        foreground = cv2.imread(fg)
        background = cv2.imread(bg)
        if foreground is None or background is None:
            print(f"Error: Unable to read image files. Foreground: {fg}, Background: {bg}")
            return 0, 0

        fgMask = cv2.absdiff(foreground, background)
        fgMask_filename = f"{formatted_date_time}_fgMask_{suffix}.png"
        cv2.imwrite(fgMask_filename, fgMask)
        print(f"Foreground mask saved as {fgMask_filename}")

        _, thresh = cv2.threshold(cv2.cvtColor(fgMask, cv2.COLOR_BGR2GRAY), 50, 255, cv2.THRESH_BINARY)
        thresh_filename = f"{formatted_date_time}_thresh_{suffix}.png"
        cv2.imwrite(thresh_filename, thresh)
        print(f"Threshold saved as {thresh_filename}")

        image = cv2.imread(thresh_filename)
        if image is None:
            print(f"Error: Unable to read threshold image {thresh_filename}")
            return 0, 0

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (7, 7), 0)
        edged = cv2.Canny(gray, 50, 100)
        edged = cv2.dilate(edged, None, iterations=1)
        edged = cv2.erode(edged, None, iterations=1)
        cnts = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)
        (cnts, _) = imutils.contours.sort_contours(cnts)

        for c in cnts:
            if cv2.contourArea(c) < 100:
                continue
            box = cv2.minAreaRect(c)
            box = cv2.boxPoints(box)
            box = np.array(box, dtype="int")
            box = imutils.perspective.order_points(box)
            (tl, tr, br, bl) = box
            pixel_width = dist.euclidean(tl, tr)
            pixel_length = dist.euclidean(tr, br)
            real_width = calculate_real_world_dimension(pixel_width, DISTANCE_CAMERA_TO_OBJECT, FOCAL_LENGTH_PIXELS)
            real_length = calculate_real_world_dimension(pixel_length, DISTANCE_CAMERA_TO_OBJECT, FOCAL_LENGTH_PIXELS)
            return real_width, real_length
        return 0, 0
    except Exception as e:
        print(f"Error in calculate_size: {e}")
        return 0, 0
    
def classify_image(image, model, class_labels):
    """Classifies a given image and returns the predicted class."""
    image = transform(image).unsqueeze(0).to(device)
    output = model(image)
    _, predicted = torch.max(output, 1)
    return class_labels[predicted.item()]

def capture_image(picam2):
    """Captures an image using the Raspberry Pi Camera and converts it to RGB."""
    t=1
    for x in range(t):
        print(f"Capturing image in {t-x} seconds...")
        time.sleep(1)
    image = picam2.capture_array()
    image = Image.fromarray(image).convert("RGB")
    return image


def calculate_total_score(ripeness_scores, bruiseness_scores, size_scores, r, b, s, top=True):

    ripeness_user_input = float(ripeness_combo.get())
    bruiseness_user_input = float(bruises_combo.get())
    size_user_input = float(size_combo.get())
    if top:
        print("\nTop")
    else:
        print("\nBottom")
    print(f"Ripeness Score: {ripeness_scores}")
    print(f"Bruises Score: {bruiseness_scores}")
    print(f"Size Score: {size_scores}")
    print(f"Ripeness User Input: {ripeness_user_input}")
    print(f"Bruises User Input: {bruiseness_user_input}")   
    print(f"Size User Input: {size_user_input}")
    # Calculate total score
    total_score = float(ripeness_scores * ripeness_user_input + bruiseness_scores * bruiseness_user_input + size_scores * size_user_input)
    # Display the total score
    if top:
        top_score.configure(text=f"Top Score: {total_score}")
        scores_dict["top"] = {total_score}
    else:
        bottom_score.configure(text=f"Bottom Score: {total_score}")
        scores_dict["bottom"] = {total_score}
        

def validate_inputs():
    """Validates the user inputs for ripeness, bruiseness, and size."""
    ripeness_value = ripeness_combo.get()
    bruises_value = bruises_combo.get()
    size_value = size_combo.get()

    print(f"Ripeness: '{ripeness_value}', Bruises: '{bruises_value}', Size: '{size_value}'")  # Debugging

    # Check if any of the combo boxes are empty
    if ripeness_value.strip() == "" or bruises_value.strip() == "" or size_value.strip() == "":
        messagebox.showwarning("Input Error", "Please fill in all the fields (Ripeness, Bruises, and Size).")
        return False
    return True

def final_grade(r,b,s):
    r_priority = float(ripeness_combo.get())
    b_priority = float(bruises_combo.get())
    s_priority = float(size_combo.get())
    resulting_grade = r_priority*ripeness_scores[r] + b_priority*bruiseness_scores[b] + s_priority*size_scores[s]
    print(f"Resulting Grade: {resulting_grade}")
    return resulting_grade

def find_grade(input_grade):
    r_priority = float(ripeness_combo.get())
    b_priority = float(bruises_combo.get())
    s_priority = float(size_combo.get())
    max_gradeA = r_priority*ripeness_scores['green'] + b_priority*bruiseness_scores['unbruised'] + s_priority*size_scores['large']
    min_gradeA = r_priority*ripeness_scores['yellow_green'] + b_priority*bruiseness_scores['bruised'] + s_priority*size_scores['small']
    difference = max_gradeA - min_gradeA
    print("Calculated Grade Range")
    print(f"Max Grade A: {max_gradeA}, Min Grade A: {min_gradeA}, Difference: {difference}")
    print(f"Max Grade B: {min_gradeA}, Min Grade B: {min_gradeA - difference}, Difference: {min_gradeA - (min_gradeA - difference)}")
    max_gradeC = min_gradeA - (min_gradeA - difference)
    print(f"Max Grade C: {max_gradeC}, Min Grade C: {max_gradeC - difference}, Difference: {max_gradeC - (min_gradeA - (max_gradeC - difference))}")
    
    if (input_grade >= min_gradeA) and (input_grade <= max_gradeA):
        grade_score.configure(text=f"Grade - A")
    elif (input_grade >= min_gradeA - difference) and (input_grade < min_gradeA):
        grade_score.configure(text=f"Grade - B")
    else:
        grade_score.configure(text=f"Grade - C")
    
def update_gui():
    """
    Updates the GUI by capturing images of the top and bottom parts of the fruit, classifying their ripeness and bruiseness, 
    calculating the size, and displaying the results. It also computes the total scores for ripeness, bruiseness, and size 
    based on user inputs and displays them on the GUI.
    
    The function performs the following steps:
    1. Validates user inputs before proceeding.
    2. Captures and saves images of the top and bottom parts of the fruit, along with background images.
    3. Classifies the images to determine ripeness and bruiseness.
    4. Calculates the size of the fruit using the captured images.
    5. Displays the classification results and sizes on the GUI.
    6. Waits for 10 seconds between capturing the top and bottom parts.
    7. Computes and displays the total scores for ripeness, bruiseness, and size based on user-defined weights.
    """
    # update_video_feed()
    if not validate_inputs():
        return  # Stop execution if validation fails
    """Updates the GUI with the captured images, classification results, and size."""
    global top_image, bottom_image, picam2, top_background, bottom_background
    # Get the current date and time
    now = datetime.now()
    # Format the date and time as a string (e.g., "2023-10-05_14-30-45")
    formatted_date_time = now.strftime("%Y-%m-%d_%H-%M-%S")
    
    print("\nCapturing Background")
    top_background = capture_image(picam2)
    top_background.save(f"{formatted_date_time}_background.png")  # Save the top image for size calculation
    # Capture top part
    # clockwiseM1(1)
    # clockwiseM2(1)
    topSideCapture(15)
    print("\nCapturing Top Part")
    top_label.configure(text="Capturing top part of the mango...")
    top_image = capture_image(picam2)
    top_image.save(f"{formatted_date_time}_top.png")  # Save the top image for size calculation
    top_class_ripeness = classify_image(top_image, model_ripeness, class_labels_ripeness)
    top_class_bruises = classify_image(top_image, model_bruises, class_labels_bruises)
    top_width, top_length = calculate_size(f"{formatted_date_time}_top.png",f"{formatted_date_time}_background.png",formatted_date_time,top=True)
    top_result_label.configure(text=f"Ripeness: {top_class_ripeness}\nBruises: {top_class_bruises}\nSize: {top_width:.2f} cm (W) x {top_length:.2f} cm (L)")
    top_photo = ImageTk.PhotoImage(top_image.resize((300, 200)))
    top_canvas.create_image(0, 0, anchor=tk.NW, image=top_photo)
    top_canvas.image = top_photo
    bottomSideCapture(10)
    # update_video_feed()
    
    # Capture bottom part
    print("\nCapturing Bottom Part")
    bottom_label.configure(text="Capturing bottom part of the mango...")
    bottom_image = capture_image(picam2)
    bottom_image.save(f"{formatted_date_time}_bottom.png")  # Save the bottom image for size calculation
    bottom_class_ripeness = classify_image(bottom_image, model_ripeness, class_labels_ripeness)
    bottom_class_bruises = classify_image(bottom_image, model_bruises, class_labels_bruises)
    bottom_width, bottom_length = calculate_size(f"{formatted_date_time}_bottom.png",f"{formatted_date_time}_background.png",formatted_date_time,top=False)
    bottom_result_label.configure(text=f"Ripeness: {bottom_class_ripeness}\nBruises: {bottom_class_bruises}\nSize: {bottom_width:.2f} cm (W) x {bottom_length:.2f} cm (L)")
    bottom_photo = ImageTk.PhotoImage(bottom_image.resize((300, 200)))
    bottom_canvas.create_image(0, 0, anchor=tk.NW, image=bottom_photo)
    bottom_canvas.image = bottom_photo

    print("\nComputing Score")
    top_size_class = determine_size(top_width, top_length)
    print(f"Top Size = {top_size_class}")
    calculate_total_score(ripeness_scores[top_class_ripeness], bruiseness_scores[top_class_bruises], size_scores[top_size_class], r=top_class_ripeness, b=top_class_bruises, s=top_size_class, top=True)
    bottom_size_class = determine_size(bottom_width, bottom_length)
    print(f"Bottom Size = {bottom_size_class}")
    calculate_total_score(ripeness_scores[bottom_class_ripeness], bruiseness_scores[bottom_class_bruises], size_scores[bottom_size_class], r=bottom_class_ripeness, b=bottom_class_bruises, s=bottom_size_class, top=False)
    
    print("\nComputing Grade")
    top_final_grade = final_grade(top_class_ripeness, top_class_bruises, top_size_class)
    bottom_final_grade = final_grade(bottom_class_ripeness, bottom_class_bruises, bottom_size_class)
    average_final_grade = (top_final_grade + bottom_final_grade) / 2
    print(f"Average Final Score: {average_final_grade}")
    find_grade(average_final_grade)
    exitAndEnterMango(10)
    print("\nDone")
    
    
def determine_size(length, width):
    """Determines the size of the mango based on its length and width.
    
    :param length: The length of the mango in cm
    :param width: The width of the mango in cm
    :return: A string indicating the size of the mango: 'small', 'medium', or 'large'
    """
    area = float(length * width)  # Calculate area (you can use any metric you prefer)
    if area < 50:  # Example thresholds
        return 'small'
    elif 50 <= area < 100:
        return 'medium'
    else:
        return 'large'
    
def update_video_feed():
    """Updates the video feed on the Tkinter canvas."""
    global picam2, video_canvas
    
    # Capture frame from the camera
    frame = picam2.capture_array()
    frame = Image.fromarray(frame).convert("RGB")  # Convert RGBA to RGB
    
    # Resize and convert to PhotoImage
    frame = frame.resize((300, 200))
    frame = ImageTk.PhotoImage(frame)
    
    # Update the video canvas with the new frame
    video_canvas.create_image(0, 0, anchor=tk.NW, image=frame)
    video_canvas.image = frame
    
    # Schedule the next update
    root.after(10, update_video_feed)

def stop_now():
	GPIO.cleanup()  # Reset GPIO settings
	os.execv(sys.executable, [sys.executable] + sys.argv)
def exit_program():
    print("Exiting the program. Goodbye!")
    GPIO.cleanup()  # Reset GPIO settings
    sys.exit(0)  # 0 indicates a successful termination
def show_help():
    """Opens a new window to display help information."""
    help_window = tk.Toplevel(root)
    help_window.title("Help")
    help_window.geometry("800x700")  # Set the size of the help window

    # Add help content
    help_text = """
    Mango Quality Assessment Application

    Instructions:
    1. Click 'Start' to capture and analyze the top and bottom parts of the mango.
    2. Adjust the priority scores for Ripeness, Bruises, and Size using the dropdown menus.
    3. View the results in the left panel, including ripeness, bruises, size, and total score.
    4. Use the 'Reset' button to restart the analysis.
    5. Click 'Export' to save the results (not implemented yet).
    6. Click 'Stop' to exit the application.

    """
    help_label = tk.Label(help_window, text=help_text, justify=tk.LEFT, padx=10, pady=10)
    help_label.pack()
def checkbox_event():
    if check_var.get() == "on":  # Check for "on" instead of 1
        ripeness_combo.set("")  # Clears selection
        bruises_combo.set("")  # Clears selection
        size_combo.set("")  # Clears selection
    else:
        ripeness_combo.set("3.0")  # Default value
        bruises_combo.set("3.0")  # Default value
        size_combo.set("3.0")  # Default value

    print("checkbox toggled, current value:", check_var.get())
    print("ripeness value:", ripeness_combo.get())
    print("bruises value:", bruises_combo.get())
    print("size value:", size_combo.get())

    


# Initialize the camera
picam2 = Picamera2()
camera_config = picam2.create_video_configuration(main={"size": (1920, 1080)})
picam2.configure(camera_config)
picam2.start()
# 
# Create the main GUI window
root = ctk.CTk(fg_color="#e5e0d8")
root.title("Carabao Mango Grader and Sorter")

# Configure grid layout
root.grid_columnconfigure(0, weight=1)  # Left column (analysis results)
root.grid_columnconfigure(1, weight=1)  # Right column (video feed and combo boxes)
root.grid_rowconfigure(0, weight=1)

# Left Side: Analysis Results
left_frame = ctk.CTkFrame(root, fg_color="#B3B792")
left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

# Top part UI
top_label = ctk.CTkLabel(left_frame, text="Top Image")
top_label.grid(row=0, column=0, padx=10, pady=10, sticky="nswe")
top_canvas = tk.Canvas(left_frame, width=300, height=200)
top_canvas.grid(row=1, column=0, padx=10, pady=10, sticky="nswe")
top_result_label = ctk.CTkLabel(left_frame, text="Ripeness: -\nBruises: - \nSize - ")
top_result_label.grid(row=2, column=0, sticky="nswe")


# Bottom part UI
bottom_label = ctk.CTkLabel(left_frame, text="Bottom Image")
bottom_label.grid(row=3, column=0)
bottom_canvas = tk.Canvas(left_frame, width=300, height=200)
bottom_canvas.grid(row=4, column=0)
bottom_result_label = ctk.CTkLabel(left_frame, text="Ripeness: -\nBruises: - \nSize - ")
bottom_result_label.grid(row=5, column=0)

# Right Side: Video Feed and Combo Boxes
right_frame = ctk.CTkFrame(root, fg_color="#B3B792")
right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

# Start Button
start_button = ctk.CTkButton(right_frame, text="Start",
                             fg_color="#8AD879",command=update_gui)
# start_button = tk.Button(right_frame, text="Start", command=update_gui)
start_button.grid(row=0, column=0, padx=10, pady=10, sticky="ns")

end_button = ctk.CTkButton(right_frame, text="Stop", fg_color="#F3533A",
                           command=exit_program)
# end_button = tk.Button(right_frame, text="Stop", command=exit_program)
end_button.grid(row=0, column=1, padx=10, pady=10, sticky="ns")

# Stop Button
stop_button = ctk.CTkButton(right_frame, text="Reset", fg_color="#5CACF9",
                            command=stop_now)
# stop_button = tk.Button(right_frame, text="Reset", command=stop_now)
stop_button.grid(row=1, column=0, padx=10, pady=10, sticky="ns")

# Help Button
help_button = ctk.CTkButton(right_frame, text="Help", fg_color="#f85cf9",
                            command=show_help)
# help_button = tk.Button(right_frame, text="Help", command=show_help)
help_button.grid(row=1, column=1, padx=10, pady=10, sticky="ns")  # Place it below the combo boxes

# Export Button 
export_button = ctk.CTkButton(right_frame, text="Export", fg_color="#a95cf9",
                              command=exit_program)
# export_button = tk.Button(right_frame, text="Export", command=exit_program)
export_button.grid(row=2, column=0, padx=10, pady=10, sticky="ns")

# Toggle Button
check_var = ctk.StringVar(value="off")
checkbox = ctk.CTkCheckBox(right_frame, text="Default", command=checkbox_event,
                                     variable=check_var, onvalue="on", offvalue="off")
checkbox.grid(row=2, column=1, padx=10, pady=10, sticky="ns")

# Video Feed
video_label = ctk.CTkLabel(right_frame, text="Live Video Feed")
video_label.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="ns")
video_canvas = tk.Canvas(right_frame, width=300, height=200)
video_canvas.grid(row=4, column=0, columnspan=2, padx=10,pady=10, sticky="ns")

# Score
top_score = ctk.CTkLabel(right_frame, text="Top Score - ")
top_score.grid(row=5, column=0)
bottom_score = ctk.CTkLabel(right_frame, text="Bottom Score - ")
bottom_score.grid(row=6, column=0)
grade_score = ctk.CTkLabel(right_frame, text="Grade - ")
grade_score.grid(row=7, column=0)

#frame
frame_choices = ctk.CTkFrame(right_frame,fg_color="#809671")
frame_choices.grid(row=8, column=0, padx=10, pady=10, columnspan=2, sticky="nswe")
frame_choices.columnconfigure(0,weight=2)
# User Priority
priority_label = ctk.CTkLabel(frame_choices, text="User Priority")
priority_label.grid(row=0,column=0, padx=10, pady=10, columnspan=2, sticky="nswe")
#priority_label.grid(row=8, column=0)
# Combo Boxes
ripeness_label = ctk.CTkLabel(frame_choices, text="Ripeness Score (0-3):")
ripeness_label.grid(row=1, column=0, padx=10, pady=10, columnspan=2, sticky="nswe")
ripeness_combo = ttk.Combobox(frame_choices, values=[0.0, 1.0, 2.0, 3.0])
ripeness_combo.grid(row=2, column=0)

bruises_label = ctk.CTkLabel(frame_choices, text="Bruises Score (0-3):")
bruises_label.grid(row=3, column=0, padx=10, pady=10, columnspan=2, sticky="nswe")
bruises_combo = ttk.Combobox(frame_choices, values=[0.0, 1.0, 2.0, 3.0])
bruises_combo.grid(row=4, column=0)

size_label = ctk.CTkLabel(frame_choices, text="Size Score (0-3):")
size_label.grid(row=5, column=0, padx=10, pady=10, columnspan=2, sticky="nswe")
size_combo = ttk.Combobox(frame_choices, values=[0.0, 1.0, 2.0, 3.0])
size_combo.grid(row=6, column=0, padx=10, pady=(0,20))

# Start the video feed
update_video_feed()

# Run the GUI
root.mainloop()

# Stop the camera when the GUI is closed
picam2.stop()
