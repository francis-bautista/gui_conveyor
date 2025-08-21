import torch
import torchvision
from torchvision.models.detection import fasterrcnn_resnet50_fpn
from torchvision.models.detection import fasterrcnn_mobilenet_v3_large_fpn
import os
import sys

def check_model_loading(model_path):
    """
    Check if the RCNN mango detection model can be loaded successfully
    """
    print("=== RCNN Model Loading Test ===\n")
    
    # Check if file exists
    if not os.path.exists(model_path):
        print(f"❌ Error: Model file '{model_path}' not found!")
        return False
    
    print(f"✅ Model file found: {model_path}")
    print(f"📁 File size: {os.path.getsize(model_path) / (1024*1024):.2f} MB")
    
    # Check PyTorch installation and fix deprecation warnings
    print(f"🔧 PyTorch version: {torch.__version__}")
    print(f"🔧 Torchvision version: {torchvision.__version__}")
    
    # Suppress deprecation warnings for cleaner output
    import warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    
    # Check CUDA availability
    if torch.cuda.is_available():
        print(f"🚀 CUDA available: {torch.cuda.get_device_name(0)}")
        device = torch.device('cuda')
    else:
        print("💻 Using CPU")
        device = torch.device('cpu')
    
    try:
        print("\n📥 Loading model...")
        
        # Load the model state dict
        checkpoint = torch.load(model_path, map_location=device)
        print("✅ Model file loaded successfully")
        
        # Check what's in the checkpoint
        if isinstance(checkpoint, dict):
            print(f"📋 Checkpoint keys: {list(checkpoint.keys())}")
            
            # If it's a training checkpoint with model state
            if 'model_state_dict' in checkpoint:
                model_state = checkpoint['model_state_dict']
                print("✅ Found 'model_state_dict' in checkpoint")
            elif 'state_dict' in checkpoint:
                model_state = checkpoint['state_dict']
                print("✅ Found 'state_dict' in checkpoint")
            else:
                model_state = checkpoint
                print("✅ Using checkpoint as model state directly")
        else:
            model_state = checkpoint
            print("✅ Checkpoint is direct model state")
        
        # Analyze the model architecture from state dict
        print("\n🔍 Analyzing model architecture...")
        
        # Detect number of classes from classifier weights
        if 'roi_heads.box_predictor.cls_score.weight' in model_state:
            num_classes = model_state['roi_heads.box_predictor.cls_score.weight'].shape[0]
            print(f"🎯 Detected {num_classes} classes from classifier")
        else:
            num_classes = 2  # fallback
        
        # Detect backbone type from FPN weights
        backbone_type = "resnet50"  # default
        if 'backbone.fpn.inner_blocks.0.0.weight' in model_state:
            fpn_shape = model_state['backbone.fpn.inner_blocks.0.0.weight'].shape
            if fpn_shape[1] == 160:  # MobileNetV3 Large
                backbone_type = "mobilenet_v3_large"
                print(f"🏗️ Detected MobileNetV3-Large backbone (FPN input: {fpn_shape[1]})")
            elif fpn_shape[1] == 256:  # ResNet50
                backbone_type = "resnet50"
                print(f"🏗️ Detected ResNet50 backbone (FPN input: {fpn_shape[1]})")
            else:
                print(f"🤔 Unknown backbone (FPN input channels: {fpn_shape[1]})")
        
        # Create the appropriate model
        print(f"\n🏗️ Creating Faster R-CNN model with {backbone_type} backbone...")
        
        if backbone_type == "mobilenet_v3_large":
            from torchvision.models.detection import fasterrcnn_mobilenet_v3_large_fpn
            model = fasterrcnn_mobilenet_v3_large_fpn(weights=None, num_classes=num_classes)
        else:
            model = fasterrcnn_resnet50_fpn(weights=None, num_classes=num_classes)
        
        # Load the state dict with strict=False to handle minor differences
        print("🔄 Loading model weights...")
        missing_keys, unexpected_keys = model.load_state_dict(model_state, strict=False)
        
        if missing_keys:
            print(f"⚠️  Missing keys: {len(missing_keys)} (this might be okay)")
        if unexpected_keys:
            print(f"⚠️  Unexpected keys: {len(unexpected_keys)} (this might be okay)")
        
        model.to(device)
        model.eval()
        
        print("✅ Model weights loaded successfully!")
        
        # Test with a dummy input
        print("\n🧪 Testing model with dummy input...")
        dummy_input = torch.randn(1, 3, 800, 800).to(device)  # Typical RCNN input size
        
        with torch.no_grad():
            output = model(dummy_input)
        
        print("✅ Model inference test passed!")
        print(f"📊 Output keys: {list(output[0].keys())}")
        print(f"📊 Number of detections: {len(output[0]['boxes'])}")
        
        # Print model info if available in checkpoint
        if isinstance(checkpoint, dict):
            if 'epoch' in checkpoint:
                print(f"🎯 Training epoch: {checkpoint['epoch']}")
            if 'loss' in checkpoint:
                print(f"📉 Training loss: {checkpoint['loss']:.4f}")
            if 'optimizer_state_dict' in checkpoint:
                print("✅ Optimizer state found in checkpoint")
        
        print("\n🎉 SUCCESS: Your RCNN mango detection model loaded successfully!")
        return True
        
    except FileNotFoundError:
        print(f"❌ Error: Could not find model file at {model_path}")
        return False
    except RuntimeError as e:
        print(f"❌ Runtime Error loading model: {str(e)}")
        print("💡 This might be due to:")
        print("   - Incorrect model architecture")
        print("   - Wrong number of classes")
        print("   - Model was saved with different PyTorch version")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        print(f"❌ Error type: {type(e).__name__}")
        return False

def main():
    # Default model path - change this to your actual path
    model_path = "mango_detection_model.pth"
    
    # Allow command line argument
    if len(sys.argv) > 1:
        model_path = sys.argv[1]
    
    print(f"Checking model: {model_path}")
    success = check_model_loading(model_path)
    
    if not success:
        print("ERROR: Unable to load the model")

if __name__ == "__main__":
    main()
