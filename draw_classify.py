import os
import fitz
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
from utils import extract_blocks, drop_to_file

class ManualClassifierGUI:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.doc = fitz.open(pdf_path)
        self.total_pages = self.doc.page_count
        self.all_blocks = extract_blocks(pdf_path)
        self.current_page = 0
        # For each block store the classification (or None if unclassified)
        self.block_classifications = [None] * len(self.all_blocks)
        self.current_label = 'Body'
        
        self.label_colors = {
            'Header': '#ff0000',
            'Body': '#00aaff',
            'Footer': '#0000ff',
            'Quote': '#ffff00',
            'Exclude': '#808080'
        }
        self.key_to_label = {
            'h': 'Header',
            'b': 'Body',
            'f': 'Footer',
            'q': 'Quote',
            'e': 'Exclude'
        }
        
        # GUI setup
        self.root = tk.Tk()
        self.root.title("Manual PDF Block Classifier")
        
        # Canvas for displaying the page image
        self.canvas = tk.Canvas(self.root, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Control panel for label selection and navigation
        self.control_frame = tk.Frame(self.root)
        self.control_frame.pack(pady=10, fill=tk.X)
        
        # Label buttons
        self.button_texts = ["Header", "Body", "Footer", "Quote", "Exclude"]
        self.buttons = []
        for idx, text in enumerate(self.button_texts):
            btn = tk.Button(
                self.control_frame,
                text=text,
                width=8,
                command=lambda t=text: self.set_current_label(t)
            )
            btn.grid(row=0, column=idx, padx=2)
            self.buttons.append(btn)
        
        # Next page button
        self.next_button = tk.Button(
            self.control_frame,
            text="Next Page",
            width=10,
            command=self.next_page,
            bg="#4CAF50",
            fg="white"
        )
        self.next_button.grid(row=0, column=len(self.button_texts), padx=10)
        
        # Status label
        self.status_var = tk.StringVar()
        self.status_label = tk.Label(self.root, textvariable=self.status_var, bg="white")
        self.status_label.pack(pady=5, fill=tk.X)
        
        # Event bindings
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.root.bind('<KeyPress>', self.on_key_press)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Rendering parameters
        self.zoom = 2
        self.scale = 1.0
        self.geometry_set = False
        
        self.load_current_page()
        self.root.mainloop()

    def set_current_label(self, label):
        self.current_label = label
        self.update_button_highlight()

    def load_current_page(self):
        if self.current_page >= self.total_pages:
            self.finish_classification()
            return

        page = self.doc.load_page(self.current_page)
        mat = fitz.Matrix(self.zoom, self.zoom)
        pix = page.get_pixmap(matrix=mat)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        
        # Calculate scaling for display
        max_width = self.root.winfo_screenwidth() * 0.8
        max_height = self.root.winfo_screenheight() * 0.8
        img_width, img_height = img.size
        self.scale = min(max_width / img_width, max_height / img_height, 1)
        new_size = (int(img_width * self.scale), int(img_height * self.scale))
        img = img.resize(new_size, Image.Resampling.LANCZOS)
        
        # Update canvas
        self.photo = ImageTk.PhotoImage(img)
        self.canvas.config(width=new_size[0], height=new_size[1])
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
        
        # Draw block outlines on current page in natural order
        for idx, block in enumerate(self.all_blocks):
            if block['page'] != self.current_page:
                continue
            zoomed_x0 = block['x0'] * self.zoom * self.scale
            zoomed_y0 = block['y0'] * self.zoom * self.scale
            zoomed_x1 = block['x1'] * self.zoom * self.scale
            zoomed_y1 = block['y1'] * self.zoom * self.scale
            outline_color = self.label_colors.get(self.block_classifications[idx], 'black')
            self.canvas.create_rectangle(
                zoomed_x0, zoomed_y0, zoomed_x1, zoomed_y1,
                outline=outline_color, fill="", width=2
            )
        
        if not self.geometry_set:
            window_height = new_size[1] + 120
            self.root.geometry(f"{new_size[0]}x{window_height}")
            self.geometry_set = True

        self.status_var.set(f"Page {self.current_page + 1} of {self.total_pages}")
        self.update_button_highlight()

    def on_canvas_click(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        pdf_x = x / (self.zoom * self.scale)
        pdf_y = y / (self.zoom * self.scale)
        # Identify the clicked block on the current page
        for idx, block in enumerate(self.all_blocks):
            if block['page'] != self.current_page:
                continue
            if block['x0'] <= pdf_x <= block['x1'] and block['y0'] <= pdf_y <= block['y1']:
                self.block_classifications[idx] = self.current_label
                self.load_current_page()
                break

    def on_key_press(self, event):
        key = event.keysym.lower()
        if key in self.key_to_label:
            self.set_current_label(self.key_to_label[key])

    def update_button_highlight(self):
        for btn in self.buttons:
            btn.config(relief=tk.SUNKEN if btn['text'] == self.current_label else tk.RAISED)

    def process_current_page(self):
        """Sort and write out the blocks on the current page in reading order."""
        page_blocks = [(idx, block) for idx, block in enumerate(self.all_blocks)
                       if block['page'] == self.current_page]
        page_blocks.sort(key=lambda tup: (tup[1]['y0'], tup[1]['x0']))
        for idx, block in page_blocks:
            classification = self.block_classifications[idx] or 'Exclude'
            drop_to_file(block['raw_block'][4], classification, block['page'])
    
    def next_page(self):
        self.process_current_page()
        self.current_page += 1
        if self.current_page >= self.total_pages:
            self.finish_classification()
        else:
            self.load_current_page()

    def finish_classification(self):
        if self.current_page < self.total_pages:
            self.process_current_page()
        messagebox.showinfo("Complete", "Classification saved successfully!")
        self.doc.close()
        self.root.quit()

    def on_close(self):
        self.root.destroy()

def main():
    file_name = input("Enter PDF file name (without extension): ").strip()
    pdf_path = f"{file_name}.pdf"
    if not os.path.exists(pdf_path):
        print(f"Error: File {pdf_path} not found!")
        return
    open("output.txt", "w", encoding='utf-8').close()
    ManualClassifierGUI(pdf_path)
    print("Classification saved to output.txt")

if __name__ == "__main__":
    main()

