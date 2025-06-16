import customtkinter as ctk
import time
from tkinter import ttk  # For combo boxes
# import RPi.GPIO as GPIO   

def picture_side1():
    print("Process and pictured side 1")
    buttonSide1.configure(state="disabled")
    buttonSide2.configure(state="normal")
    
def picture_side2():
    print("Process and pictured side 2")
    buttonSide1.configure(state="normal")
    buttonSide2.configure(state="disabled")
    
def move_motor(motor_array):
    # GPIO.output(self.relay1, val1)  # Motor 1 Forward
    # GPIO.output(self.relay2, val2)   # Motor 1 Reverse OFF
    # GPIO.output(self.relay3, val3)  # Motor 2 Forward
    # GPIO.output(self.relay4, val4)   # Motor 2 Reverse OFF
    if motor_array[0] == 1:
        print("Motor 1 is moving in Clockwise")
    if motor_array[1] == 1:
        print("Motor 1 is moving in Counter Clockwise")
    if motor_array[2] == 1:
        print("Motor 2 is moving in Clockwise")
    if motor_array[3] == 1:
        print("Motor 2 is moving in Counter Clockwise")
    # print(motor_array)

def get_number_from_textbox(textbox):
    try:
        text = textbox.get("1.0", "end-1c").strip()
        if text:  # Check if not empty
            return float(text)  # or int(text) for integer
        else:
            print("Please a number")
            return None  # default value for empty textbox
    except ValueError:
        print("Please enter a valid number")
        return None
    
# Countdown loop that prints the count and sleeps
def countdown(start_count):
    for i in range(start_count, 0, -1):
        print(i)
        time.sleep(1)
    
def button_callback(button):
    def toggle_color():
        # Get current color
        current_color = button.cget("fg_color")
        # Toggle between blue and green
        if current_color == "#1F6AA5" or current_color == "#3B8ED0" :  # Default blue
            button.configure(fg_color="green", hover_color="#0B662B")
        else:
            button.configure(fg_color="#1F6AA5", hover_color= "#3B8ED0" )
    return toggle_color

def button_run(buttontorun, textbox):
    run_time = get_number_from_textbox(textbox)
    textbox.configure(state="disabled")  # configure textbox to be read-only
    button_color = [buttonCWC1.cget("fg_color"), buttonCCWC1.cget("fg_color"), buttonCWC2.cget("fg_color"), buttonCCWC2.cget("fg_color")]
    button_list = [buttonCWC1, buttonCCWC1, buttonCWC2, buttonCCWC2]
    if run_time is None:
        print("Input a value")
    elif 'green' in button_color:
        if (button_color[0]=='green' and button_color[1]=='green') or (button_color[2]=='green' and button_color[3]=='green'):
            print("ERROR Unselect one of the buttons for C1/C2")
            textbox.configure(state="normal")  
        else:
            button_state_array = [1 if 'green' in color else 0 for color in button_color]
            move_motor(button_state_array)
            buttontorun.configure(text="Running...", state="disabled")
            countdown(int(run_time))
            
            buttontorun.configure(text="Run C1/C2", state="normal")
            print("Done Running!")
            for button in button_list:
                button.configure(fg_color="#1F6AA5", hover_color="#3B8ED0")
            textbox.configure(state="normal")      
            textbox.delete("0.0", "end")  # delete all text
    else: 
        print("Select One of the Buttons") 
        textbox.configure(state="normal") 
    
app =ctk.CTk()
app.title("Conveyor Controller")
app.geometry("500x500")

# Set consistent button dimensions
button_width = 180
button_height = 40

buttonCWC1 =ctk.CTkButton(app, text="Clockwise C1" , width=button_width, height=button_height, fg_color="#1F6AA5")
buttonCWC1.configure(command=button_callback(buttonCWC1))
buttonCWC1.grid(row=0, column=0, padx=20, pady=20)

buttonCCWC1 = ctk.CTkButton(app, text="Counter Clockwise C1" , width=button_width, height=button_height, fg_color="#1F6AA5")
buttonCCWC1.configure(command=button_callback(buttonCCWC1))
buttonCCWC1.grid(row=0, column=1, padx=20, pady=20)

buttonCWC2 = ctk.CTkButton(app, text="Clockwise C2" , width=button_width, height=button_height, fg_color="#1F6AA5")
buttonCWC2.configure(command=button_callback(buttonCWC2))
buttonCWC2.grid(row=1, column=0, padx=20, pady=20)

buttonCCWC2 = ctk.CTkButton(app, text="Counter Clockwise C2" , width=button_width, height=button_height, fg_color="#1F6AA5")
buttonCCWC2.configure(command=button_callback(buttonCCWC2))
buttonCCWC2.grid(row=1, column=1, padx=20, pady=20)

label = ctk.CTkLabel(app, text="Time to Move (in seconds?)", fg_color="transparent")
label.grid(row=2, column=0, columnspan=2, padx=10, pady=10)

textbox = ctk.CTkTextbox(app, width=button_width * 2 + 40, height=button_height)
textbox.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="nswe")

buttonRun = ctk.CTkButton(app, text="Run C1/C2" , width=button_width * 2 + 40, height=button_height, fg_color="#1FA3A5", hover_color="#177E80")
buttonRun.configure(command=lambda: button_run(buttonRun, textbox))
buttonRun.grid(row=4, column=0, columnspan=2, padx=20, pady=20)

buttonSide1 = ctk.CTkButton(app, text="Capture Side 1" , width=button_width, height=button_height, fg_color="#1FA3A5", hover_color="#177E80")
buttonSide1.configure(command=lambda: picture_side1())
buttonSide1.grid(row=5, column=0, padx=20, pady=20)

buttonSide2 = ctk.CTkButton(app, text="Capture Side 2" , width=button_width, height=button_height, fg_color="#1FA3A5", hover_color="#177E80")
buttonSide2.configure(command=lambda: picture_side2(), state="disabled")
buttonSide2.grid(row=5, column=1, padx=20, pady=20)

app.mainloop()
