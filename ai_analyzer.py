import torch
import torchvision.transforms as transforms
from efficientnet_pytorch import EfficientNet

class AIAnalyzer:
    def __init__(self, device, ripeness_scores, bruises_scores, size_scores):
        self.device = device
        self.RIPENESS_SCORES = ripeness_scores
        self.BRUISES_SCORES = bruises_scores
        self.SIZE_SCORES = size_scores
        self.transform = self.create_transform()
        self.load_models()
    def get_is_ripeness(self):
        return True
    def get_is_bruises(self):
        return False
    def get_is_s1(self):
        return True
    def get_is_s2(self):
        return False
    def create_transform(self):
        self.tf_params = {'px': 224, 'py': 224,
                          'mean_r':0.485, 'mean_g':0.456, 'mean_b':0.406,
                          'sd_r':0.229, 'sd_g':0.224, 'sd_b': 0.225}
        transform = transforms.Compose([
            transforms.Resize((self.tf_params['px'], self.tf_params['py'])),
            transforms.ToTensor(),
            transforms.Normalize([self.tf_params['mean_r'], self.tf_params['mean_g'], self.tf_params['mean_b']],
                                 [self.tf_params['sd_r'], self.tf_params['sd_g'], self.tf_params['sd_b']])
        ])

        return transform
    
        """     
        def load_models(self):
            # TODO: change this one to the specific version of the efficientnet
            # b0 -> b4
            # bruises -> bruises_b4
            self.model_ripeness = EfficientNet.from_pretrained('efficientnet-b4', num_classes=len(self.RIPENESS_SCORES))
            self.model_ripeness.load_state_dict(torch.load("ripeness_b4.pth", map_location=self.device))
            self.model_ripeness.eval()
            self.model_ripeness.to(self.device)
            self.model_bruises = EfficientNet.from_pretrained('efficientnet-b4', num_classes=len(self.BRUISES_SCORES))
            self.model_bruises.load_state_dict(torch.load("bruises_b4.pth", map_location=self.device))
            self.model_bruises.eval()
            self.model_bruises.to(self.device)
            print("loaded the ripeness and bruises model") 
        """

    def load_models(self):
        from torchvision.models import efficientnet_v2_m, EfficientNet_V2_M_Weights
        import torch.nn as nn
        
        # Load ripeness model (EfficientNetV2-M)
        weights = EfficientNet_V2_M_Weights.IMAGENET1K_V1
        self.model_ripeness = efficientnet_v2_m(weights=weights)
        self.model_ripeness.classifier[1] = nn.Linear(
            self.model_ripeness.classifier[1].in_features, 
            len(self.RIPENESS_SCORES)
        )
        self.model_ripeness = self.model_ripeness.to(self.device)
        self.model_ripeness.load_state_dict(torch.load("ripeness_v2m.pth", map_location=self.device))
        self.model_ripeness.eval()
        
        # Load bruises model (EfficientNetV2-M)
        weights = EfficientNet_V2_M_Weights.IMAGENET1K_V1
        self.model_bruises = efficientnet_v2_m(weights=weights)
        self.model_bruises.classifier[1] = nn.Linear(
            self.model_bruises.classifier[1].in_features, 
            len(self.BRUISES_SCORES)
        )
        self.model_bruises = self.model_bruises.to(self.device)
        self.model_bruises.load_state_dict(torch.load("bruises_v2m.pth", map_location=self.device))
        self.model_bruises.eval()
        
        print("loaded the ripeness and bruises model")
                  
    def get_predicted_class(self, image, isRipeness):
        image = self.transform(image).unsqueeze(0).to(self.device)
        
        with torch.no_grad():  # Disable gradient computation for inference
            if (isRipeness):
                output = self.model_ripeness(image)
                class_labels = list(self.RIPENESS_SCORES.keys())
            else:
                output = self.model_bruises(image)            
                class_labels = list(self.BRUISES_SCORES.keys())
            
            # Apply softmax to get probabilities
            probabilities = torch.softmax(output, dim=1)
            
            # Get the highest confidence prediction
            confidence, predicted = torch.max(probabilities, 1)
            
            predicted_class = class_labels[predicted.item()]
            confidence_score = confidence.item()
            
            # Display confidence information
            print(f"Predicted class: {predicted_class}")
            print(f"Confidence: {confidence_score:.4f} ({confidence_score*100:.2f}%)")
            
            # Optional: Display all class probabilities
            print("All class probabilities:")
            for i, label in enumerate(class_labels):
                prob = probabilities[0][i].item()
                print(f"  {label}: {prob:.4f} ({prob*100:.2f}%)")
            
            return predicted_class, confidence_score
        
    def get_overall_grade(self, scores, predicted):
        resulting_grade = (predicted['ripeness']*self.RIPENESS_SCORES[scores['ripeness']] +
            predicted['bruises']*self.BRUISES_SCORES[scores['bruises']] +
            predicted['size']*self.SIZE_SCORES[scores['size']])
        print(f"Resulting Grade: {resulting_grade}")
        return resulting_grade

