# Import necessary libraries
import customtkinter as ctk  # CustomTkinter for modern GUI
from PIL import Image  # Pillow for image handling
import os
import sys

# Install the CustomTkinter libraries if not already installed
# pip install customtkinter pillow

# Create the main application window
window = ctk.CTk()  # Initialize the main window
window.geometry("800x600")  # Set window size to 800x600 pixels
window.columnconfigure(0, weight=2)  # Configure column 0 to expand
window.columnconfigure(1, weight=1)  # Configure column 1 to expand

# Define a custom label class (currently empty, can be extended later)
class Ezlbl(ctk.CTkLabel):
    pass

def stop_now():
    """Restarts the program. This function is used to reset the program state by stopping
    the current process and starting a new one. This is useful when the program is stuck
    in an infinite loop or when the user wants to reset the program state."""
    
    print("Restarting the program...")
    os.execv(sys.executable, [sys.executable] + sys.argv)

def exit_program():
    """Exits the program gracefully. This function is 
    used to stop the program when the user is done using it. 
    It will print a message and then exit the program with a 
    status code of 0, indicating a successful termination."""

    print("Exiting the program. Goodbye!")
    sys.exit(0)  # 0 indicates a successful termination

# Create a frame for the webcam window
frame_1 = ctk.CTkFrame(window, fg_color="#B3B792")  # Frame with a custom background color
frame_1.rowconfigure(0, weight=2)  # Configure row 0 to expand
frame_1.grid(row=0, column=0, columnspan=2, rowspan=2, padx=10, pady=10, sticky="nswe")  # Place the frame in the window
frame_1.columnconfigure(0, weight=1)  # Configure column 0 to expand
frame_1.columnconfigure(1, weight=1)  # Configure column 1 to expand

# Create a sub-frame for displaying the webcam feed or image
frame_1_1 = ctk.CTkFrame(frame_1, fg_color="#000")  # Sub-frame with black background
frame_1_1.grid(row=0, column=0, padx=10, pady=10, sticky="nswe")  # Place the sub-frame in frame_1

# Calculate the width and height for the image display
width = frame_1_1.winfo_width() - 50
height = frame_1_1.winfo_height() - 50

# Load the first image using Pillow and create a CTkImage object
ctk_image_1 = ctk.CTkImage(light_image=Image.open("mango.jpg"), size=(300, 400))  # Load and resize the image
image_lbl_1 = ctk.CTkLabel(frame_1_1, image=ctk_image_1, text="mango")  # Create a label to display the image
image_lbl_1.pack(fill="both", expand=True)  # Pack the label to fill the sub-frame

# Load the second image using Pillow and create a CTkImage object
ctk_image_2 = ctk.CTkImage(light_image=Image.open("mango.jpg"), size=(300, 400))  # Load and resize the second image
image_lbl_2 = ctk.CTkLabel(frame_1_1, image=ctk_image_2, text="mango")  # Create a label to display the second image
image_lbl_2.pack(fill="both", expand=True)  # Pack the label to fill the sub-frame

# Create another sub-frame for displaying mango details
frame_1_2 = ctk.CTkFrame(frame_1, fg_color="transparent")  # Transparent sub-frame
frame_1_2.grid(row=0, column=1, padx=10, pady=10, sticky="nswe")  # Place the sub-frame in frame_1
frame_1_2.columnconfigure(0, weight=1)  # Configure column 0 to expand
frame_1_2.columnconfigure(1, weight=1)  # Configure column 1 to expand

# Add labels for mango details
details_lbl = ctk.CTkLabel(frame_1_2, text="Mango Details", text_color="white", anchor="center")  # Title label
details_lbl.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="nswe")  # Place the label

# Labels for mango attributes (e.g., weight, size, ripeness)
weight_lbl = ctk.CTkLabel(frame_1_2, text="Weight:", text_color="white")
weight_val = ctk.CTkLabel(frame_1_2, text="----", text_color="white")
size_lbl = ctk.CTkLabel(frame_1_2, text="Size:", text_color="white")
size_val = ctk.CTkLabel(frame_1_2, text="----", text_color="white")
ripeness_lbl = ctk.CTkLabel(frame_1_2, text="Ripeness:", text_color="white")
ripeness_val = ctk.CTkLabel(frame_1_2, text="----", text_color="white")
tss_lbl = ctk.CTkLabel(frame_1_2, text="TSS:", text_color="white")
tss_val = ctk.CTkLabel(frame_1_2, text="----", text_color="white")
dfct_lbl = ctk.CTkLabel(frame_1_2, text="Defect:", text_color="white")
dfct_val = ctk.CTkLabel(frame_1_2, text="----", text_color="white")
brs_lbl = ctk.CTkLabel(frame_1_2, text="Bruises:", text_color="white")
brs_val = ctk.CTkLabel(frame_1_2, text="----", text_color="white")

# Place the labels in the grid
size_lbl.grid(row=2, column=0, padx=5, pady=5)
size_val.grid(row=2, column=1, padx=5, pady=5)
ripeness_lbl.grid(row=3, column=0, padx=5, pady=5)
ripeness_val.grid(row=3, column=1, padx=5, pady=5)
brs_lbl.grid(row=7, column=0, padx=5, pady=5)
brs_val.grid(row=7, column=1, padx=5, pady=5)

# Add a counter for graded mangoes
grade_lbl = ctk.CTkLabel(frame_1_2, text="Mangoes Graded", text_color="white")
grade_lbl.grid(row=8, column=0, padx=5, pady=5, columnspan=2)
a_lbl = ctk.CTkLabel(frame_1_2, text="Grade A:", text_color="white")
a_val = ctk.CTkLabel(frame_1_2, text="----", text_color="white")
a_lbl.grid(row=9, column=0, padx=5, pady=5)
a_val.grid(row=9, column=1, padx=5, pady=5)
b_lbl = ctk.CTkLabel(frame_1_2, text="Grade B:", text_color="white")
b_val = ctk.CTkLabel(frame_1_2, text="----", text_color="white")
b_lbl.grid(row=10, column=0, padx=5, pady=5)
b_val.grid(row=10, column=1, padx=5, pady=5)
c_lbl = ctk.CTkLabel(frame_1_2, text="Grade C:", text_color="white")
c_val = ctk.CTkLabel(frame_1_2, text="----", text_color="white")
c_lbl.grid(row=11, column=0, padx=5, pady=5)
c_val.grid(row=11, column=1, padx=5, pady=5)
tot_lbl = ctk.CTkLabel(frame_1_2, text="Total:", text_color="white")
tot_val = ctk.CTkLabel(frame_1_2, text="----", text_color="white")
tot_lbl.grid(row=12, column=0, padx=5, pady=5)
tot_val.grid(row=12, column=1, padx=5, pady=5)

# Create a frame for interactable elements (buttons and options)
frame_2 = ctk.CTkFrame(window, fg_color="#B3B792")
frame_2.grid(row=0, column=2, padx=10, pady=10)

# Button frame for start, stop, and export buttons
btn_frame = ctk.CTkFrame(frame_2, fg_color="#000")
btn_frame.grid(row=0, column=0, padx=10, pady=10)
start_btn = ctk.CTkButton(btn_frame, text="start", fg_color="#8AD879")  # Green start button
start_btn.pack()
stop_btn = ctk.CTkButton(btn_frame, text="reset", fg_color="#F3533A", command=stop_now)  # Red stop button
stop_btn.pack()
exit_btn = ctk.CTkButton(btn_frame, text="stop", fg_color="#F3533A", command=exit_program)  # Exit button
exit_btn.pack()
export_btn = ctk.CTkButton(btn_frame, text="export", fg_color="#0000FF")  # Export button
export_btn.pack()

# Option frame for mango attribute priority settings
opt_frame = ctk.CTkFrame(frame_2, fg_color="#000")
opt_frame.grid(row=1, column=0, padx=10, pady=10)
mng_att_lbl = ctk.CTkLabel(opt_frame, text_color="white", text="Mango Attribute Priority")
mng_att_lbl.grid(column=0, row=0, padx=10, pady=10, sticky="nswe")

# Labels and dropdown menus for mango attributes
att_lbl1 = ctk.CTkLabel(opt_frame, text_color="white", text="Sweetness")
optionmenu = ctk.CTkOptionMenu(opt_frame, values=["option 1", "option 2"])
att_lbl2 = ctk.CTkLabel(opt_frame, text_color="white", text="Ripeness")
att_lbl2.grid(column=0, row=3, padx=10, pady=10, sticky="nswe")
optionmenu = ctk.CTkOptionMenu(opt_frame, values=["option 1", "option 2"])
optionmenu.grid(column=0, row=4, padx=10, pady=10, sticky="nswe")
att_lbl3 = ctk.CTkLabel(opt_frame, text_color="white", text="Size")
att_lbl3.grid(column=0, row=5, padx=10, pady=10, sticky="nswe")
optionmenu = ctk.CTkOptionMenu(opt_frame, values=["option 1", "option 2"])
optionmenu.grid(column=0, row=6, padx=10, pady=10, sticky="nswe")
att_lbl4 = ctk.CTkLabel(opt_frame, text_color="white", text="Bruising")
att_lbl4.grid(column=0, row=7, padx=10, pady=10, sticky="nswe")
optionmenu = ctk.CTkOptionMenu(opt_frame, values=["option 1", "option 2"])
optionmenu.grid(column=0, row=8, padx=10, pady=10, sticky="nswe")

# Run the application
window.mainloop()