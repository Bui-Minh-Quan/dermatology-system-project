from torchvision import transforms

DISEASE_CLASSES_9 = sorted([
    'Acne Vulgaris',
    'Atopic Dermatitis',
    'Contact Dermatitis',
    'Normal Skin',
    'Psoriasis',
    'Rosacea',
    'Seborrheic Dermatitis',
    'Tinea',
    'Urticaria'
])

skin_detector_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

disease_classifier_transform = transforms.Compose([
    transforms.Resize((384, 384)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])