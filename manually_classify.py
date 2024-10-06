import os
import sys
import fitz
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk, ImageDraw
from utils import (extract_blocks, drop_to_file,)

class ManualClassifierGUI:
    def __init__(self, pdf_path, output_file="output.txt"):
        self.pdf_path = pdf_path
        self.output_file = output_file
        self.doc = fitz.open(self.pdf_path)
        self.total_pages = self.doc.page_count
        self.all_blocks = extract_blocks(self.pdf_path)
        self.total_blocks = len(self.all_blocks)
        self.current_index = 0
        self.classifications = []
        self.undo_stack = []
        self.pending_classification = None
        self.root = tk.Tk()
        self.root.title("Manual PDF Block Classifier")
        self.canvas = tk.Canvas(self.root, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.control_frame = tk.Frame(self.root)
        self.control_frame.pack(pady=10)
        self.button_texts = ["Header", "Body", "Footer", "Quote"]
        self.buttons = []
        for idx, text in enumerate(self.button_texts):
            btn = tk.Button(self.control_frame, text=text, width=6,
                            command=lambda i=idx: self.classify(i))
            btn.grid(row=0, column=idx, padx=1)
            self.buttons.append(btn)
        self.undo_button = tk.Button(self.control_frame, text="Undo", width=4, command=self.undo)
        self.undo_button.grid(row=0, column=len(self.button_texts), padx=1)
        self.status_var = tk.StringVar()
        self.status_var.set("Loading...")
        self.status_label = tk.Label(self.root, textvariable=self.status_var)
        self.status_label.pack(pady=5)
        self.load_current_block()
        self.root.bind('0', lambda event: self.classify(0))
        self.root.bind('1', lambda event: self.classify(1))
        self.root.bind('2', lambda event: self.classify(2))
        self.root.bind('3', lambda event: self.classify(3))
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.mainloop()

    def load_current_block(self):
        if self.current_index < 0 or self.current_index >= self.total_blocks:
            self.status_var.set("All blocks have been classified.")
            messagebox.showinfo("Completion", "All blocks have been classified.")
            self.root.quit()
            return
        block = self.all_blocks[self.current_index]
        page_number = block['page']  
        page = self.doc.load_page(page_number)
        zoom = 2    
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        mode = "RGB" if pix.alpha == 0 else "RGBA"
        img = Image.frombytes(mode, [pix.width, pix.height], pix.samples)
        x0, y0, x1, y1 = block['x0'], block['y0'], block['x1'], block['y1']
        x0_zoomed, y0_zoomed = x0 * zoom, y0 * zoom
        x1_zoomed, y1_zoomed = x1 * zoom, y1 * zoom
        draw = ImageDraw.Draw(img)
        draw.rectangle([x0_zoomed, y0_zoomed, x1_zoomed, y1_zoomed], outline="black", width=2)
        max_width, max_height = 1200, 800
        img_width, img_height = img.size
        scale = min(max_width / img_width, max_height / img_height, 1)
        new_size = (int(img_width * scale), int(img_height * scale))
        img = img.resize(new_size, Image.Resampling.LANCZOS)
        self.photo = ImageTk.PhotoImage(img)
        self.canvas.delete("all")  
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = new_size[0]
        window_height = new_size[1] + 100
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.status_var.set(f"Block {self.current_index + 1} of {self.total_blocks} (Page {page_number + 1})")

    def classify(self, label_idx):
        label = self.button_texts[label_idx]
        block = self.all_blocks[self.current_index]
        block_text = block['raw_block'][4]
        block_page_number = block['page']
        if self.pending_classification is not None:
            drop_to_file(self.pending_classification[0], self.pending_classification[1], self.pending_classification[2])
            self.undo_stack.append(self.pending_classification)
        self.pending_classification = (block_text, label, block_page_number)
        self.current_index += 1
        self.load_current_block()

    def undo(self):
        if self.pending_classification is not None:
            self.pending_classification = None
            self.current_index -= 1
            self.load_current_block()
            return
        if not self.undo_stack:
            messagebox.showwarning("Undo", "No actions to undo.")
            return
        last_classification = self.undo_stack.pop()
        self.current_index -= 1
        self.remove_last_line(self.output_file)
        self.load_current_block()
        def remove_last_line(self, filename):
            try:
                with open(filename, "rb+") as f:
                    f.seek(-1, os.SEEK_END)
                    while f.read(1) != b'\n' and f.tell() > 1:
                        f.seek(-2, os.SEEK_CUR)
                    if f.tell() > 1:
                        f.seek(-1, os.SEEK_CUR)
                    f.truncate()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to undo last action: {e}")

    def on_close(self):
        if self.pending_classification is not None:
            drop_to_file(self.pending_classification[0], self.pending_classification[1], self.pending_classification[2])
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.doc.close()
            self.root.destroy()
            sys.exit()

def main():
    file_name = input("File name: ")
    pdf_path = f"{file_name}.pdf"
    output_file = "output.txt"
    if not os.path.exists(pdf_path):
        print(f"PDF file '{pdf_path}' not found.")
        return
    open(output_file, "w", encoding='utf-8').close()
    gui = ManualClassifierGUI(pdf_path, output_file)
    print("Classification completed.")

if __name__ == "__main__":
    main()
