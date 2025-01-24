import os
import glob
import subprocess
import customtkinter as ctk
from tkinter import filedialog
import threading
import queue

# Function to detect all After Effects versions
def detect_aerender_versions():
    common_paths = [
        r"C:\Program Files\Adobe\Adobe After Effects *\Support Files\aerender.exe",
        r"C:\Program Files (x86)\Adobe\Adobe After Effects *\Support Files\aerender.exe",
    ]
    aerender_versions = []
    for path_pattern in common_paths:
        for aerender_path in glob.glob(path_pattern):
            version = os.path.basename(os.path.dirname(os.path.dirname(aerender_path))).replace("Adobe After Effects ", "")
            aerender_versions.append((version, aerender_path))
    return aerender_versions

# Function to run aerender
def render_aep():
    aerender_path = aerender_var.get()
    aep_file = aep_path_var.get()

    if not aerender_path:
        status_label.configure(text="Error: Select aerender first!", text_color="red")
        return
    if not aep_file:
        status_label.configure(text="Error: Select an AEP file first!", text_color="red")
        return

    # Disable render button
    render_button.configure(state="disabled")
    output_text.delete(1.0, ctk.END)
    status_label.configure(text="Rendering...", text_color="yellow")

    def render_thread():
        cmd = f'"{aerender_path}" -project "{aep_file}"'
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                output_queue.put(output.strip())
                root.event_generate('<<NewOutput>>')

        return_code = process.poll()
        
        if return_code == 0:
            status_queue.put(("Render successful!", "green"))
        else:
            status_queue.put(("Error: Render failed!", "red"))
        
        root.event_generate('<<RenderComplete>>')

    def update_output(event):
        while not output_queue.empty():
            line = output_queue.get()
            output_text.insert(ctk.END, line + "\n")
            output_text.see(ctk.END)

    def render_complete(event):
        status_text, status_color = status_queue.get()
        status_label.configure(text=status_text, text_color=status_color)
        render_button.configure(state="normal")

    output_queue = queue.Queue()
    status_queue = queue.Queue()
    
    root.bind('<<NewOutput>>', update_output)
    root.bind('<<RenderComplete>>', render_complete)
    
    threading.Thread(target=render_thread, daemon=True).start()

# Function to select an AEP file from the folder
def select_aep():
    aep_file = filedialog.askopenfilename(title="Select AEP File", filetypes=[("After Effects Project", "*.aep")])
    if aep_file:
        aep_path_var.set(aep_file)
        status_label.configure(text=f"AEP file selected: {aep_file}", text_color="white")

# GUI Setup
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# Window Setup
root = ctk.CTk()
root.title("skrtl-AER | 24 Jan 2025")
root.geometry("800x600")
root.configure(bg="#1a1a1a")

# Main Container
main_container = ctk.CTkFrame(root, fg_color="#1a1a1a")
main_container.pack(pady=10, padx=20, fill="both", expand=True)

# Header Section
header_frame = ctk.CTkFrame(main_container, fg_color="#2d2d2d", corner_radius=10)
header_frame.pack(fill="x", pady=(0, 10))

title_label = ctk.CTkLabel(header_frame, text="AERender", font=("Ubuntu", 28, "bold"), text_color="#ffffff")
title_label.pack(pady=8)

version_label = ctk.CTkLabel(header_frame, text="0.1.0", font=("Ubuntu", 12), text_color="#ffffff")
version_label.pack(pady=(0,8))

# Content Section
content_frame = ctk.CTkFrame(main_container, fg_color="#2d2d2d", corner_radius=10)
content_frame.pack(fill="both", expand=True)

# Aerender Version Selection
aerender_versions = detect_aerender_versions()
if not aerender_versions:
    status_label = ctk.CTkLabel(content_frame, text="Error: No After Effects versions detected!", text_color="#ff4444", font=("Ubuntu", 14))
    status_label.pack(pady=10)
    root.mainloop()
    exit()

version_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
version_frame.pack(pady=10, padx=20)

aerender_var = ctk.StringVar(value=aerender_versions[0][1])
aerender_label = ctk.CTkLabel(version_frame, text="Select After Effects Version:", font=("Ubuntu", 14, "bold"), text_color="#ffffff")
aerender_label.pack(pady=(0, 5))

# Create dropdown for AE versions
version_options = [f"After Effects {version}" for version, _ in aerender_versions]
path_dict = {f"After Effects {version}": path for version, path in aerender_versions}

def on_version_select(choice):
    aerender_var.set(path_dict[choice])

version_dropdown = ctk.CTkOptionMenu(
    version_frame,
    values=version_options,
    command=on_version_select,
    font=("Ubuntu", 12),
    text_color="#ffffff",
    fg_color="#1a1a1a",
    button_color="#1a1a1a",
    button_hover_color="#2d2d2d",
    dropdown_fg_color="#1a1a1a",
    dropdown_hover_color="#2d2d2d",
    width=200
)
version_dropdown.set(version_options[0])
version_dropdown.pack(pady=5)

# File Selection Section
file_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
file_frame.pack(pady=10, padx=20)

aep_path_var = ctk.StringVar()

button_frame = ctk.CTkFrame(file_frame, fg_color="transparent")
button_frame.pack()

select_aep_button = ctk.CTkButton(button_frame, text="Select AEP", command=select_aep, font=("Ubuntu", 14, "bold"),
                                fg_color="#2980b9", text_color="#ffffff", hover_color="#3498db", height=35, width=140,
                                corner_radius=8)
select_aep_button.pack(side="left", padx=3)

render_button = ctk.CTkButton(button_frame, text="Render", command=render_aep, font=("Ubuntu", 14, "bold"),
                            fg_color="#27ae60", text_color="#ffffff", hover_color="#2ecc71", height=35, width=140,
                            corner_radius=8)
render_button.pack(side="left", padx=3)

# Status Section
status_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
status_frame.pack(fill="x", pady=(10, 3), padx=20)

status_label = ctk.CTkLabel(status_frame, text="", font=("Ubuntu", 12), text_color="#ffffff")
status_label.pack()

# Output Section
output_frame = ctk.CTkFrame(content_frame, fg_color="#1a1a1a", corner_radius=8)
output_frame.pack(fill="both", expand=True, pady=10, padx=20)

log_label = ctk.CTkLabel(output_frame, text="Logs:", font=("Ubuntu", 12, "bold"), text_color="#ffffff")
log_label.pack(anchor="w", padx=8, pady=(8,0))

output_text = ctk.CTkTextbox(output_frame, font=("Consolas", 11), text_color="#ffffff", fg_color="#1a1a1a",
                            wrap="none", height=150)
output_text.pack(fill="both", expand=True, pady=8, padx=8)

# Run Application
root.mainloop()