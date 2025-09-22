#!/usr/bin/env python3

import argparse
import sys
import os
from pathlib import Path
import torch
from PIL import Image
import glob

from ai_analyzer import AIAnalyzer

def setup_device():
    if torch.cuda.is_available():
        device = torch.device("cuda")
        print(f"Using GPU: {torch.cuda.get_device_name(0)}")
    else:
        device = torch.device("cpu")
        print("Using CPU")
    return device

def load_image(image_path):
    try:
        image = Image.open(image_path).convert('RGB')
        print(f"Successfully loaded image: {image_path}")
        print(f"Image size: {image.size}")
        return image
    except Exception as e:
        print(f"Error loading image {image_path}: {e}")
        return None

def test_single_image(analyzer, image_path, test_ripeness=True, test_bruises=True):
    print(f"\n{'='*60}")
    print(f"Testing image: {os.path.basename(image_path)}")
    print(f"{'='*60}")
    
    image = load_image(image_path)
    if image is None:
        return None
    
    results = {}
    
    if test_ripeness and analyzer.get_is_ripeness():
        print(f"\n{'-'*30} RIPENESS ANALYSIS {'-'*30}")
        ripeness_class = analyzer.get_predicted_class(image, isRipeness=True)
        results['ripeness'] = ripeness_class
    
    if test_bruises and analyzer.get_is_bruises():
        print(f"\n{'-'*30} BRUISES ANALYSIS {'-'*30}")
        bruises_class = analyzer.get_predicted_class(image, isRipeness=False)
        results['bruises'] = bruises_class
    
    if len(results) >= 2:
        print(f"\n{'-'*30} OVERALL GRADE {'-'*30}")
        scores = {
            'ripeness': results.get('ripeness', 'yellow'),
            'bruises': results.get('bruises', 'unbruised'),
            'size': 'medium'
        }
        
        predicted = {
            'ripeness': 1.0,
            'bruises': 1.0,
            'size': 1.0
        }
        
        print("Overall grade calculation requires size analysis implementation")
    
    return results

def test_batch_images(analyzer, image_pattern, test_ripeness=True, test_bruises=True):
    image_paths = glob.glob(image_pattern)
    
    if not image_paths:
        print(f"No images found matching pattern: {image_pattern}")
        return
    
    print(f"Found {len(image_paths)} images to test")
    
    all_results = {}
    
    for image_path in sorted(image_paths):
        results = test_single_image(analyzer, image_path, test_ripeness, test_bruises)
        if results:
            all_results[os.path.basename(image_path)] = results
    
    print(f"\n{'='*60}")
    print("BATCH TEST SUMMARY")
    print(f"{'='*60}")
    
    for filename, results in all_results.items():
        print(f"{filename:30} -> ", end="")
        if 'ripeness' in results:
            print(f"Ripeness: {results['ripeness']:12} ", end="")
        if 'bruises' in results:
            print(f"Bruises: {results['bruises']:10} ", end="")
        print()

def main():
    parser = argparse.ArgumentParser(
        description="Test images with AI Analyzer models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_images.py image.jpg                    
  python test_images.py image.jpg --ripeness-only    
  python test_images.py image.jpg --bruises-only     
  python test_images.py "*.jpg" --batch              
  python test_images.py "images/*.png" --batch       
        """
    )
    
    parser.add_argument("image_path", 
                       help="Path to image file or glob pattern for batch processing")
    
    parser.add_argument("--batch", 
                       action="store_true",
                       help="Process multiple images using glob pattern")
    
    parser.add_argument("--ripeness-only", 
                       action="store_true",
                       help="Test ripeness classification only")
    
    parser.add_argument("--bruises-only", 
                       action="store_true",
                       help="Test bruises classification only")
    
    parser.add_argument("--device", 
                       choices=['auto', 'cpu', 'cuda'],
                       default='auto',
                       help="Device to use for inference (default: auto)")
    
    args = parser.parse_args()
    
    if args.ripeness_only and args.bruises_only:
        print("Error: Cannot specify both --ripeness-only and --bruises-only")
        sys.exit(1)
    
    if args.device == 'auto':
        device = setup_device()
    elif args.device == 'cuda':
        if torch.cuda.is_available():
            device = torch.device("cuda")
            print(f"Using GPU: {torch.cuda.get_device_name(0)}")
        else:
            print("CUDA not available, falling back to CPU")
            device = torch.device("cpu")
    else:
        device = torch.device("cpu")
        print("Using CPU")
    
    RIPENESS_SCORES = {'green': 3.0, 'yellow': 1.0, 'yellow_green': 2.0}
    BRUISES_SCORES = {'bruised': 1.0, 'unbruised': 2.0}
    SIZE_SCORES = {'small': 1.0, 'medium': 2.0, 'large': 3.0}
    
    print("Initializing AI Analyzer...")
    try:
        analyzer = AIAnalyzer(device, RIPENESS_SCORES, BRUISES_SCORES, SIZE_SCORES)
    except Exception as e:
        print(f"Error initializing AI Analyzer: {e}")
        print("Make sure the model files (ripeness_v2b3_02.pth, bruises_v2b3_02.pth) are in the current directory")
        sys.exit(1)
    
    test_ripeness = not args.bruises_only
    test_bruises = not args.ripeness_only
    
    if args.batch:
        test_batch_images(analyzer, args.image_path, test_ripeness, test_bruises)
    else:
        if not os.path.exists(args.image_path):
            print(f"Error: Image file '{args.image_path}' not found")
            sys.exit(1)
        
        test_single_image(analyzer, args.image_path, test_ripeness, test_bruises)

if __name__ == "__main__":
    main()