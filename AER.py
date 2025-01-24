import os
import glob
import subprocess
import customtkinter as ctk
from tkinter import filedialog
import threading
import queue
import signal
import psutil

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

# Add this function after detect_aerender_versions()
def get_system_memory():
    """Get total system memory in GB"""
    return round(psutil.virtual_memory().total / (1024.0 ** 3), 1)

# Add these global variables after imports
render_process = None
is_paused = False

# Function to run aerender
def render_aep():
    global render_process
    aerender_path = aerender_var.get()
    aep_file = aep_path_var.get()

    if not aerender_path:
        status_label.configure(text="Error: Select aerender first!", text_color="red")
        return
    if not aep_file:
        status_label.configure(text="Error: Select an AEP file first!", text_color="red")
        return

    # Disable/enable appropriate buttons
    render_button.configure(state="disabled")
    stop_button.configure(state="normal")
    pause_button.configure(state="normal")
    output_text.delete(1.0, ctk.END)
    status_label.configure(text="Rendering...", text_color="#ffff00")

    def render_thread():
        global render_process
        memory_limit = str(memory_var.get())
        cmd = f'"{aerender_path}" -project "{aep_file}" -mem_usage {memory_limit} {memory_limit}'
        
        render_process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, 
                                        stderr=subprocess.STDOUT, universal_newlines=True)
        
        while True:
            output = render_process.stdout.readline()
            if output == '' and render_process.poll() is not None:
                break
            if output:
                output_queue.put(output.strip())
                root.event_generate('<<NewOutput>>')

        return_code = render_process.poll()
        
        if return_code == 0:
            status_queue.put(("Render successful!", "#00ff00"))
        else:
            status_queue.put(("Render failed!", "#ff0000"))
        
        root.event_generate('<<RenderComplete>>')

    def update_output(event):
        while not output_queue.empty():
            line = output_queue.get()
            output_text.insert(ctk.END, line + "\n")
            output_text.see(ctk.END)

    def render_complete(event):
        global render_process
        status_text, status_color = status_queue.get()
        status_label.configure(text=status_text, text_color=status_color)
        render_button.configure(state="normal")
        stop_button.configure(state="disabled")
        pause_button.configure(state="disabled")
        pause_button.configure(text="Pause")
        render_process = None

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

def stop_render():
    global render_process
    if render_process:
        try:
            parent = psutil.Process(render_process.pid)
            children = parent.children(recursive=True)
            
            for child in children:
                child.terminate()
            
            render_process.terminate()
            
            status_label.configure(text="Render stopped!", text_color="#ff0000")
            render_button.configure(state="normal")
            stop_button.configure(state="disabled")
            pause_button.configure(state="disabled")
            pause_button.configure(text="Pause")
        except:
            pass

def toggle_pause():
    global render_process, is_paused
    if not render_process:
        return

    if is_paused:
        try:
            parent = psutil.Process(render_process.pid)
            parent.resume()
            for child in parent.children(recursive=True):
                child.resume()
            pause_button.configure(text="Pause")
            status_label.configure(text="Rendering...", text_color="#ffff00")
        except:
            pass
    else:
        try:
            parent = psutil.Process(render_process.pid)
            parent.suspend()
            for child in parent.children(recursive=True):
                child.suspend()
            pause_button.configure(text="Resume")
            status_label.configure(text="Render paused", text_color="#ffa500")
        except:
            pass
    
    is_paused = not is_paused

# GUI Setup
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# Window Setup
root = ctk.CTk()
root.title("skrtl-AER | 25 Jan 2025")
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

version_label = ctk.CTkLabel(header_frame, text="0.1.1", font=("Ubuntu", 12), text_color="#ffffff")
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

# Memory Usage Section
memory_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
memory_frame.pack(pady=5, padx=20)

total_ram = get_system_memory()
memory_label = ctk.CTkLabel(memory_frame, 
                           text=f"Maximum Memory Usage (%) - System RAM: {total_ram}GB", 
                           font=("Ubuntu", 14, "bold"), 
                           text_color="#ffffff")
memory_label.pack(pady=(0, 5))

memory_var = ctk.IntVar(value=75)
memory_slider = ctk.CTkSlider(memory_frame, from_=25, to=90, number_of_steps=65,
                             variable=memory_var, width=200)
memory_slider.pack(pady=5)

# Add after memory slider section
memory_info_frame = ctk.CTkFrame(memory_frame, fg_color="transparent")
memory_info_frame.pack(pady=(5, 0))

memory_info_high = ctk.CTkLabel(memory_info_frame, 
                               text="• High RAM (>75%): Faster render, higher risk of errors",
                               font=("Ubuntu", 11), 
                               text_color="#ff4444",
                               justify="left")
memory_info_high.pack(anchor="w")

memory_info_medium = ctk.CTkLabel(memory_info_frame, 
                                 text="• Medium RAM (50-75%): Balanced performance",
                                 font=("Ubuntu", 11), 
                                 text_color="#44ff44",
                                 justify="left")
memory_info_medium.pack(anchor="w")

memory_info_low = ctk.CTkLabel(memory_info_frame, 
                              text="• Low RAM (<50%): Slower render, more stable",
                              font=("Ubuntu", 11), 
                              text_color="#4444ff",
                              justify="left")
memory_info_low.pack(anchor="w")

def update_memory_label(*args):
    ram_usage = (memory_var.get() / 100.0) * total_ram
    memory_value_label.configure(text=f"{memory_var.get()}% ({round(ram_usage, 1)}GB)")
    
    # Update text colors based on memory usage with more contrast
    if memory_var.get() > 75:
        memory_value_label.configure(text_color="#ff4444")  # Merah lebih terang
    elif memory_var.get() > 50:
        memory_value_label.configure(text_color="#44ff44")  # Hijau lebih terang
    else:
        memory_value_label.configure(text_color="#4444ff")  # Biru lebih terang

memory_var.trace_add("write", update_memory_label)
memory_value_label = ctk.CTkLabel(memory_frame, text="75%", 
                                 font=("Ubuntu", 12), text_color="#ffffff")
memory_value_label.pack()
update_memory_label()  # Initial update

# File Selection Section
file_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
file_frame.pack(pady=10, padx=20)

aep_path_var = ctk.StringVar()

button_frame = ctk.CTkFrame(file_frame, fg_color="transparent")
button_frame.pack()

select_aep_button = ctk.CTkButton(button_frame, text="Select AEP", command=select_aep, font=("Ubuntu", 14, "bold"),
                                fg_color="#1a1a1a", text_color="#ffffff", hover_color="#2d2d2d", height=35, width=140,
                                corner_radius=8)
select_aep_button.pack(side="left", padx=3)

render_button = ctk.CTkButton(button_frame, text="Render", command=render_aep, font=("Ubuntu", 14, "bold"),
                            fg_color="#1a1a1a", text_color="#ffffff", hover_color="#2d2d2d", height=35, width=140,
                            corner_radius=8)
render_button.pack(side="left", padx=3)

# Add status label below the button frame
status_label = ctk.CTkLabel(file_frame, text="", font=("Ubuntu", 12), text_color="#ffffff")
status_label.pack(pady=(5, 0))

# Output Section
output_frame = ctk.CTkFrame(content_frame, fg_color="#1a1a1a", corner_radius=8)
output_frame.pack(fill="both", expand=True, pady=10, padx=20)

# Add a frame for log header and control buttons
log_header_frame = ctk.CTkFrame(output_frame, fg_color="transparent")
log_header_frame.pack(fill="x", padx=8, pady=(8,0))

log_label = ctk.CTkLabel(log_header_frame, text="Logs:", font=("Ubuntu", 12, "bold"), text_color="#ffffff")
log_label.pack(side="left")

# Add control buttons to the right side of log header
control_frame = ctk.CTkFrame(log_header_frame, fg_color="transparent")
control_frame.pack(side="right")

stop_button = ctk.CTkButton(control_frame, text="Stop", command=stop_render, font=("Ubuntu", 12, "bold"),
                         fg_color="#1a1a1a", text_color="#ffffff", hover_color="#2d2d2d", height=25, width=80,
                         corner_radius=8, state="disabled")
stop_button.pack(side="left", padx=3)

pause_button = ctk.CTkButton(control_frame, text="Pause", command=toggle_pause, font=("Ubuntu", 12, "bold"),
                          fg_color="#1a1a1a", text_color="#ffffff", hover_color="#2d2d2d", height=25, width=80,
                          corner_radius=8, state="disabled")
pause_button.pack(side="left", padx=3)

output_text = ctk.CTkTextbox(output_frame, font=("Consolas", 11), text_color="#ffffff", fg_color="#1a1a1a",
                            wrap="none", height=150)
output_text.pack(fill="both", expand=True, pady=8, padx=8)

# Run Application
root.mainloop()
