import os
import json
import shutil
import xml.etree.ElementTree as ET
from xml.dom import minidom

def cleanup_output_dir(output_dir):
    """Remove the output directory if it exists to ensure clean export"""
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)

def export_to_coco(annotations, output_dir):
    coco_dir = os.path.join(output_dir, "coco")
    images_dir = os.path.join(coco_dir, "images")
    os.makedirs(images_dir, exist_ok=True)
    output_path = os.path.join(coco_dir, "annotations.coco.json")
    
    coco_data = {
        "images": [],
        "annotations": [],
        "categories": []
    }
    categories = {}
    category_id = 1
    
    for idx, ann in annotations.items():
        img_width, img_height = ann['image_size']
        img_filename = os.path.basename(ann['image_path'])
        coco_data["images"].append({
            "id": idx,
            "file_name": img_filename,
            "width": img_width,
            "height": img_height
        })
        # Copy image
        shutil.copy(ann['image_path'], os.path.join(images_dir, img_filename))
        
        for obj in ann['objects']:
            if obj['class'] not in categories:
                categories[obj['class']] = category_id
                coco_data["categories"].append({
                    "id": category_id,
                    "name": obj['class'],
                    "supercategory": "none"
                })
                category_id += 1
            
            if obj['width'] > img_width:
                obj['width'] = img_width
            if obj['height'] > img_height:
                obj['height'] = img_height
                
            coco_data["annotations"].append({
                "id": len(coco_data["annotations"]),
                "image_id": idx,
                "category_id": categories[obj['class']],
                "bbox": [obj['x'], obj['y'], obj['width'], obj['height']],
                "area": obj['width'] * obj['height'],
                "iscrowd": 0
            })
    
    with open(output_path, 'w') as f:
        json.dump(coco_data, f, indent=2)

def export_to_yolo(annotations, output_dir):
    
    yolo_dir = os.path.join(output_dir, "yolo")
    images_dir = os.path.join(yolo_dir, "images")
    os.makedirs(images_dir, exist_ok=True)
    classes = set()
    for ann in annotations.values():
        for obj in ann['objects']:
            classes.add(obj['class'])
    
    with open(os.path.join(yolo_dir, 'classes.txt'), 'w') as f:
        for cls in sorted(classes):
            f.write(f"{cls}\n")
    
    class_list = sorted(list(classes))
    for idx, ann in annotations.items():
        img_width, img_height = ann['image_size']
        img_filename = os.path.basename(ann['image_path'])
        txt_path = os.path.join(yolo_dir, os.path.splitext(img_filename)[0] + '.txt')
        # Copy image
        shutil.copy(ann['image_path'], os.path.join(images_dir, img_filename))
        
        with open(txt_path, 'w') as f:
            for obj in ann['objects']:
                x_center = (obj['x'] + obj['width'] / 2) / img_width
                y_center = (obj['y'] + obj['height'] / 2) / img_height
                width = obj['width'] / img_width
                height = obj['height'] / img_height
                class_id = class_list.index(obj['class'])
                f.write(f"{class_id} {x_center} {y_center} {width} {height}\n")

def export_to_pascal(annotations, output_dir):
    
    pascal_dir = os.path.join(output_dir, "pascal")
    images_dir = os.path.join(pascal_dir, "images")
    os.makedirs(images_dir, exist_ok=True)
    
    for idx, ann in annotations.items():
        img_width, img_height = ann['image_size']
        img_filename = os.path.basename(ann['image_path'])
        # Copy image
        shutil.copy(ann['image_path'], os.path.join(images_dir, img_filename))
        
        root = ET.Element("annotation")
        ET.SubElement(root, "filename").text = img_filename
        ET.SubElement(root, "folder").text = "images"
        
        size = ET.SubElement(root, "size")
        ET.SubElement(size, "width").text = str(img_width)
        ET.SubElement(size, "height").text = str(img_height)
        ET.SubElement(size, "depth").text = "3"
        
        for obj in ann['objects']:
            obj_elem = ET.SubElement(root, "object")
            ET.SubElement(obj_elem, "name").text = obj['class']
            ET.SubElement(obj_elem, "pose").text = "Unspecified"
            ET.SubElement(obj_elem, "truncated").text = "0"
            ET.SubElement(obj_elem, "difficult").text = "0"
            bndbox = ET.SubElement(obj_elem, "bndbox")
            ET.SubElement(bndbox, "xmin").text = str(int(obj['x']))
            ET.SubElement(bndbox, "ymin").text = str(int(obj['y']))
            if obj['width'] == img_width:
                ET.SubElement(bndbox, "xmax").text = str(int(obj['width']))
            else:
                ET.SubElement(bndbox, "xmax").text = str(int(obj['width'] + obj['x']))
            if obj['height'] == img_height:
                ET.SubElement(bndbox, "ymax").text = str(int(obj['height']))
            else:
                ET.SubElement(bndbox, "ymax").text = str(int(obj['height'] + obj['y']))
        
        xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
        xml_path = os.path.join(pascal_dir, os.path.splitext(img_filename)[0] + '.xml')
        with open(xml_path, 'w') as f:
            f.write(xml_str)