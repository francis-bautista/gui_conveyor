import cv2, imutils, json
import numpy as np
from imutils import perspective
from scipy.spatial import distance as dist

def load_json_file(filepath, default_data=None):
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: '{filepath}' not found.")
    except json.JSONDecodeError as e:
        print(f"Error decoding '{filepath}': {e}")
    return default_data if default_data is not None else {}

def calculate_real_world_dimension(pixel_dimension, distance_camera_to_object, focal_length_pixels):
    return (pixel_dimension * distance_camera_to_object) / focal_length_pixels

def calculate_size(img, top):
    fg = img['m']
    bg = img['g']
    formatted_date_time = img['f_dt']
    FOCAL_LENGTH_PIXELS = 3500
    DISTANCE_CAMERA_TO_OBJECT = 40
    try:
        # Determine the suffix based on the `top` parameter
        suffix = "top" if top else "bottom"
        foreground = cv2.imread(fg)
        background = cv2.imread(bg)
        if foreground is None or background is None:
            print(f"Error: Unable to read image files. Foreground: {fg}, Background: {bg}")
            return 0, 0
            
        # Generate foreground mask using absolute difference
        fgMask = cv2.absdiff(foreground, background)
        fgMask_filename = f"{formatted_date_time}_fgMask_{suffix}.png"
        cv2.imwrite(fgMask_filename, fgMask)
        # print(f"Foreground mask saved as {fgMask_filename}")
        
        # Fix the syntax errors in the thresholding line
        _, thresh = cv2.threshold(cv2.cvtColor(fgMask, cv2.COLOR_BGR2GRAY), 50, 255, cv2.THRESH_BINARY)
        thresh_filename = f"{formatted_date_time}_thresh_{suffix}.png"
        cv2.imwrite(thresh_filename, thresh)
        # print(f"Threshold saved as {thresh_filename}")
        
        # Process the threshold image
        image = cv2.imread(thresh_filename)
        if image is None:
            print(f"Error: Unable to read threshold image {thresh_filename}")
            return 0, 0
            
        # Image processing steps
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (7, 7), 0)
        edged = cv2.Canny(gray, 50, 100)
        edged = cv2.dilate(edged, None, iterations=1)
        edged = cv2.erode(edged, None, iterations=1)
        
        # Find all contours
        cnts = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)
        
        # If no contours found, return zero dimensions
        if not cnts:
            return 0, 0
            
        # Find the largest contour by area
        largest_contour = max(cnts, key=cv2.contourArea)
        
        # Only process if the contour area is significant enough
        if cv2.contourArea(largest_contour) < 100:
            return 0, 0
            
        # Process the largest contour
        box = cv2.minAreaRect(largest_contour)
        box = cv2.boxPoints(box)
        box = np.array(box, dtype="int")
        box = imutils.perspective.order_points(box)
        (tl, tr, br, bl) = box
        
        pixel_width = dist.euclidean(tl, tr)
        pixel_length = dist.euclidean(tr, br)
        real_width = calculate_real_world_dimension(pixel_width, DISTANCE_CAMERA_TO_OBJECT, FOCAL_LENGTH_PIXELS)
        real_length = calculate_real_world_dimension(pixel_length, DISTANCE_CAMERA_TO_OBJECT, FOCAL_LENGTH_PIXELS)
        
        return real_width, real_length
        
    except Exception as e:
        print(f"Error in calculate_size: {e}")
        return 0, 0
    
def determine_size(length, width):
    area = { 'min_x': 11.5,
            'min_y': 7.0,
            'max_x': 12.5,
            'max_y': 8.5,
    }
    minArea = float(area['min_x'] * area['min_y'])
    maxArea = float(area['max_x'] * area['max_y'])
    area = float(length * width)
    if area < minArea:
        return 'small'
    elif minArea <= area < maxArea:
        return 'medium'
    else:
        return 'large'
    
def midpoint(ptA, ptB):
    return ((ptA[0] + ptB[0]) * 0.5, (ptA[1] + ptB[1]) * 0.5)
