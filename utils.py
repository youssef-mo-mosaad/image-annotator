from PIL import Image

def get_image_size(image_path):
    with Image.open(image_path) as img:
        return img.size

def validate_annotations(annotations):
    valid = True
    errors = []
    
    for idx, ann in annotations.items():
        if not os.path.exists(ann['image_path']):
            valid = False
            errors.append(f"Image not found: {ann['image_path']}")
            continue
            
        img_width, img_height = ann['image_size']
        bbox = ann['bbox']
        
        if (bbox['x'] + bbox['width'] > img_width or 
            bbox['y'] + bbox['height'] > img_height):
            valid = False
            errors.append(f"Bounding box out of image bounds in {ann['image_path']}")
    
    return valid, errors