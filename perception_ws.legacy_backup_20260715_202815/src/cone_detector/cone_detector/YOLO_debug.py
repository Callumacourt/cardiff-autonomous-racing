#!/usr/bin/env python3
"""
Debug YOLO model to understand class mappings and detect issues
"""

import torch
from ultralytics import YOLO
import cv2
import numpy as np

def analyze_model_classes(model_path):
    """Analyze the model's class definitions"""
    print("🔍 Analyzing Model Classes")
    print("=" * 40)
    
    try:
        # Load model
        model = YOLO(model_path)
        
        # Get class names
        if hasattr(model.model, 'names'):
            class_names = model.model.names
            print(f"Number of classes: {len(class_names)}")
            print("Class mapping:")
            for class_id, name in class_names.items():
                print(f"  {class_id}: {name}")
        else:
            print("Could not extract class names from model")
            
        # Load raw checkpoint to get more info
        ckpt = torch.load(model_path, map_location='cpu')
        if 'model' in ckpt and hasattr(ckpt['model'], 'names'):
            print(f"\nRaw checkpoint classes: {ckpt['model'].names}")
            
        return class_names if hasattr(model.model, 'names') else None
        
    except Exception as e:
        print(f"Error analyzing model: {e}")
        return None

def test_color_detection_on_sample():
    """Test color detection on a sample image"""
    print("\n🎨 Testing Color Detection")
    print("=" * 40)
    
    # Create sample images with different colors
    colors = {
        'blue': (255, 0, 0),     # BGR format
        'yellow': (0, 255, 255),
        'orange': (0, 165, 255)
    }
    
    for color_name, bgr_color in colors.items():
        # Create colored image
        test_image = np.full((100, 100, 3), bgr_color, dtype=np.uint8)
        
        # Test HSV conversion
        hsv = cv2.cvtColor(test_image, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)
        
        print(f"{color_name.upper()}:")
        print(f"  BGR: {bgr_color}")
        print(f"  HSV: H={h[0,0]}, S={s[0,0]}, V={v[0,0]}")
        
        # Check against your original HSV ranges
        blue_range = (100, 130)
        yellow_range = (20, 35)
        orange_range = (5, 20)
        
        hue = h[0,0]
        if blue_range[0] <= hue <= blue_range[1]:
            print(f"Would be detected as BLUE")
        elif yellow_range[0] <= hue <= yellow_range[1]:
            print(f"Would be detected as YELLOW")
        elif orange_range[0] <= hue <= orange_range[1]:
            print(f"Would be detected as ORANGE")
        else:
            print(f"Would NOT be detected (H={hue})")
        print()

def suggest_fixes():
    """Suggest potential fixes for the issues"""
    print("\n🔧 Suggested Fixes")
    print("=" * 40)
    
    print("1. MODEL CLASS MAPPING:")
    print("   - Check if your model's class 0, 1, 2 correspond to blue, yellow, orange")
    print("   - Your model might have different class ordering")
    print("   - Use the class debugger output to fix the mapping")
    
    print("\n2. MISSING YELLOW CONES:")
    print("   - Model might not be trained on yellow cones")
    print("   - Yellow cones might be classified as different class")
    print("   - Check if yellow cones are being detected as class 2 (orange)")
    
    print("\n3. IMMEDIATE FIXES (no retraining needed):")
    print("   - Lower confidence threshold: conf_threshold = 0.3")
    print("   - Add HSV post-processing for color classification")
    print("   - Use bounding boxes from YOLO + HSV color analysis")
    
    print("\n4. PERFORMANCE OPTIMIZATIONS:")
    print("   - ROI masking is now implemented")
    print("   - Distance filtering is now implemented")
    print("   - Consider resizing input images")

def create_color_classifier():
    """Create a simple HSV-based color classifier as backup"""
    print("\nHSV Color Classifier (Backup Solution)")
    print("=" * 40)
    
    code = '''
def classify_cone_color_hsv(image, bbox):
    """
    Classify cone color using HSV analysis within bounding box
    """
    x, y, w, h = bbox
    roi = image[y:y+h, x:x+w]
    
    # Convert to HSV
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    
    # Define HSV ranges
    blue_mask = cv2.inRange(hsv, np.array([100, 100, 100]), np.array([130, 255, 255]))
    yellow_mask = cv2.inRange(hsv, np.array([20, 100, 100]), np.array([35, 255, 255]))
    orange_mask = cv2.inRange(hsv, np.array([5, 100, 100]), np.array([20, 255, 255]))
    
    # Count pixels for each color
    blue_pixels = np.sum(blue_mask > 0)
    yellow_pixels = np.sum(yellow_mask > 0)
    orange_pixels = np.sum(orange_mask > 0)
    
    # Determine dominant color
    if blue_pixels > yellow_pixels and blue_pixels > orange_pixels:
        return "blue", 0
    elif yellow_pixels > orange_pixels:
        return "yellow", 1
    else:
        return "orange", 2
'''
    
    print("Use this function to classify colors from YOLO bounding boxes:")
    print(code)

def main():
    """Main debugging function"""
    print("🐛 YOLO Model Debugger")
    print("=" * 50)
    
    # Analyze model classes
    model_path = "/home/ritvik/ros2_ws/src/cone_detector/cone_detector/train3_25_iou050_lrf012/content/{HOME}/datasets/runs/detect/train/weights/best.pt"
    class_names = analyze_model_classes(model_path)
    
    # Test color detection
    test_color_detection_on_sample()
    
    # Print suggestions
    suggest_fixes()
    
    # Show backup color classifier
    create_color_classifier()
    
    print("\n" + "=" * 50)
    print("NEXT STEPS:")
    print("1. Check the class mapping output above")
    print("2. Update your get_cone_color_from_class() function")
    print("3. Consider adding HSV post-processing")
    print("4. Test with lower confidence threshold")
    print("5. Run your detector again and monitor class distribution")

if __name__ == "__main__":
    main()
