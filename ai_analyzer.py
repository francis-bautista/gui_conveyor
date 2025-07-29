import torch
import torchvision.transforms as transforms
from efficientnet_pytorch import EfficientNet

class AIAnalyzer:
    def __init__(self, device):
        self.device = device
        self.CLASS_LABEL_RIPENESS = ['green', 'yellow_green', 'yellow']
        self.CLASS_LABEL_BRUISES = ['bruised', 'unbruised']
        self.CLASS_LABEL_SIZE = ['small', 'medium', 'large']
        self.RIPENESS_SCORES = {'yellow': 1.0, 'yellow_green': 2.0, 'green': 3.0}
        self.BRUISES_SCORES = {'bruised': 1.5, 'unbruised': 3.0}
        self.SIZE_SCORES = {'small': 1.0, 'medium': 2.0, 'large': 3.0}
        self.transform = self.create_transform()
        self.load_models()
    
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
    
    def load_models(self):
        self.model_ripeness = EfficientNet.from_pretrained('efficientnet-b0', num_classes=len(self.CLASS_LABEL_RIPENESS))
        self.model_ripeness.load_state_dict(torch.load("ripeness.pth", map_location=self.device))
        self.model_ripeness.eval()
        self.model_ripeness.to(self.device)
        self.model_bruises = EfficientNet.from_pretrained('efficientnet-b0', num_classes=len(self.CLASS_LABEL_BRUISES))
        self.model_bruises.load_state_dict(torch.load("bruises.pth", map_location=self.device))
        self.model_bruises.eval()
        self.model_bruises.to(self.device)
    
    def get_predicted_class(self, image, isRipeness):
        image = self.transform(image).unsqueeze(0).to(self.device)
        if (isRipeness):
            output = self.model_ripeness(image)
            class_labels = list(self.RIPENESS_SCORES.keys())
        else:
            output = self.model_bruises(image)            
            class_labels = list(self.BRUISES_SCORES.keys())
        _, predicted = torch.max(output, 1)

        return class_labels[predicted.item()]
    
    def get_overall_grade(self, scores, predicted):
        resulting_grade = (predicted['r']*self.RIPENESS_SCORES[scores['r']] +
            predicted['b']*self.BRUISES_SCORES[scores['b']] +
            predicted['s']*self.SIZE_SCORES[scores['s']])
        print(f"Resulting Grade: {resulting_grade}")
        return resulting_grade

