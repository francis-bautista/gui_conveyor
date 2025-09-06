import cv2, os, torch, torchvision, math
import numpy as np
from typing import List, Dict, Tuple
from torchvision.models.detection import fasterrcnn_mobilenet_v3_large_fpn

class MangoMeasurementSystem:
    def __init__(self, model_path, num_classes=7):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = self.load_model(model_path, num_classes)
        
        self.class_names = {
            1: 'bruised', 2: 'not_bruised', 3: 'yellow',
            4: 'green_yellow', 5: 'green', 6: 'mango', 7: 'background'
        }
        # coin object reference
        self.reference_box = [815, 383, 999, 556]
        # self.reference_box = [980, 435, 1164, 612]  # [x1, y1, x2, y2] of reference object
        self.reference_size_cm = 2.4  # Known size of reference object in cm

    def load_model(self, model_path, num_classes=7):
        try:
            print("Creating Faster R-CNN with MobileNetV3-Large backbone...")
            
            model = fasterrcnn_mobilenet_v3_large_fpn(weights=None, num_classes=num_classes)
            
            print("Loading model weights...")
            checkpoint = torch.load(model_path, map_location=self.device)
            
            if isinstance(checkpoint, dict):
                if 'model_state_dict' in checkpoint:
                    model_state = checkpoint['model_state_dict']
                elif 'state_dict' in checkpoint:
                    model_state = checkpoint['state_dict']
                else:
                    model_state = checkpoint
            else:
                model_state = checkpoint
            
            missing_keys, unexpected_keys = model.load_state_dict(model_state, strict=False)
            
            if missing_keys:
                print(f"⚠️ Missing keys: {len(missing_keys)}")
            if unexpected_keys:
                print(f"⚠️ Unexpected keys: {len(unexpected_keys)}")
            
            model.to(self.device)
            model.eval()
            
            print(f"Model loaded successfully on {self.device}")
            print(f"Classes: {num_classes}")
            self.model = model
            
            return model
            
        except Exception as e:
            print(f"Error loading model: {e}")
            return None    
    
    def get_size(self, img_path, confidence_threshold=0.2, save_annotated=True):
        image = cv2.imread(img_path)
        if image is None:
            print(f"Could not load image: {img_path}")
            return []
        print("loaded img")
        x1, y1, x2, y2 = self.reference_box
        ref_width_pixels = x2 - x1
        ref_height_pixels = y2 - y1
        ref_size_pixels = max(ref_width_pixels, ref_height_pixels)
        pixels_per_cm = ref_size_pixels / self.reference_size_cm
        
        print(f"Calibration: {pixels_per_cm:.2f} pixels/cm")
        
        if self.model is None:
            print("Model not loaded")
            return []
        print("loaded rcnn model")
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image_tensor = torch.tensor(image_rgb, dtype=torch.float32).permute(2, 0, 1) / 255.0
        input_tensor = image_tensor.unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            predictions = self.model(input_tensor)
        
        pred = predictions[0]
        boxes = pred['boxes'].cpu().numpy()
        scores = pred['scores'].cpu().numpy()
        labels = pred['labels'].cpu().numpy()
        
        keep = scores >= confidence_threshold
        
        results = []
        for i, (box, score, label) in enumerate(zip(boxes[keep], scores[keep], labels[keep])):
            x1, y1, x2, y2 = box
            
            width_pixels = x2 - x1
            height_pixels = y2 - y1
            
            width_cm = width_pixels / pixels_per_cm
            height_cm = height_pixels / pixels_per_cm
            
            length_cm = max(width_cm, height_cm)
            width_cm = min(width_cm, height_cm)
            
            area_cm2 = length_cm * width_cm
            
            a = length_cm / 2
            b = width_cm / 2
            c = (a + b) / 2
            
            result = {
                'mango_id': i,
                'class': self.class_names.get(label, f'Class_{label}'),
                'confidence': round(score, 3),
                'length_cm': round(length_cm, 2), #3
                'width_cm': round(width_cm, 2), #4
                'area_cm2': round(area_cm2, 2),
                'bounding_box': box.tolist()
            }
            results.append(result)
        
        print(f"\nFound {len(results)} mangoes:")
        for result in results:
            print(f"Mango {result['mango_id']} ({result['class']}):")
            print(f"  Length: {result['length_cm']} cm")
            print(f"  Width: {result['width_cm']} cm") 
            print(f"  Area: {result['area_cm2']} cm²")
            print(f"  Confidence: {result['confidence']}")
        
        if save_annotated and results:
            self._save_annotated_image(image, results, img_path)
        
        return results


    def _save_annotated_image(self, image, results, original_path):
        
        annotated_image = image.copy()
        
        for result in results:
            box = result['bounding_box']
            x1, y1, x2, y2 = [int(coord) for coord in box]
            
            cv2.rectangle(annotated_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            text_lines = [
                f"ID: {result['mango_id']} ({result['class']})",
                f"L: {result['length_cm']} cm",
                f"W: {result['width_cm']} cm",
                f"Area: {result['area_cm2']} cm²",
            ]
            
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.6
            font_thickness = 2
            line_height = 25
            
            text_start_y = max(y1 - 10, line_height * len(text_lines))
            
            for i, line in enumerate(text_lines):
                text_y = text_start_y - (len(text_lines) - i - 1) * line_height
                
                (text_width, text_height), baseline = cv2.getTextSize(line, font, font_scale, font_thickness)
                
                overlay = annotated_image.copy()
                cv2.rectangle(overlay, 
                             (x1, text_y - text_height - 5), 
                             (x1 + text_width + 10, text_y + baseline + 5), 
                             (0, 255, 0), -1)
                cv2.addWeighted(annotated_image, 0.7, overlay, 0.3, 0, annotated_image)
                
                cv2.putText(annotated_image, line, (x1 + 5, text_y), 
                           font, font_scale, (0, 0, 0), font_thickness)
        
        base_name = os.path.splitext(original_path)[0]
        extension = os.path.splitext(original_path)[1]
        output_path = f"{base_name}_measured{extension}"
        
        success = cv2.imwrite(output_path, annotated_image)
        
        if success:
            print(f"\nAnnotated image saved as: {output_path}")
        else:
            print(f"Error: Could not save annotated image to {output_path}")
