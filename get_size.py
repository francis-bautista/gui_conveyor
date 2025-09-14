import cv2, imutils, json
import numpy as np
from imutils import perspective
from scipy.spatial import distance as dist
import os
import pandas as pd
# C:\Users\Kenan\thesis-size

def batch_analyze(self, image_folder, output_csv=None):
    all_results = []
    image_files = [f for f in os.listdir(image_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    
    for image_file in image_files:
        image_path = os.path.join(image_folder, image_file)
        print(f"Processing: {image_file}")
        
        results = self.analyze_image(image_path)
        
        for result in results:
            row = {
                'image_file': image_file,
                'mango_id': result['mango_id'],
                'class': result['class'],
                'confidence': result['confidence'],
                'length_cm': result['measurements']['length_cm'],
                'width_cm': result['measurements']['width_cm'],
                'area_cm2': result['measurements']['area_cm2'],
                'volume_cm3': result['measurements']['volume_cm3']
            }
            all_results.append(row)
    
    df = pd.DataFrame(all_results)
    
    if output_csv:
        df.to_csv(output_csv, index=False)
        print(f"Results saved to: {output_csv}")
    
    if not df.empty:
        print("\n=== MEASUREMENT SUMMARY ===")
        print(f"Total mangoes measured: {len(df)}")
        print(f"Average length: {df['length_cm'].mean():.2f} cm")
        print(f"Average width: {df['width_cm'].mean():.2f} cm")
        print(f"Average area: {df['area_cm2'].mean():.2f} cm²")
        print(f"Length range: {df['length_cm'].min():.2f} - {df['length_cm'].max():.2f} cm")
        print(f"Width range: {df['width_cm'].min():.2f} - {df['width_cm'].max():.2f} cm")
    
    return df

def calibrate_with_reference_object(self, image, reference_box, reference_size_cm):
    """
    Calibrate the measurement system using a reference object
    
    Args:
        image: Input image
        reference_box: Bounding box of reference object [x1, y1, x2, y2]
        reference_size_cm: Known size of reference object in cm
    """
    x1, y1, x2, y2 = reference_box
    
    ref_width_pixels = x2 - x1
    ref_height_pixels = y2 - y1
    
    ref_size_pixels = max(ref_width_pixels, ref_height_pixels)
    
    self.pixels_per_cm = ref_size_pixels / reference_size_cm
    self.reference_object_size_cm = reference_size_cm
    
    print(f"Calibration complete:")
    print(f"  Reference object: {reference_size_cm} cm")
    print(f"  Reference pixels: {ref_size_pixels:.1f} pixels")
    print(f"  Scale: {self.pixels_per_cm:.2f} pixels/cm")
    
    return self.pixels_per_cm

def calibrate_and_measure_single_image(img_path):
    """Example: Calibrate with reference object and measure mangoes"""

    measurement_system = MangoMeasurementSystem('mango_detection_model.pth')

    image_path = img_path
    image = cv2.imread(image_path)

    reference_box = [980, 435, 1164, 612]  # [x1, y1, x2, y2] of reference object
    reference_size_cm = 2.4  # Known size of reference object in cm

    measurement_system.calibrate_with_reference_object(image, reference_box, reference_size_cm)

    results = measurement_system.analyze_image(image_path)

    for result in results:
        print(f"\nMango {result['mango_id']} ({result['class']}):")
        print(f"  Length: {result['measurements']['length_cm']} cm")
        print(f"  Width: {result['measurements']['width_cm']} cm")
        print(f"  Area: {result['measurements']['area_cm2']} cm²")
        print(f"  Confidence: {result['confidence']}")

    measurement_system.visualize_measurements(image_path)

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

def calculate_size(img, top, dir):
    fg = img['m']
    bg = img['g']
    formatted_date_time = img['f_dt']
    FOCAL_LENGTH_PIXELS = 3500
    DISTANCE_CAMERA_TO_OBJECT = 40
    try:
        suffix = "top" if top else "bottom"
        foreground = cv2.imread(fg)
        background = cv2.imread(bg)
        if foreground is None or background is None:
            print(f"Error: Unable to read image files. Foreground: {fg}, Background: {bg}")
            return 0, 0
            
        fgMask = cv2.absdiff(foreground, background)
        fgMask_filename = f"{formatted_date_time}_fgMask_{suffix}.png"
        # cv2.imwrite(fgMask_filename, fgMask)
        cv2.imwrite(os.path.join(dir, fgMask_filename), fgMask)
        # print(f"Foreground mask saved as {fgMask_filename}")
        
        _, thresh = cv2.threshold(cv2.cvtColor(fgMask, cv2.COLOR_BGR2GRAY), 50, 255, cv2.THRESH_BINARY)
        thresh_filename = f"{formatted_date_time}_thresh_{suffix}.png"
        # cv2.imwrite(thresh_filename, thresh)        
        thresh_path = os.path.join(dir, thresh_filename)
        cv2.imwrite(thresh_path, thresh)
        # print(f"Threshold saved as {thresh_filename}")
        
        image = cv2.imread(thresh_path)
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
    area = { 'min_x': 12.5,
            'min_y': 8.5,
            'max_x': 14.5,
            'max_y': 9,
    }
    minArea = float(area['min_x'] * area['min_y'])
    maxArea = float(area['max_x'] * area['max_y'])
    area = float(length * width)
    if area < minArea: # less than 106.25 cm area
        return 'small'
    elif minArea <= area < maxArea: # between  106.25 and 130.5 cm area
        return 'medium'
    else: # greater than 130.5 cm
        return 'large'
    
def midpoint(ptA, ptB):
    return ((ptA[0] + ptB[0]) * 0.5, (ptA[1] + ptB[1]) * 0.5)
