# Image Annotator
A modern, user-friendly desktop application for creating bounding box annotations on images. Export your annotations in COCO, YOLO, and Pascal VOC formats with a single click.

## Features
- 🖼️ Intuitive Interface: Clean, modern GUI with professional styling

- 🎯 Multi-format Export: Export annotations to COCO JSON, YOLO TXT, and Pascal VOC XML formats

- ⌨️ Keyboard Shortcuts: Navigate and annotate efficiently with keyboard controls

- 📊 Real-time Statistics: Track progress with live annotation statistics

- 🎨 Visual Feedback: Color-coded bounding boxes with class labels

- 🔄 Easy Navigation: Quickly move between images with arrow keys or buttons

- 🗂️ Class Management: Smart class selection with auto-suggestions from previous annotations

<img width="1920" height="1021" alt="image" src="https://github.com/user-attachments/assets/afaf6eb0-d283-4c8c-b04e-db30ae400b33" />

## Installation
### Prerequisites
Python 3.7+

### Dependencies
Install the required packages:

```bash
pip install -r requirements.txt
```
Running the Application
```bash
python main.py
```

## Usage
Load Images: Click "Load Images" and select a folder containing your images

Draw Annotations: Click and drag to create bounding boxes around objects

Classify Objects: Enter or select a class name for each annotation

Navigate: Use arrow keys or buttons to move between images

Export: Click "Export All" to save annotations in all supported formats

<img width="1920" height="1018" alt="image" src="https://github.com/user-attachments/assets/72089951-58fb-4d33-9f9e-69b67581e934" />


## Keyboard Shortcuts
- `Left Arrow`: Previous image
- `Right Arrow`: Next image
- `Delete`: Remove last annotation
- `Ctrl+O`: Load new folder
- `Ctrl+S`: Export annotations

## Supported Annotation Formats
**`COCO`**: JSON format with category definitions and bounding box coordinates

**`YOLO`**: TXT files with normalized coordinates and class IDs

**`Pascal VOC`**: XML files with object metadata and bounding boxes

## File Structure
```bash
image-annotator/
├── main.py          # Main application GUI
├── writers.py       # Export functions for different formats
├── utils.py         # Utility functions
├── requirements.txt         # Libraries needed to install
├── LICENSE/     # License
└── README.md        # This file
```

## Output Structure
After export, your annotations will be organized as:

```bash
your-image-folder/
└── annotations/
    ├── coco/
    │   ├── images/
    │   └── annotations.coco.json
    ├── yolo/
    │   ├── images/
    │   ├── classes.txt
    │   └── [image_name].txt files
    └── pascal/
        ├── images/
        └── [image_name].xml files
```
<img width="569" height="386" alt="image" src="https://github.com/user-attachments/assets/3d04fbb4-e9f2-43ef-b680-f84a0b33fdf7" />

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## License
This project is open source and available under the MIT License.
