'''
This code file is the console and implementation of the Web(the index.html file in the templates folder) 
If you want to run the web demo, please run this file directly:
Input the command `python app.py` in the terminal.
Then open your browser and visit `http://127.0.0.1:5000/`
Then you could see the Web.
'''

# ===== Developers =====
# 31808397_Shen Ruiting finished the Basic GUI/Website Interactivity and Visualization.
# 31808636_Zhang Enze finished Presentation and Visualisation.
# 31808395_Shen Fangjie designed Testing and Demonstration.


# ===== Imports =====
from flask import Flask, render_template, request
import tkinter as tk
from tkinter import messagebox, colorchooser, ttk
from PIL import Image, ImageTk
from qr_generator_version1 import qr_img as qr_img_v1
from qr_generator_version2 import qr_img as qr_img_v2
from qr_generator_version2 import generate_qr_code2, generate_step_images
import qr_generator_version2
import io
import base64

# ===== Flask App Initialization and Global Variables =====
app = Flask(__name__)

# Step descriptions for QR code construction process (for web demo)
STEP_DESCRIPTIONS = [
    "Step 1: Add Finder Patterns<br><b>Explanation:</b> Finder patterns are the large black-and-white squares at three corners of the QR code. They help scanners quickly locate and orient the code, ensuring it can be read from any angle. Each finder pattern consists of a 7x7 square with a specific arrangement of black and white modules.",
    "Step 2: Add Alignment Pattern<br><b>Explanation:</b> The alignment pattern is a smaller square, present in version 2 and above, usually near the bottom right. It helps correct for distortion when the QR code is bent or viewed at an angle, improving error tolerance and scanning reliability.",
    "Step 3: Add Format Information<br><b>Explanation:</b> Format information encodes the error correction level and mask pattern used. It is placed near the finder patterns and is essential for the scanner to correctly decode the QR code, even if part of the code is damaged.",
    "Step 4: Fill Data Bits<br><b>Explanation:</b> The actual data (your input text) is encoded into binary and placed into the QR matrix following a zigzag pattern. This step also includes error correction codes, ensuring the QR code can be read even if partially obscured.",
    "Step 5: Apply Masking<br><b>Explanation:</b> Masking modifies the QR code's modules using one of eight patterns to avoid problematic patterns (like large blocks of the same color) that could confuse scanners. The best mask is chosen based on penalty scores to maximize readability and robustness."
]

# ===== Web: Helper Functions =====
def get_step_images_and_desc(input_text, color="#000000", background="#ffffff", scale=10, mask_id=0):
    """
    Generate step-by-step images and descriptions for QR code construction.
    Returns a list of (base64 image, description) tuples.
    """
    images = generate_step_images(
        input_text, color=color, background=background, scale=scale, mask_id=mask_id
    )
    img_b64_list = []
    for img in images:
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        img_b64 = base64.b64encode(buf.getvalue()).decode("ascii")
        img_b64_list.append(img_b64)
    return list(zip(img_b64_list, STEP_DESCRIPTIONS))

# ===== Web: Route Definitions =====
@app.route('/')
def home():
    """
    Home page route. Shows the main interface and optionally the QR construction steps.
    """
    active_section = request.args.get('section', 'version2')
    step_images = None
    if active_section == 'principle':
        # Default content for process demo
        step_images = get_step_images_and_desc("Hello QR!", "#000000", "#ffffff", 10, 0)
    return render_template('index.html', active_section=active_section, step_images=step_images)

@app.route('/generate', methods=['POST'])
def generate_qr():
    """
    Handle QR code generation requests from the web form.
    Supports version 1, version 2, and principle (step demo) sections.
    """
    active_section = request.form.get('active_section', 'version2')
    input_text = request.form.get('text')
    show_masks = request.form.get('show_masks') == '1'

    if not input_text:
        return render_template('index.html',
                               error="Please input URL or Text.",
                               active_section=active_section)

    try:
        if active_section == 'version1':
            # Generate QR code using version 1 algorithm
            qr_image = qr_img_v1(input_text, debug=True)
            buffered = io.BytesIO()
            qr_image.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode("ascii")
            return render_template('index.html',
                                   qr_image=img_str,
                                   input_text=input_text,
                                   active_section=active_section,
                                   form_data=request.form)  # Ensure version1 passes form_data

        elif active_section == 'version2':
            # Generate QR code using version 2 algorithm with style options
            params = {
                'color': request.form.get('color', '#000000'),
                'background': request.form.get('background', '#ffffff'),
                'scale': int(request.form.get('scale', 10)),
                'border_width': int(request.form.get('border_width', 4)),
                'border_color': request.form.get('border_color', '#000000'),
                'gradient_type': request.form.get('gradient_type', 'none'),
                'gradient_colors': [
                    request.form.get('gradient_color1', '#FF0000'),
                    request.form.get('gradient_color2', '#0000FF')
                ]
            }
            mask_images, mask_scores, best_mask, version_info = generate_qr_code2(
                input_text,
                return_version=True,
                **params
            )

            # Only show the best mask QR code
            buffered = io.BytesIO()
            mask_images[best_mask].save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode("ascii")

            # Show all masks and scores if requested
            masks_data = []
            if show_masks:
                for idx, (img, score) in enumerate(zip(mask_images, mask_scores)):
                    buf = io.BytesIO()
                    img.save(buf, format="PNG")
                    img_b64 = base64.b64encode(buf.getvalue()).decode("ascii")
                    masks_data.append({
                        'img': img_b64,
                        'score': sum(score),
                        'idx': idx,
                        'is_best': (idx == best_mask)
                    })

            return render_template(
                'index.html',
                qr_image=img_str,
                input_text=input_text,
                active_section=active_section,
                form_data=request.form,
                data_length=len(input_text.encode('utf-8')),
                qr_version=version_info,
                masks_data=masks_data if show_masks else None,
                show_masks=show_masks
            )

        elif active_section == 'principle':
            # Support custom input for process steps demo
            color = request.form.get('color', '#000000')
            background = request.form.get('background', '#ffffff')
            scale = int(request.form.get('scale', 10))
            step_images = get_step_images_and_desc(input_text, color, background, scale, 0)
            return render_template('index.html',
                                   active_section=active_section,
                                   input_text=input_text,
                                   step_images=step_images)

    except Exception as e:
        # Handle errors and display error message on the web page
        return render_template('index.html',
                               error=f"Failure: {str(e)}",
                               active_section=active_section)

@app.route('/process_steps', methods=['POST'])
def process_steps():
    """
    Handle AJAX requests for step-by-step QR code construction images.
    Returns only the current step image and description.
    """
    input_text = request.form.get('text', 'Hello QR!')
    color = request.form.get('color', '#000000')
    background = request.form.get('background', '#ffffff')
    scale = int(request.form.get('scale', 10))
    step = int(request.form.get('step', 0))  # Current step index
    step_images = get_step_images_and_desc(input_text, color, background, scale, 0)
    # Only return the current step
    if step < 0: step = 0
    if step >= len(step_images): step = len(step_images) - 1
    current_img, current_desc = step_images[step]
    return render_template('index.html',
                           active_section='principle',
                           input_text=input_text,
                           step_img=current_img,
                           step_desc=current_desc,
                           step=step,
                           total_steps=len(step_images),
                           color=color,
                           background=background,
                           scale=scale)

# ===== Desktop GUI Code (Mainly for Demo, Web is the Main Presentation) =====

class QRCodeGUI:
    """
    Simple desktop GUI for QR code generation (version 1).
    """
    def __init__(self, root):
        self.root = root
        self.root.title("QR Code Generator")

        self.label = tk.Label(root, text="Enter URL or Text:")
        self.label.pack()

        self.entry = tk.Entry(root, width=50)
        self.entry.pack()

        self.gen_btn = tk.Button(root, text="Generate QR Code", command=self.gen_qr)
        self.gen_btn.pack()

        self.image_label = tk.Label(root)
        self.image_label.pack()

        self.warning_label = tk.Label(
            root,
            text="Warning: Do not scan QR codes from unknown sources to avoid phishing and other security risks.",
            fg="red",
            wraplength=400,
            justify="center"
        )
        self.warning_label.pack()

    def gen_qr(self):
        """
        Generate QR code and display in the GUI.
        """
        input_string = self.entry.get()

        if not input_string:
            messagebox.showerror("Error", "Please enter a URL or text.")
            return

        try:
            # Generate QR code image using the generator module
            qr_image = qr_img_v1(input_string, debug=True)
            img_tk = ImageTk.PhotoImage(qr_image)
            self.image_label.config(image=img_tk)
            self.image_label.image = img_tk  # Prevent image from being garbage collected
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate QR code: {e}")


class QRCodeGeneratorGUI:
    """
    Advanced desktop GUI for QR code generation (version 2, with style options).
    """
    def __init__(self, root):
        self.root = root
        self.root.title("QR Code Generator")
        self.root.geometry("800x600")
        self.root.minsize(420, 520)

        # Input area
        input_frame = ttk.Frame(root)
        input_frame.pack(pady=10, fill=tk.X)

        ttk.Label(input_frame, text="Enter URL or Text:").grid(row=0, column=0, sticky="e")
        self.entry = ttk.Entry(input_frame, width=40)
        self.entry.grid(row=0, column=1, columnspan=3, padx=5, pady=2)

        # Color settings
        ttk.Label(input_frame, text="QR Color:").grid(row=1, column=0, sticky="e")
        self.color_var = tk.StringVar(value="#000000")
        self.color_entry = ttk.Entry(input_frame, textvariable=self.color_var, width=10)
        self.color_entry.grid(row=1, column=1, pady=2)
        ttk.Button(input_frame, text="Pick", command=self.pick_color).grid(row=1, column=2, padx=2)

        ttk.Label(input_frame, text="Background:").grid(row=1, column=3, sticky="e")
        self.bg_var = tk.StringVar(value="#ffffff")
        self.background_entry = ttk.Entry(input_frame, textvariable=self.bg_var, width=10)
        self.background_entry.grid(row=1, column=4, pady=2)
        ttk.Button(input_frame, text="Pick", command=self.pick_bg_color).grid(row=1, column=5, padx=2)

        ttk.Label(input_frame, text="Scale:").grid(row=2, column=0, sticky="e")
        self.scale_var = tk.IntVar(value=10)
        ttk.Spinbox(input_frame, from_=2, to=20, textvariable=self.scale_var, width=5).grid(row=2, column=1, pady=2)

        # Style control area
        style_frame = ttk.Frame(root)
        style_frame.pack(pady=5, fill=tk.X)

        ttk.Label(style_frame, text="border width:").grid(row=0, column=0, sticky="e")
        self.border_var = tk.IntVar(value=4)
        ttk.Spinbox(style_frame, from_=0, to=20, textvariable=self.border_var, width=5).grid(row=0, column=1, padx=2)

        ttk.Label(style_frame, text="border color:").grid(row=0, column=2, sticky="e")
        self.border_color_var = tk.StringVar(value="#000000")
        self.border_color_entry = ttk.Entry(style_frame, textvariable=self.border_color_var, width=10)
        self.border_color_entry.grid(row=0, column=3, padx=2)
        ttk.Button(style_frame, text="Pick", command=self.pick_border_color).grid(row=0, column=4, padx=2)

        # Gradient type
        ttk.Label(style_frame, text="Gradient type:").grid(row=1, column=0, sticky="e")
        self.gradient_type = tk.StringVar(value="none")
        ttk.Combobox(style_frame, textvariable=self.gradient_type,
                     values=["none", "linear", "radial"], width=8).grid(row=1, column=1, columnspan=2)

        ttk.Label(style_frame, text="graduated color:").grid(row=1, column=3, sticky="e")
        self.gradient_colors = ttk.Entry(style_frame, width=15)
        self.gradient_colors.insert(0, "#FF0000,#0000FF")
        self.gradient_colors.grid(row=1, column=4, padx=2)
        ttk.Button(style_frame, text="Pick1", command=self.pick_gradient_color1).grid(row=1, column=5, padx=2)
        ttk.Button(style_frame, text="Pick2", command=self.pick_gradient_color2).grid(row=1, column=6, padx=2)

        # Info area
        self.info_label = ttk.Label(root, text="Data length: 0 bytes | Current version: 2")
        self.info_label.pack(pady=5)

        # Button area (horizontal)
        button_frame = ttk.Frame(root)
        button_frame.pack(pady=10)
        self.generate_button = ttk.Button(button_frame, text="Generate QR Code", command=self.generate_qr)
        self.generate_button.pack(side=tk.LEFT, padx=10)
        self.show_masks_btn = ttk.Button(button_frame, text="Display all masks and scores", command=self.show_all_masks)
        self.show_masks_btn.pack(side=tk.LEFT, padx=10)
        self.reset_button = ttk.Button(button_frame, text="Restore Color Option", command=self.reset_colors)
        self.reset_button.pack(side=tk.LEFT, padx=10)
        # Preview area
        self.image_label = ttk.Label(root)
        self.image_label.pack(pady=10)

        # Warning info
        self.warning_label = ttk.Label(
            root,
            text="Warning: Do not scan QR codes from unknown sources to avoid phishing and other security risks.",
            foreground="red",
            wraplength=400,
            justify="center"
        )
        self.warning_label.pack(pady=5)

    def pick_color(self):
        """
        Open color picker for QR color.
        """
        color = colorchooser.askcolor(title="Pick QR Color")
        if color[1]:
            self.color_var.set(color[1])

    def pick_bg_color(self):
        """
        Open color picker for background color.
        """
        color = colorchooser.askcolor(title="Pick Background Color")
        if color[1]:
            self.bg_var.set(color[1])

    def pick_border_color(self):
        """
        Open color picker for border color.
        """
        color = colorchooser.askcolor(title="Pick Border Color")
        if color[1]:
            self.border_color_var.set(color[1])

    def pick_gradient_color1(self):
        """
        Open color picker for gradient start color.
        """
        color = colorchooser.askcolor(title="Pick Gradient Start Color")
        if color[1]:
            colors = self.gradient_colors.get().split(",")
            if len(colors) == 2:
                self.gradient_colors.delete(0, tk.END)
                self.gradient_colors.insert(0, f"{color[1]},{colors[1].strip()}")
            else:
                self.gradient_colors.delete(0, tk.END)
                self.gradient_colors.insert(0, f"{color[1]},#0000FF")

    def pick_gradient_color2(self):
        """
        Open color picker for gradient end color.
        """
        color = colorchooser.askcolor(title="Pick Gradient End Color")
        if color[1]:
            colors = self.gradient_colors.get().split(",")
            if len(colors) == 2:
                self.gradient_colors.delete(0, tk.END)
                self.gradient_colors.insert(0, f"{colors[0].strip()},{color[1]}")
            else:
                self.gradient_colors.delete(0, tk.END)
                self.gradient_colors.insert(0, f"#FF0000,{color[1]}")

    def generate_qr(self):
        """
        Generate QR code with current style settings and display in GUI.
        """
        input_string = self.entry.get()
        color = self.color_var.get()
        background = self.bg_var.get()
        scale = self.scale_var.get()
        border_width = self.border_var.get()
        border_color = self.border_color_var.get()
        gradient_type = self.gradient_type.get()
        gradient_colors = [c.strip() for c in self.gradient_colors.get().split(",")]

        if not input_string:
            messagebox.showerror("Error", "Please enter a URL or text.")
            return

        try:
            data_bytes = input_string.encode('utf-8')
            data_length = len(data_bytes)

            mask_images, mask_scores, best_mask, actual_version = qr_generator_version2.generate_qr_code2(
                input_string,
                color=color,
                background=background,
                scale=scale,
                border_width=border_width,
                border_color=border_color,
                gradient_type=gradient_type,
                gradient_colors=gradient_colors,
                return_version=True
            )

            self.info_label.config(
                text=f"data length: {data_length} bytes | current version: {actual_version}"
            )

            img = mask_images[best_mask]
            img_tk = ImageTk.PhotoImage(img)
            self.image_label.config(image=img_tk)
            self.image_label.image = img_tk

        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate QR code: {e}")

    def show_all_masks(self):
        """
        Display all mask patterns and their penalty scores in a popup window.
        """
        input_string = self.entry.get()
        color = self.color_var.get()
        background = self.bg_var.get()
        scale = self.scale_var.get()
        border_width = self.border_var.get()
        border_color = self.border_color_var.get()
        gradient_type = self.gradient_type.get()
        gradient_colors = [c.strip() for c in self.gradient_colors.get().split(",")]

        if not input_string:
            messagebox.showerror("Error", "Please enter a URL or text.")
            return

        try:
            mask_images, mask_scores, best_mask, actual_version = qr_generator_version2.generate_qr_code2(
                input_string,
                color=color,
                background=background,
                scale=scale,
                border_width=border_width,
                border_color=border_color,
                gradient_type=gradient_type,
                gradient_colors=gradient_colors,
                return_version=True
            )
            # Popup display
            win = tk.Toplevel(self.root)
            win.title("All Masks and Scores (Best Mask Highlighted)")
            for i, (img, scores) in enumerate(zip(mask_images, mask_scores)):
                img_tk = ImageTk.PhotoImage(img.resize((120, 120), Image.NEAREST))
                frame = ttk.Frame(win, borderwidth=2, relief="solid" if i == best_mask else "flat")
                frame.grid(row=i // 4, column=i % 4, padx=5, pady=5)
                label = ttk.Label(frame, image=img_tk)
                label.image = img_tk
                label.pack()
                score_str = f"Mask {i}\nScore: {sum(scores)} (R1:{scores[0]} R2:{scores[1]} R3:{scores[2]} R4:{scores[3]})"
                ttk.Label(frame, text=score_str, foreground="red" if i == best_mask else "black").pack()
            # Slideshow button
            step_button = ttk.Button(win, text="Show QR Construction Steps",
                                     command=lambda: self.show_steps(win, input_string, color, background, scale,
                                                                     best_mask))
            step_button.grid(row=2, column=0, columnspan=4, pady=10)
            win.grab_set()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to display masks: {e}")

    def show_steps(self, mask_window, input_string, color, background, scale, best_mask):
        """
        Show a slideshow of QR code construction steps for the selected mask.
        """
        mask_window.destroy()
        step_images = qr_generator_version2.generate_step_images(
            input_string, color=color, background=background, scale=scale, mask_id=best_mask
        )
        step_titles = [
            "Step 1: Finder Patterns",
            "Step 2: Finder + Alignment Patterns",
            "Step 3: Finder + Alignment + Data Bits",
            "Step 4: Final QR Code (Masked)"
        ]
        slide_window = tk.Toplevel(self.root)
        slide_window.title("QR Code Construction Slideshow")
        slide_frame = ttk.Frame(slide_window)
        slide_frame.pack(padx=10, pady=10)
        img_label = ttk.Label(slide_frame)
        img_label.pack()
        title_label = ttk.Label(slide_frame, font=("Arial", 14))
        title_label.pack(pady=5)
        state = {'idx': 0}
        img_tk_list = [ImageTk.PhotoImage(img.resize((300, 300), Image.NEAREST)) for img in step_images]

        def update_slide():
            idx = state['idx']
            img_label.config(image=img_tk_list[idx])
            img_label.image = img_tk_list[idx]
            title_label.config(text=step_titles[idx])

        def prev_slide():
            if state['idx'] > 0:
                state['idx'] -= 1
                update_slide()

        def next_slide():
            if state['idx'] < len(step_images) - 1:
                state['idx'] += 1
                update_slide()

        btn_frame = ttk.Frame(slide_window)
        btn_frame.pack(pady=10)
        prev_btn = ttk.Button(btn_frame, text="Previous", command=prev_slide)
        prev_btn.grid(row=0, column=0, padx=5)
        next_btn = ttk.Button(btn_frame, text="Next", command=next_slide)
        next_btn.grid(row=0, column=1, padx=5)

        update_slide()

    # Restore colors to default values
    def reset_colors(self):
        self.color_var.set("#000000")
        self.bg_var.set("#ffffff")
        self.border_color_var.set("#000000")
        self.gradient_type.set("none")
        self.gradient_colors.delete(0, tk.END)
        self.gradient_colors.insert(0, "#FF0000,#0000FF")

# ===== Main Entry Point =====
if __name__ == '__main__':
    # Start Flask web server
    app.run(debug=True)

    # To start the desktop GUI, run the following code separately
    # root = tk.Tk()
    # app_gui = QRCodeGeneratorGUI(root)
    # root.mainloop()