import torch
import torchvision.transforms as transforms
from efficientnet_pytorch import EfficientNet
from PIL import Image, ImageTk
import time
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



# Define classification mapping
class_labels_ripeness = ['green', 'yellow_green', 'yellow']
class_labels_bruises = ['bruised', 'unbruised']
ripeness_scores = {'yellow': 1, 'yellow_green': 2, 'green': 3}
bruiseness_scores = {'bruised': 1, 'unbruised': 2}
size_scores = {'small': 1, 'medium': 2, 'large': 3}

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
    return ((ptA[0] + ptB[0]) * 0.5, (ptA[1] + ptB[1]) * 0.5)

def calculate_real_world_dimension(pixel_dimension, distance_camera_to_object, focal_length_pixels):
    """
    Calculate the real-world dimension of an object.
    :param pixel_dimension: Dimension of the object in pixels (width or length).
    :param distance_camera_to_object: Distance from the camera to the object in cm.
    :param focal_length_pixels: Focal length of the camera in pixels.
    :return: Real-world dimension in cm.
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
    for x in range(5):
        print(f"Capturing image in {5-x} seconds...")
        time.sleep(1)
    image = picam2.capture_array()
    image = Image.fromarray(image).convert("RGB")
    return image

def update_gui():
    """Updates the GUI with the captured images, classification results, and size."""
    global top_image, bottom_image, picam2, top_background, bottom_background
    # Get the current date and time
    now = datetime.now()
    # Format the date and time as a string (e.g., "2023-10-05_14-30-45")
    # You can customize the format as needed
    formatted_date_time = now.strftime("%Y-%m-%d_%H-%M-%S")
    
    print("\nCapturing Top Background")
    top_background = capture_image(picam2)
    top_background.save(f"{formatted_date_time}_top_background.png")  # Save the top image for size calculation
    # Capture top part
    print("\nCapturing Top Part")
    top_label.config(text="Capturing top part of the mango...")
    top_image = capture_image(picam2)
    # filename = f"{formatted_date_time}_top.png"
    top_image.save(f"{formatted_date_time}_top.png")  # Save the top image for size calculation
    top_class_ripeness = classify_image(top_image, model_ripeness, class_labels_ripeness)
    top_class_bruises = classify_image(top_image, model_bruises, class_labels_bruises)
    top_width, top_length = calculate_size(f"{formatted_date_time}_top.png",f"{formatted_date_time}_top_background.png",formatted_date_time,top=True)
    top_result_label.config(text=f"Ripeness: {top_class_ripeness}\nBruises: {top_class_bruises}\nSize: {top_width:.2f} cm (W) x {top_length:.2f} cm (L)")
    top_photo = ImageTk.PhotoImage(top_image.resize((300, 200)))
    top_canvas.create_image(0, 0, anchor=ctk.NW, image=top_photo)
    top_canvas.image = top_photo

    # Wait before capturing the bottom
    print("\nWaiting for 10 seconds before capturing the bottom part...")
    time.sleep(10)

    print("\nCapturing Bottom Background")
    bottom_background = capture_image(picam2)
    bottom_background.save(f"{formatted_date_time}_bottom_background.png")  # Save the top image for size calculation
    # Capture bottom part
    print("\nCapturing Bottom Part")
    bottom_label.config(text="Capturing bottom part of the mango...")
    bottom_image = capture_image(picam2)
    bottom_image.save(f"{formatted_date_time}_bottom.png")  # Save the bottom image for size calculation
    bottom_class_ripeness = classify_image(bottom_image, model_ripeness, class_labels_ripeness)
    bottom_class_bruises = classify_image(bottom_image, model_bruises, class_labels_bruises)
    bottom_width, bottom_length = calculate_size(f"{formatted_date_time}_bottom.png",f"{formatted_date_time}_bottom_background.png",formatted_date_time,top=False)
    bottom_result_label.config(text=f"Ripeness: {bottom_class_ripeness}\nBruises: {bottom_class_bruises}\nSize: {bottom_width:.2f} cm (W) x {bottom_length:.2f} cm (L)")
    bottom_photo = ImageTk.PhotoImage(bottom_image.resize((300, 200)))
    bottom_canvas.create_image(0, 0, anchor=ctk.NW, image=bottom_photo)
    bottom_canvas.image = bottom_photo

    # Compute final scores
    print("\nComputing")
    ripeness_score = (ripeness_scores[top_class_ripeness] + ripeness_scores[bottom_class_ripeness]) / 2
    bruiseness_score = (bruiseness_scores[top_class_bruises] + bruiseness_scores[bottom_class_bruises]) / 2
    final_score_label.config(text=f"Final Ripeness Score: {ripeness_score:.1f}\nFinal Bruiseness Score: {bruiseness_score:.1f}")
    print("\nDone!")
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
    video_canvas.create_image(0, 0, anchor=ctk.NW, image=frame)
    video_canvas.image = frame
    
    # Schedule the next update
    root.after(10, update_video_feed)

def stop_now():
    os.execv(sys.executable, [sys.executable] + sys.argv)

# Initialize the camera
picam2 = Picamera2()
camera_config = picam2.create_video_configuration(main={"size": (1920, 1080)})
picam2.configure(camera_config)
picam2.start()

# Create the main GUI window
root = ctk.CTk()
root.title("Mango Quality Assessment")

# Configure grid layout
root.grid_columnconfigure(0, weight=1)  # Left column (analysis results)
root.grid_columnconfigure(1, weight=1)  # Right column (video feed and combo boxes)
root.grid_rowconfigure(0, weight=1)

# Left Side: Analysis Results
left_frame = ctk.CTkFrame(root)
left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

# Top part UI
top_label = ctk.CTkLabel(left_frame, text="Top Image")
top_label.grid(row=0, column=0)
top_canvas = ctk.CTkFrame(left_frame, width=300, height=200)
top_canvas.grid(row=1, column=0)
top_result_label = ctk.CTkLabel(left_frame, text="Ripeness: -\nBruises: -")
top_result_label.grid(row=2, column=0)

# Bottom part UI
bottom_label = ctk.CTkLabel(left_frame, text="Bottom Image")
bottom_label.grid(row=3, column=0)
bottom_canvas = ctk.CTkCanvas(left_frame, width=300, height=200)
bottom_canvas.grid(row=4, column=0)
bottom_result_label = ctk.CTkLabel(left_frame, text="Ripeness: -\nBruises: -")
bottom_result_label.grid(row=5, column=0)

# Final Score UI
final_score_label = ctk.CTkLabel(left_frame, text="Final Ripeness Score: -\nFinal Bruiseness Score: -")
final_score_label.grid(row=6, column=0)

# Right Side: Video Feed and Combo Boxes
right_frame = ctk.CTkFrame(root)
right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

# Start Button
start_button = ctk.CTkButton(right_frame, text="Start",
                             command=update_gui,
                             fg_color= "#8AD879")
start_button.grid(row=0, column=0)

# Stop Button
stop_button = ctk.CTkButton(right_frame, text="Reset", command=stop_now,
                            fg_color="#F3533A")
stop_button.grid(row=1, column=0)

# Export Button 
export_button = ctk.CTkButton(right_frame, text="Export", command=stop_now,
                              fg_color="#5CACF9")
export_button.grid(row=2, column=0)


# Video Feed
video_label = ctk.CTkLabel(right_frame, text="Live Video Feed")
video_label.grid(row=3, column=0)
video_canvas = ctk.CTkCanvas(right_frame, width=300, height=200)
video_canvas.grid(row=4, column=0)

# User Priority
priority_label = ctk.CTkLabel(right_frame, text="User Priority")
priority_label.grid(row=5, column=0)
# Combo Boxes
ripeness_label = ctk.CTkLabel(right_frame, text="Ripeness Score (0-3):")
ripeness_label.grid(row=6, column=0, pady=(10, 0))
ripeness_combo = ttk.Combobox(right_frame, values=[0, 1, 2, 3])
ripeness_combo.grid(row=7, column=0)

bruises_label = ctk.CTkLabel(right_frame, text="Bruises Score (0-3):")
bruises_label.grid(row=8, column=0, pady=(10, 0))
bruises_combo = ttk.Combobox(right_frame, values=[0, 1, 2, 3])
bruises_combo.grid(row=9, column=0)

size_label = ctk.CTkLabel(right_frame, text="Size Score (0-3):")
size_label.grid(row=10, column=0, pady=(10, 0))
size_combo = ttk.Combobox(right_frame, values=[0, 1, 2, 3])
size_combo.grid(row=11, column=0)

# Start the video feed
update_video_feed()

# Run the GUI
root.mainloop()

# Stop the camera when the GUI is closed
picam2.stop()
