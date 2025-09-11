import os
import json
from tkinter import *
from tkinter import filedialog, messagebox, simpledialog, ttk
from PIL import Image, ImageTk
import tkinter.font as tkFont
from writers import export_to_coco, export_to_yolo, export_to_pascal, cleanup_output_dir

pro = None
canvas = None
control_frame = None
info_frame = None
sidebar_frame = None
current_index = 0
image_paths = []
photo_ref = None
current_rect = None
start_x, start_y = 0, 0
annotations = {}
output_dir = ""
default_class = "object"
progress_var = None
class_listbox = None
object_listbox = None

# Color scheme
COLORS = {
    'primary': '#2563eb',
    'primary_dark': '#1d4ed8',
    'secondary': '#64748b',
    'success': '#059669',   
    'warning': '#d97706',
    'danger': '#dc2626',
    'background': '#f8fafc',
    'sidebar': '#f1f5f9',
    'white': '#ffffff',
    'text_dark': '#1e293b',
    'text_light': '#64748b',
    'border': '#e2e8f0'
}

def load_image_paths():
    global image_paths, output_dir
    folder_path = filedialog.askdirectory(title="Select Folder with Images")
    if not folder_path:
        messagebox.showerror("Error", "No folder selected")
        return False
    
    image_paths = [os.path.join(folder_path, f) for f in os.listdir(folder_path) 
                if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    
    if not image_paths:
        messagebox.showerror("Error", "No images found")
        return False
    
    output_dir = os.path.join(folder_path, "annotations")
    os.makedirs(output_dir, exist_ok=True)
    update_progress_bar()
    update_sidebar_info()
    return True

def resize_image(img, max_size=800):
    if img.width > max_size or img.height > max_size:
        ratio = min(max_size/img.width, max_size/img.height)
        new_size = (int(img.width * ratio)), int(img.height * ratio)
        return img.resize(new_size, Image.Resampling.LANCZOS)
    return img

def on_mouse_down(event):
    global start_x, start_y, current_rect
    start_x, start_y = event.x, event.y
    if current_rect:
        canvas.delete(current_rect)
    current_rect = canvas.create_rectangle(
        start_x, start_y, start_x, start_y, 
        outline=COLORS['primary'], width=3, dash=(5, 3)
    )

def on_mouse_drag(event):
    if current_rect:
        canvas.coords(current_rect, start_x, start_y, event.x, event.y)

def on_mouse_up(event):
    global current_rect, annotations, current_index, default_class
    
    if not current_rect:
        return
    
    coords = canvas.coords(current_rect)
    if len(coords) != 4:
        return
    
    if abs(coords[2] - coords[0]) < 10 or abs(coords[3] - coords[1]) < 10:
        canvas.delete(current_rect)
        current_rect = None
        return
    
    class_name = show_class_dialog()
    
    if not class_name:
        canvas.delete(current_rect)
        current_rect = None
        return
    
    default_class = class_name
    
    img = Image.open(image_paths[current_index])
    img_width, img_height = img.size
    
    x1, y1, x2, y2 = coords
    width = x2 - x1
    height = y2 - y1
    
    if current_index not in annotations:
        annotations[current_index] = {
            'image_path': image_paths[current_index],
            'image_size': (img_width, img_height),
            'objects': []
        }
    
    annotations[current_index]['objects'].append({
        'x': x1,
        'y': y1,
        'width': width,
        'height': height,
        'class': class_name
    })
    
    # Update the rectangle style
    canvas.itemconfig(current_rect, outline=COLORS['success'], dash=(), width=2)
    
    # Add class label with background
    text_id = canvas.create_text(x1, y1-15, text=class_name, anchor="nw", 
                                fill='white', font=("Segoe UI", 9, "bold"))
    bbox = canvas.bbox(text_id)
    if bbox:
        bg_rect = canvas.create_rectangle(bbox[0]-2, bbox[1]-1, bbox[2]+2, bbox[3]+1, 
                                        fill=COLORS['success'], outline="", width=0)
        canvas.tag_lower(bg_rect, text_id)
    
    update_object_list()
    update_sidebar_info()

def show_class_dialog():
    """Custom class selection dialog"""
    dialog = Toplevel(pro)
    dialog.title("Select Class")
    dialog.geometry("300x400")
    dialog.configure(bg=COLORS['white'])
    dialog.resizable(False, False)
    dialog.transient(pro)
    dialog.grab_set()
    
    # Center the dialog
    dialog.update_idletasks()
    x = (dialog.winfo_screenwidth() // 2) - (300 // 2)
    y = (dialog.winfo_screenheight() // 2) - (400 // 2)
    dialog.geometry(f"300x400+{x}+{y}")
    
    result = [None]
    
    # Title
    title_label = Label(dialog, text="Select Object Class", font=("Segoe UI", 14, "bold"), bg=COLORS['white'], fg=COLORS['text_dark'])
    title_label.pack(pady=20)
    
    # Entry for new class
    Label(dialog, text="Enter new class:", font=("Segoe UI", 10), bg=COLORS['white'], fg=COLORS['text_light']).pack(pady=(0, 5))
    
    entry_var = StringVar(value=default_class)
    class_entry = Entry(dialog, textvariable=entry_var, font=("Segoe UI", 11),width=25, relief=SOLID, bd=1)
    class_entry.pack(pady=(0, 20), ipady=5)
    class_entry.focus_set()
    class_entry.select_range(0, END)
    
    # Existing classes
    if any(annotations.values()):
        existing_classes = set()
        for ann in annotations.values():
            for obj in ann['objects']:
                existing_classes.add(obj['class'])
        
        if existing_classes:
            Label(dialog, text="Or select existing class:", font=("Segoe UI", 10), bg=COLORS['white'], fg=COLORS['text_light']).pack(pady=(0, 5))
            
            # Listbox with scrollbar
            frame = Frame(dialog, bg=COLORS['white'])
            frame.pack(pady=(0, 20), padx=20, fill=BOTH, expand=True)
            
            scrollbar = Scrollbar(frame)
            scrollbar.pack(side=RIGHT, fill=Y)
            
            listbox = Listbox(frame, yscrollcommand=scrollbar.set,
                            font=("Segoe UI", 10), height=6,
                            relief=SOLID, bd=1, selectmode=SINGLE)
            listbox.pack(side=LEFT, fill=BOTH, expand=True)
            scrollbar.config(command=listbox.yview)
            
            for cls in sorted(existing_classes):
                listbox.insert(END, cls)
            
            def on_listbox_select(event):
                selection = listbox.curselection()
                if selection:
                    entry_var.set(listbox.get(selection[0]))
            
            listbox.bind('<<ListboxSelect>>', on_listbox_select)
            listbox.bind('<Double-Button-1>', lambda e: confirm_class())
    
    # Buttons
    button_frame = Frame(dialog, bg=COLORS['white'])
    button_frame.pack(pady=20, fill=X, padx=20)
    
    def confirm_class():
        class_name = entry_var.get().strip()
        if class_name:
            result[0] = class_name
            dialog.destroy()
    
    def cancel_class():
        dialog.destroy()
    
    Button(button_frame, text="Cancel", command=cancel_class,bg=COLORS['secondary'], fg='white', font=("Segoe UI", 10),relief=FLAT, padx=20, pady=8).pack(side=LEFT)
    
    Button(button_frame, text="Confirm", command=confirm_class,bg=COLORS['primary'], fg='white', font=("Segoe UI", 10, "bold"),relief=FLAT, padx=20, pady=8).pack(side=RIGHT)
    
    # Bind Enter key to confirm
    dialog.bind('<Return>', lambda e: confirm_class())
    dialog.bind('<Escape>', lambda e: cancel_class())
    
    dialog.wait_window()
    return result[0]

def show_current_image():
    global photo_ref, current_index, image_paths
    
    if not image_paths or current_index >= len(image_paths):
        return
    
    try:
        img = Image.open(image_paths[current_index])
        original_size = img.size
        img = resize_image(img)
        
        photo_ref = ImageTk.PhotoImage(img)
        
        canvas.config(width=img.width, height=img.height)
        canvas.delete("all")
        canvas.create_image(0, 0, anchor="nw", image=photo_ref)
        
        # Draw existing annotations
        if current_index in annotations:
            for i, obj in enumerate(annotations[current_index]['objects']):
                # Calculate scaled coordinates
                scale_x = img.width / original_size[0]
                scale_y = img.height / original_size[1]
                
                x1 = obj['x'] * scale_x
                y1 = obj['y'] * scale_y
                x2 = x1 + (obj['width'] * scale_x)
                y2 = y1 + (obj['height'] * scale_y)
                
                canvas.create_rectangle(x1, y1, x2, y2,outline=COLORS['success'], width=2)
                
                # Class label with background
                text_id = canvas.create_text(x1, y1-15, text=obj['class'], anchor="nw", fill='white', font=("Segoe UI", 9, "bold"))
                bbox = canvas.bbox(text_id)
                if bbox:
                    bg_rect = canvas.create_rectangle(bbox[0]-2, bbox[1]-1, 
                                                    bbox[2]+2, bbox[3]+1, 
                                                    fill=COLORS['success'], outline="")
                    canvas.tag_lower(bg_rect, text_id)
        
        update_progress_bar()
        update_sidebar_info()
        update_object_list()
        
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load image: {str(e)}")

def next_image():
    global current_index
    if current_index < len(image_paths) - 1:
        current_index += 1
        show_current_image()
    else:
        messagebox.showinfo("Info", "This is the last image")

def prev_image():
    global current_index
    if current_index > 0:
        current_index -= 1
        show_current_image()
    else:
        messagebox.showinfo("Info", "This is the first image")

def delete_last_annotation():
    """Delete the last annotation from current image"""
    global annotations, current_index
    if current_index in annotations and annotations[current_index]['objects']:
        annotations[current_index]['objects'].pop()
        if not annotations[current_index]['objects']:
            del annotations[current_index]
        show_current_image()

def export_annotations():
    global annotations, output_dir
    
    if not annotations:
        messagebox.showwarning("Warning", "No annotations to export")
        return
    
    try:
        cleanup_output_dir(output_dir)
        export_to_coco(annotations, output_dir)
        export_to_yolo(annotations, output_dir)
        export_to_pascal(annotations, output_dir)
        messagebox.showinfo("Success", f"Annotations exported to {output_dir}")
    except Exception as e:
        messagebox.showerror("Error", f"Export failed: {str(e)}")

def update_progress_bar():
    if progress_var and image_paths:
        annotated_count = len(annotations)
        total_count = len(image_paths)
        progress = (annotated_count / total_count) * 100
        progress_var.set(progress)

def update_sidebar_info():
    if not hasattr(update_sidebar_info, 'labels'):
        return
    
    labels = update_sidebar_info.labels
    
    if image_paths:
        labels['current'].config(text=f"{current_index + 1} of {len(image_paths)}")
        labels['filename'].config(text=os.path.basename(image_paths[current_index]))
        
        total_annotations = sum(len(ann['objects']) for ann in annotations.values())
        labels['total_objects'].config(text=str(total_annotations))
        labels['annotated_images'].config(text=str(len(annotations)))

def update_object_list():
    if object_listbox:
        object_listbox.delete(0, END)
        if current_index in annotations:
            for i, obj in enumerate(annotations[current_index]['objects']):
                object_listbox.insert(END, f"{i+1}. {obj['class']}")

def setup_gui():
    global canvas, control_frame, info_frame, sidebar_frame, pro, progress_var, object_listbox
    
    pro = Tk()
    pro.title("Image Annotator - Professional Edition")
    pro.geometry("1200x800")
    pro.configure(bg=COLORS['background'])
    pro.minsize(1000, 700)
    
    # Configure style
    style = ttk.Style()
    style.theme_use('clam')
    
    # Main container
    main_container = Frame(pro, bg=COLORS['background'])
    main_container.pack(fill=BOTH, expand=True, padx=10, pady=10)
    
    # Top toolbar
    toolbar = Frame(main_container, bg=COLORS['white'], relief=SOLID, bd=1, height=60)
    toolbar.pack(fill=X, pady=(0, 10))
    toolbar.pack_propagate(False)
    
    # Toolbar content
    toolbar_left = Frame(toolbar, bg=COLORS['white'])
    toolbar_left.pack(side=LEFT, fill=Y, padx=20, pady=10)
    
    Label(toolbar_left, text="🖼️ Image Annotator", font=("Segoe UI", 16, "bold"), bg=COLORS['white'], fg=COLORS['text_dark']).pack(side=LEFT)
    
    toolbar_right = Frame(toolbar, bg=COLORS['white'])
    toolbar_right.pack(side=RIGHT, fill=Y, padx=20, pady=10)
    
    # Progress bar
    progress_frame = Frame(toolbar_right, bg=COLORS['white'])
    progress_frame.pack(side=RIGHT, padx=(0, 20))
    
    Label(progress_frame, text="Progress:", font=("Segoe UI", 9), bg=COLORS['white'], fg=COLORS['text_light']).pack()
    
    progress_var = DoubleVar()
    progress_bar = ttk.Progressbar(progress_frame, variable=progress_var, length=150, mode='determinate')
    progress_bar.pack()
    
    # Main content area
    content_container = Frame(main_container, bg=COLORS['background'])
    content_container.pack(fill=BOTH, expand=True)
    
    # Sidebar
    sidebar_frame = Frame(content_container, bg=COLORS['sidebar'], width=250, relief=SOLID, bd=1)
    sidebar_frame.pack(side=RIGHT, fill=Y, padx=(10, 0))
    sidebar_frame.pack_propagate(False)
    
    # Sidebar content
    sidebar_title = Label(sidebar_frame, text="📊 Statistics", font=("Segoe UI", 12, "bold"), bg=COLORS['sidebar'], fg=COLORS['text_dark'])
    sidebar_title.pack(pady=(20, 10), padx=20, anchor=W)
    
    # Info labels
    info_labels = {}
    
    info_items = [
        ("Current Image:", "current", "1 of 0"),
        ("Filename:", "filename", "No image"),
        ("Total Objects:", "total_objects", "0"),
        ("Annotated Images:", "annotated_images", "0")
    ]
    
    for label_text, key, default in info_items:
        frame = Frame(sidebar_frame, bg=COLORS['sidebar'])
        frame.pack(fill=X, padx=20, pady=2)
        
        Label(frame, text=label_text, font=("Segoe UI", 9), bg=COLORS['sidebar'], fg=COLORS['text_light']).pack(anchor=W)
        
        info_labels[key] = Label(frame, text=default, font=("Segoe UI", 10, "bold"), 
                                bg=COLORS['sidebar'], fg=COLORS['text_dark'])
        info_labels[key].pack(anchor=W)
    
    update_sidebar_info.labels = info_labels
    
    # Objects in current image
    Label(sidebar_frame, text="📦 Objects in Image", font=("Segoe UI", 12, "bold"), bg=COLORS['sidebar'], fg=COLORS['text_dark']).pack(pady=(20, 10), padx=20, anchor=W)
    
    object_frame = Frame(sidebar_frame, bg=COLORS['sidebar'])
    object_frame.pack(fill=BOTH, expand=True, padx=20, pady=(0, 20))
    
    object_scrollbar = Scrollbar(object_frame)
    object_scrollbar.pack(side=RIGHT, fill=Y)
    
    object_listbox = Listbox(object_frame, yscrollcommand=object_scrollbar.set,font=("Segoe UI", 9), bg=COLORS['white'], relief=SOLID, bd=1, selectmode=SINGLE)
    object_listbox.pack(side=LEFT, fill=BOTH, expand=True)
    object_scrollbar.config(command=object_listbox.yview)
    
    canvas_container = Frame(content_container, bg=COLORS['white'], relief=SOLID, bd=1)
    canvas_container.pack(side=LEFT, fill=BOTH, expand=True)
    
    canvas = Canvas(canvas_container, bg="white", cursor="crosshair")
    canvas.pack(expand=True, fill=BOTH, padx=20, pady=20)
    
    control_frame = Frame(main_container, bg=COLORS['white'], relief=SOLID, bd=1, height=80)
    control_frame.pack(fill=X, pady=(10, 0))
    control_frame.pack_propagate(False)
    
    button_config = {
        'font': ("Segoe UI", 10, "bold"),
        'relief': FLAT,
        'padx': 25,
        'pady': 10,
        'cursor': 'hand2'
    }
    
    left_buttons = Frame(control_frame, bg=COLORS['white'])
    left_buttons.pack(side=LEFT, fill=Y, padx=20, pady=15)
    
    Button(left_buttons, text="📁 Load Images", command=lambda: load_images_and_show(),
           bg=COLORS['primary'], fg='white', **button_config).pack(side=LEFT, padx=(0, 10))
    
    Button(left_buttons, text="⬅️ Previous", command=prev_image,
           bg=COLORS['secondary'], fg='white', **button_config).pack(side=LEFT, padx=5)
    
    Button(left_buttons, text="Next ➡️", command=next_image,
           bg=COLORS['secondary'], fg='white', **button_config).pack(side=LEFT, padx=5)
    
    right_buttons = Frame(control_frame, bg=COLORS['white'])
    right_buttons.pack(side=RIGHT, fill=Y, padx=20, pady=15)
    
    Button(right_buttons, text="🗑️ Delete Last", command=delete_last_annotation,
           bg=COLORS['warning'], fg='white', **button_config).pack(side=RIGHT, padx=(10, 0))
    
    Button(right_buttons, text="💾 Export All", command=export_annotations,
           bg=COLORS['success'], fg='white', **button_config).pack(side=RIGHT, padx=5)
    
    canvas.bind("<ButtonPress-1>", on_mouse_down)
    canvas.bind("<B1-Motion>", on_mouse_drag)
    canvas.bind("<ButtonRelease-1>", on_mouse_up)
    
    pro.bind('<Left>', lambda e: prev_image())
    pro.bind('<Right>', lambda e: next_image())
    pro.bind('<Delete>', lambda e: delete_last_annotation())
    pro.bind('<Control-s>', lambda e: export_annotations())
    pro.bind('<Control-o>', lambda e: load_images_and_show())
    
    return pro

def load_images_and_show():
    if load_image_paths():
        show_current_image()

def main():
    pro = setup_gui()
    
    welcome_text = """
Welcome to Image Annotator Professional!

Instructions:
• Click 'Load Images' to select a folder
• Draw rectangles around objects
• Use arrow keys or buttons to navigate
• Press Delete to remove last annotation
• Ctrl+S to export, Ctrl+O to load new folder

Ready to start annotating!
"""
    
    canvas.create_text(400, 300, text=welcome_text, anchor="center", font=("Segoe UI", 12), fill=COLORS['text_light'], width=600)
    pro.mainloop()

if __name__ == "__main__":
    main()