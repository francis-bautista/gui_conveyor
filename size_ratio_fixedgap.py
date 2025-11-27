import cv2
import numpy as np
import matplotlib.pyplot as plt

def calculate_mango_area(image_path, gap_w_cm=3, gap_w_px=139):
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError("Image not found.")

    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # Define HSV ranges for mango categories
    color_ranges = {
        "green":      (np.array([35, 40, 40]), np.array([85, 255, 255])),
        "yellow":     (np.array([20, 40, 40]), np.array([30, 255, 255])),
        "yellowgreen":(np.array([25, 40, 40]), np.array([40, 255, 255]))
    }

    # Combine masks for all categories
    mask_total = np.zeros(hsv.shape[:2], dtype=np.uint8)
    for category, (lower, upper) in color_ranges.items():
        mask = cv2.inRange(hsv, lower, upper)
        mask_total = cv2.bitwise_or(mask_total, mask)

    # Clean mask
    kernel = np.ones((5, 5), np.uint8)
    mask_clean = cv2.morphologyEx(mask_total, cv2.MORPH_OPEN, kernel)
    mask_clean = cv2.morphologyEx(mask_clean, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(mask_clean, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        raise ValueError("No mango detected.")

    mango_contour = max(contours, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(mango_contour)

    # Scaling
    cm_per_pixel = gap_w_cm / gap_w_px
    mango_length_cm = w * cm_per_pixel
    mango_width_cm  = h * cm_per_pixel
    mango_area_cm2  = mango_length_cm * mango_width_cm

    print(f"Mango length (horizontal): {mango_length_cm:.2f} cm")
    print(f"Mango width (vertical): {mango_width_cm:.2f} cm")
    print(f"Estimated Mango Area: {mango_area_cm2:.2f} cm²")

    # Visualization
    output = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    cv2.rectangle(output, (x, y), (x + w, y + h), (0, 255, 0), 2)

    plt.figure(figsize=(12,4))
    plt.subplot(1,3,1); plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB)); plt.title("Original"); plt.axis("off")
    plt.subplot(1,3,2); plt.imshow(mask_clean, cmap="gray"); plt.title("Combined Mask"); plt.axis("off")
    plt.subplot(1,3,3); plt.imshow(output); plt.title("Bounding Box"); plt.axis("off")
    plt.show()

# Example usage
calculate_mango_area("img(3).jpg", gap_w_cm=3, gap_w_px=139)