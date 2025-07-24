import torch, time, sys, os, threading
from datetime import datetime
import torchvision.transforms as transforms
import customtkinter as ctk
from efficientnet_pytorch import EfficientNet
from PIL import Image, ImageTk
from get_size import calculate_size, determine_size
try:
    import RPi.GPIO as GPIO
    from picamera2 import Picamera2
    print("Running on Raspberry Pi - using real GPIO")
except ImportError:
    from fake_gpio import GPIO
    from fake_picamera2 import Picamera2
    print("Running on non-RPi system - using mock GPIO")
    
class ConveyorController:
    def __init__(self, app):
        self.colors = {
            "main_app_background": "#e5e0d8",      # Light beige - Lines: 20, 634, 649
            "frame_background": "#B3B792",         # Olive green - Lines: 129, 131
            "default_button": "#979da2",           # Gray - Lines: 141, 399, 433, 591, 596
            "hover_red": "#CC0000",                # Red - Line: 140
            "hover_gray": "#6e7174",               # Dark gray - Lines: 141, 399, 433, 596
            "text_background": "#f9f9fa",          # Off-white - Lines: 143, 161, 229, 396, 430
            "text_color": "#000000",               # Black - Lines: 143, 396, 430, 631
            "button_hover_blue": "#3B8ED0",        # Blue - Lines: 589, 590
            "green_hover": "#0B662B",              # Dark green - Line: 588
            "transparent": "transparent",          # Transparent - Lines: 221, 250
        }
        self.app = app
        self.app.title("Conveyor Controller")
        self.app.LENGTH = 1200
        self.app.WIDTH = 700
        self.app.geometry(f"{self.app.LENGTH}x{self.app.WIDTH}")
        self.app.fg_color = self.colors["main_app_background"]
        self.DEFAULT_BOLD = ctk.CTkFont(family=ctk.ThemeManager.theme["CTkFont"]["family"],size=ctk.ThemeManager.theme["CTkFont"]["size"],weight="bold")
        TITLE_FONT_SIZE = 20
        self.TITLE_FONT = ctk.CTkFont(family=ctk.ThemeManager.theme["CTkFont"]["family"],size=TITLE_FONT_SIZE,weight="bold")
        self.BUTTON_WIDTH = 180
        self.BUTTON_HEIGHT = 40
        self.CLASS_LABEL_RIPENESS = ['green', 'yellow_green', 'yellow']
        self.CLASS_LABEL_BRUISES = ['bruised', 'unbruised']
        self.CLASS_LABEL_SIZE = ['small', 'medium', 'large']
        self.RIPENESS_SCORES = {'yellow': 1.0, 'yellow_green': 2.0, 'green': 3.0}
        self.BRUISES_SCORES = {'bruised': 1.5, 'unbruised': 3.0}
        self.SIZE_SCORES = {'small': 1.0, 'medium': 2.0, 'large': 3.0}
        self.recorded_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.top_final_score = 0
        self.bottom_final_score = 0
        self.priority_enabled = True
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model_ripeness = EfficientNet.from_pretrained('efficientnet-b0', num_classes=len(self.CLASS_LABEL_RIPENESS))
        self.model_ripeness.load_state_dict(torch.load("ripeness.pth", map_location=self.device))
        self.model_ripeness.eval()
        self.model_ripeness.to(self.device)
        self.model_bruises = EfficientNet.from_pretrained('efficientnet-b0', num_classes=len(self.CLASS_LABEL_BRUISES))
        self.model_bruises.load_state_dict(torch.load("bruises.pth", map_location=self.device))
        self.model_bruises.eval()
        self.model_bruises.to(self.device)
        RESIZE_PIXELS = 224
        MEAN_RED_CHANNEL = 0.485
        MEAN_GREEN_CHANNEL = 0.456
        MEAN_BLUE_CHANNEL = 0.406
        SD_RED_CHANNEL = 0.229
        SD_GREEN_CHANNEL = 0.224
        SD_BLUE_CHANNEL=0.225
        self.transform = transforms.Compose([
            transforms.Resize((RESIZE_PIXELS, RESIZE_PIXELS)),
            transforms.ToTensor(),
            transforms.Normalize([MEAN_RED_CHANNEL, MEAN_GREEN_CHANNEL, MEAN_BLUE_CHANNEL], [SD_RED_CHANNEL, SD_GREEN_CHANNEL, SD_BLUE_CHANNEL])
        ])
        self.FOCAL_LENGTH_PIXELS = 3500
        self.DISTANCE_CAMERA_TO_OBJECT = 40
        self.BUTTON_WIDTH = 180
        self.BUTTON_HEIGHT = 40
        self.RELAY1 = 6
        self.RELAY2 = 13
        self.RELAY3 = 19
        self.RELAY4 = 26
        GPIO.cleanup()
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.RELAY1, GPIO.OUT)
        GPIO.setup(self.RELAY2, GPIO.OUT)
        GPIO.setup(self.RELAY3, GPIO.OUT)
        GPIO.setup(self.RELAY4, GPIO.OUT)
        GPIO.output(self.RELAY1, GPIO.LOW)
        GPIO.output(self.RELAY2, GPIO.LOW)
        GPIO.output(self.RELAY3, GPIO.LOW)
        GPIO.output(self.RELAY4, GPIO.LOW)
        GPIO.setwarnings(False)
        self.DIR_PIN = 21
        self.STEP_PIN = 20
        self.steps_per_revolution = 200
        self.position1 = 50
        self.position2 = 100
        self.position3 = 150
        self.current_position = 0
        self.step_delay = 0.001
        try:
            self.picam2 = Picamera2()
            self.camera_config = self.picam2.create_video_configuration(main={"size": (1920, 1080)})
            self.picam2.configure(self.camera_config)
            self.picam2.start()
            print("Camera initialized successfully")
        except Exception as e:
            print(f"Error initializing camera: {e}")
            self.picam2 = None

        self.init_ui()
    
    def set_to_stop_dc_motors(self):
        GPIO.output(self.RELAY1, GPIO.LOW)
        GPIO.output(self.RELAY2, GPIO.LOW)
        GPIO.output(self.RELAY3, GPIO.LOW)
        GPIO.output(self.RELAY4, GPIO.LOW)
        print("Motors stopped!")

    def set_to_position_step_motor(self,target):
        steps_needed = target - self.current_position
        if steps_needed == 0:
            return  
        
        direction = GPIO.HIGH if steps_needed > 0 else GPIO.LOW
        GPIO.output(self.DIR_PIN, direction)
        for _ in range(abs(steps_needed)):
            GPIO.output(self.STEP_PIN, GPIO.HIGH)
            time.sleep(self.step_delay)
            GPIO.output(self.STEP_PIN, GPIO.LOW)
            time.sleep(self.step_delay)
        
        self.current_position = target

    def init_ui(self):
        INIT_WEIGHT=1
        FRAME_PADDING_X=7
        FRAME_PADDING_Y=7
        self.app.grid_columnconfigure(0, weight=INIT_WEIGHT)
        self.app.grid_columnconfigure(1, weight=INIT_WEIGHT)
        
        self.main_frame = ctk.CTkFrame(self.app, fg_color=self.colors["frame_background"])
        self.main_frame.grid(row=0, column=1, padx=FRAME_PADDING_X, pady=FRAME_PADDING_Y, sticky="ns")
        self.view_frame = ctk.CTkFrame(self.app, fg_color=self.colors["frame_background"])
        self.view_frame.grid(row=0, column=0, padx=FRAME_PADDING_X, pady=FRAME_PADDING_Y, sticky="ns")
        
        self.init_user_priority_frame(self.main_frame)
        self.init_control_frame(self.main_frame)
        self.init_video_frame(self.view_frame)
        self.get_video_feed()
        

    def init_control_frame(self, main_frame):
        BUTTON_PADDING_X=7
        BUTTON_PADDING_Y=7
        left_frame = ctk.CTkFrame(main_frame)
        left_frame.grid(row=0, column=0, padx=BUTTON_PADDING_X, pady=BUTTON_PADDING_Y)
        col_index=0
        row_index=0
        self.button_reset = ctk.CTkButton(left_frame, text="Reset", width=self.BUTTON_WIDTH, height=self.BUTTON_HEIGHT, 
                                          fg_color=self.colors["default_button"], hover_color=self.colors["hover_red"]
                                         ,font=self.DEFAULT_BOLD)
        self.button_reset.configure(command=self.reset_program)
        self.button_reset.grid(row=row_index, column=col_index, padx=BUTTON_PADDING_X, pady=BUTTON_PADDING_Y, sticky="nswe")
        col_index += 1
        self.button_exit = ctk.CTkButton(left_frame, text="Exit", width=self.BUTTON_WIDTH, height=self.BUTTON_HEIGHT, fg_color=self.colors["default_button"], hover_color=self.colors["hover_red"]
                                        ,font=self.DEFAULT_BOLD)
        self.button_exit.configure(command=self.exit_program)
        self.button_exit.grid(row=row_index, column=col_index, padx=BUTTON_PADDING_X, pady=BUTTON_PADDING_Y, sticky="nswe")

        row_index += 1
        col_index = 0
        self.button_cwc1 = ctk.CTkButton(left_frame, text="rotate forward TOP belt", width=self.BUTTON_WIDTH, height=self.BUTTON_HEIGHT, fg_color=self.colors["default_button"]
                                        ,font=self.DEFAULT_BOLD)
        self.button_cwc1.configure(command=self.toggle_button_color(self.button_cwc1))
        self.button_cwc1.grid(row=row_index, column=col_index, padx=BUTTON_PADDING_X, pady=BUTTON_PADDING_Y, sticky="nswe")
        col_index += 1
        self.button_ccwc1 = ctk.CTkButton(left_frame, text="rotate backward TOP belt", width=self.BUTTON_WIDTH, height=self.BUTTON_HEIGHT, fg_color=self.colors["default_button"]
                                         ,font=self.DEFAULT_BOLD)
        self.button_ccwc1.configure(command=self.toggle_button_color(self.button_ccwc1))
        self.button_ccwc1.grid(row=row_index, column=col_index, padx=BUTTON_PADDING_X, pady=BUTTON_PADDING_Y, sticky="nswe")

        row_index += 1
        self.button_cwc2 = ctk.CTkButton(left_frame, text="rotate forward BOTTOM belt", width=self.BUTTON_WIDTH, height=self.BUTTON_HEIGHT, fg_color=self.colors["default_button"]
                                        ,font=self.DEFAULT_BOLD)
        self.button_cwc2.configure(command=self.toggle_button_color(self.button_cwc2))
        col_index = 0
        self.button_cwc2.grid(row=row_index, column=col_index, padx=BUTTON_PADDING_X, pady=BUTTON_PADDING_Y, sticky="nswe")
        self.button_ccwc2 = ctk.CTkButton(left_frame, text="rotate backward BOTTOM belt", width=self.BUTTON_WIDTH, height=self.BUTTON_HEIGHT, fg_color=self.colors["default_button"]
                                         ,font=self.DEFAULT_BOLD)
        col_index += 1
        self.button_ccwc2.configure(command=self.toggle_button_color(self.button_ccwc2))
        self.button_ccwc2.grid(row=row_index, column=col_index, padx=BUTTON_PADDING_X, pady=BUTTON_PADDING_Y, sticky="nswe")

        row_index += 1
        col_index = 0
        self.time_txt_button = ctk.CTkButton(left_frame, text="Time to Move (in seconds)", hover="disabled", font=self.DEFAULT_BOLD, fg_color=self.colors["text_background"], text_color=self.colors["text_color"]) 
        self.time_txt_button.grid(row=row_index, column=col_index, columnspan=2, padx=BUTTON_PADDING_X, pady=BUTTON_PADDING_Y, sticky="nswe")

        row_index += 1
        self.textbox = ctk.CTkTextbox(left_frame, width=self.BUTTON_WIDTH, height=self.BUTTON_HEIGHT)
        self.textbox.grid(row=row_index, column=col_index, columnspan=2, padx=BUTTON_PADDING_X, pady=BUTTON_PADDING_Y, sticky="nswe")

        row_index += 1
        self.button_background = ctk.CTkButton(left_frame, text="Capture Background", width=self.BUTTON_WIDTH * 2 + 40, height=self.BUTTON_HEIGHT, 
                                              fg_color=self.colors["default_button"], hover_color=self.colors["hover_gray"], font=self.DEFAULT_BOLD)
        self.button_background.configure(command=self.set_background_image)
        self.button_background.grid(row=row_index, column=col_index, columnspan=2, padx=BUTTON_PADDING_X, pady=BUTTON_PADDING_Y, sticky="nswe")
        
        row_index += 1
        self.button_run = ctk.CTkButton(left_frame, text="Run Conveyor(s) (top/bottom)", width=self.BUTTON_WIDTH * 2 + 40, height=self.BUTTON_HEIGHT, fg_color=self.colors["default_button"], hover_color=self.colors["hover_gray"]
                                       ,font=self.DEFAULT_BOLD, state="disabled")
        self.button_run.configure(command=lambda: self.init_run_conveyor(self.button_run, self.textbox))
        self.button_run.grid(row=row_index, column=col_index, columnspan=2, padx=BUTTON_PADDING_X, pady=BUTTON_PADDING_Y, sticky="nswe")

        row_index += 1
        self.button_side1 = ctk.CTkButton(left_frame, text="Capture Side 1", width=self.BUTTON_WIDTH, height=self.BUTTON_HEIGHT, fg_color=self.colors["default_button"], 
                                         hover_color=self.colors["hover_gray"], state="disabled",font=self.DEFAULT_BOLD)
        self.button_side1.configure(command=self.picture_side1)
        self.button_side1.grid(row=row_index, column=col_index, padx=BUTTON_PADDING_X, pady=BUTTON_PADDING_Y, sticky="nswe")

        self.button_side2 = ctk.CTkButton(left_frame, text="Capture Side 2", width=self.BUTTON_WIDTH, height=self.BUTTON_HEIGHT, fg_color=self.colors["default_button"], 
                                         hover_color=self.colors["hover_gray"], state="disabled",font=self.DEFAULT_BOLD)
        self.button_side2.configure(command=self.picture_side2)
        col_index += 1
        self.button_side2.grid(row=row_index, column=col_index, padx= BUTTON_PADDING_X, pady=BUTTON_PADDING_Y, sticky="nswe")
    
    def init_video_frame(self, frame):
        row_index=0
        PADDING_X=7
        PADDING_Y=7
        video_frame = ctk.CTkFrame(frame)
        video_frame.grid(row=row_index, column=0, padx=PADDING_X, pady=PADDING_Y, sticky="nsew")
        results_vid_frame = ctk.CTkFrame(video_frame, fg_color=self.colors["transparent"])
        results_vid_frame.grid(row=row_index, column=0, padx=PADDING_X/2, pady=PADDING_Y/2, sticky="nsew")
        
        video_button = ctk.CTkButton(results_vid_frame, text="Video Feed", width=300, height=self.BUTTON_HEIGHT, hover="disabled", font=self.TITLE_FONT, fg_color=self.colors["text_background"], 
                                     text_color=self.colors["text_color"])
        video_button.grid(row=row_index, column=0, padx=PADDING_X/2, pady=PADDING_Y/2, sticky="ns")
        row_index += 1
        self.video_canvas = ctk.CTkCanvas(video_frame, width=300, height=200)
        self.video_canvas.grid(row=row_index, column=0, padx=PADDING_X/2, pady=PADDING_Y/2, sticky="ns")

        row_index = 0
        results_frame = ctk.CTkFrame(video_frame, fg_color=self.colors["transparent"])
        results_frame.grid(row=row_index, columnspan=2, column=1, padx=PADDING_X/2, pady=PADDING_Y/2, sticky="nsew")
        results_button = ctk.CTkButton(results_frame, text="List of Results", width=300, height=self.BUTTON_HEIGHT, hover="disabled", font=self.TITLE_FONT, fg_color=self.colors["text_background"], 
                                       text_color=self.colors["text_color"])
        results_button.grid(row=row_index, column=0, padx=PADDING_X/2, pady=PADDING_Y/2, stick="nswe")
        
        row_index += 1
        dynamic_results_frame = ctk.CTkFrame(video_frame)
        dynamic_results_frame.grid(row=row_index, columnspan=2, column=1, padx=PADDING_X, pady=PADDING_Y, sticky="nsew")
        self.results_data = ctk.CTkLabel(dynamic_results_frame, text="Average Score: null \nPredicted Grade: null ", compound="left", justify="left")
        self.results_data.grid(row=row_index, columnspan=2, column=0, padx=PADDING_X, pady=PADDING_Y, sticky="nsew")
        
        row_index = 0
        side_frame = ctk.CTkFrame(frame, width=300, height=200)
        side_frame.grid(row=row_index+1, column=0, padx=PADDING_X, pady=PADDING_Y, sticky="ns")
        self.side1_button = ctk.CTkButton(side_frame, text="Side 1 Image", width=300, height=self.BUTTON_HEIGHT, hover="disabled", font=self.TITLE_FONT, fg_color=self.colors["text_background"], 
                                          text_color=self.colors["text_color"])
        self.side1_button.grid(row=row_index, column=0, padx=PADDING_X, pady=PADDING_Y, sticky="nswe")
        self.side2_button = ctk.CTkButton(side_frame, text="Side 2 Image", width=300, height=self.BUTTON_HEIGHT, hover="disabled", font=self.TITLE_FONT, fg_color=self.colors["text_background"], 
                                          text_color=self.colors["text_color"])
        self.side2_button.grid(row=row_index, column=1, padx=PADDING_X, pady=PADDING_Y, sticky="nswe")
        
        row_index += 1
        self.side1_box = ctk.CTkCanvas(side_frame, width=300, height=200, bg=self.colors["text_background"])
        self.side1_box.grid(row=row_index, column=0, padx=PADDING_X, pady=PADDING_Y, sticky="nswe")
        self.side2_box = ctk.CTkCanvas(side_frame, width=300, height=200, bg=self.colors["text_background"])
        self.side2_box.grid(row=row_index, column=1, padx=PADDING_X, pady=PADDING_Y, sticky="nswe")
        
        row_index += 1
        results_txt_frame1 = ctk.CTkFrame(side_frame)
        results_txt_frame1.grid(row=row_index, column=0, padx=PADDING_X, pady=PADDING_Y, sticky="nswe")
        self.side1_results = ctk.CTkLabel(results_txt_frame1, text="Ripeness: null\nBruises: null\nSize: null\nScore: null", compound="left", justify="left")
        self.side1_results.grid(row=0, column=0, padx=PADDING_X, pady=PADDING_Y,  sticky="nswe")
        
        results_txt_frame2 = ctk.CTkFrame(side_frame)
        results_txt_frame2.grid(row=row_index, column=1, padx=PADDING_X, pady=PADDING_Y, sticky="nswe")
        self.side2_results = ctk.CTkLabel(results_txt_frame2, text="Ripeness: null\nBruises: null\nSize: null\nScore: null", compound="left", justify="left")
        self.side2_results.grid(row=0, column=1, padx=PADDING_X, pady=PADDING_Y, sticky="nswe")
        
        return video_frame
    
    def init_user_priority_frame(self, main_frame):
        """TODO: add constant to column"""        
        row_index=6
        col_index=0
        PADDING_X_Y=7
        WIDTH_COMBOBOX=120
        TXT_WIDTH=80
        frame_choices = ctk.CTkFrame(main_frame)
        frame_choices.grid(row=row_index, column=col_index, padx=PADDING_X_Y, pady=PADDING_X_Y, sticky="nswe")
        frame_choices.columnconfigure(0, weight=1)
        frame_choices.columnconfigure(1, weight=1) 
        frame_choices.columnconfigure(2, weight=1)

        priority_txt = ctk.CTkButton(frame_choices, text="Input User Priority", hover="disabled", font=self.DEFAULT_BOLD, fg_color=self.colors["text_background"], text_color=self.colors["text_color"])
        priority_txt.grid(row=6, column=col_index, padx=PADDING_X_Y, pady=PADDING_X_Y, sticky="nswe", columnspan=3)   
        row_index+=1
        
        ripeness_txt = ctk.CTkButton(frame_choices, text="Ripeness", width=TXT_WIDTH, hover="disabled", font=self.DEFAULT_BOLD, fg_color=self.colors["text_background"], text_color=self.colors["text_color"])
        ripeness_txt.grid(row=row_index, column=col_index, padx=PADDING_X_Y, pady=PADDING_X_Y, sticky="ew")
        
        self.ripeness_combo = ctk.CTkComboBox(frame_choices, values=["0.0", "1.0", "2.0", "3.0"], width=WIDTH_COMBOBOX)
        self.ripeness_combo.set("3.0")
        self.ripeness_combo.grid(row=row_index+1, column=col_index, padx=PADDING_X_Y, pady=PADDING_X_Y, sticky="nswe")

        col_index+=1
        bruises_txt = ctk.CTkButton(frame_choices, text="Bruises", width=TXT_WIDTH, hover="disabled", font=self.DEFAULT_BOLD, fg_color=self.colors["text_background"], text_color=self.colors["text_color"])
        bruises_txt.grid(row=row_index, column=col_index, padx=PADDING_X_Y, pady=PADDING_X_Y, sticky="ew")
        self.bruises_combo = ctk.CTkComboBox(frame_choices, values=["0.0", "1.0", "2.0", "3.0"], width=WIDTH_COMBOBOX)
        self.bruises_combo.set("3.0")
        self.bruises_combo.grid(row=row_index+1, column=col_index, padx=PADDING_X_Y, pady=PADDING_X_Y, sticky="nswe")
        
        col_index+=1
        size_txt = ctk.CTkButton(frame_choices, text="Size", width=TXT_WIDTH, hover="disabled", font=self.DEFAULT_BOLD, fg_color=self.colors["text_background"], text_color=self.colors["text_color"])
        size_txt.grid(row=row_index, column=col_index, padx=PADDING_X_Y, pady=PADDING_X_Y, sticky="ew")
 
        row_index+=1
        self.size_combo = ctk.CTkComboBox(frame_choices, values=["0.0", "1.0", "2.0", "3.0"], width=WIDTH_COMBOBOX)
        self.size_combo.set("3.0")
        self.size_combo.grid(row=row_index, column=col_index, padx=PADDING_X_Y, pady=PADDING_X_Y, sticky="nswe")

        row_index+=1
        col_index=0
        self.button_enter = ctk.CTkButton(frame_choices, text="Enter", command=self.enter_priority, fg_color=self.colors["default_button"], hover_color=self.colors["hover_gray"]
                                          ,font=self.DEFAULT_BOLD)
        self.button_enter.grid(row=row_index, column=col_index, padx=PADDING_X_Y, pady=PADDING_X_Y, sticky="nswe", columnspan=3)

        row_index+=1
        self.button_help = ctk.CTkButton(frame_choices, text="Help", command=self.get_help_page_info, fg_color=self.colors["default_button"], hover_color=self.colors["hover_gray"]
                                         ,font=self.DEFAULT_BOLD)
        self.button_help.grid(row=row_index, column=col_index, padx=PADDING_X_Y, pady=PADDING_X_Y, sticky="nswe", columnspan=3)
        
        return frame_choices
        
    def get_help_page_info(self):
        #TODO: FILL UP THE HELP PAGE
        popup = ctk.CTkToplevel()
        length = self.app.LENGTH
        width = self.app.WIDTH
        popup.geometry(f"{length}x{width}")
        close_button = ctk.CTkButton(popup, text="Close", command=popup.destroy)
        close_button.pack(pady=10)
        
    def get_predicted_class(self, image, model, class_labels):
        image = self.transform(image).unsqueeze(0).to(self.device)
        output = model(image)
        _, predicted = torch.max(output, 1)
        return class_labels[predicted.item()]
    
    def set_background_image(self):
        if self.priority_enabled == False:
            self.recorded_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            
            background_img = self.get_image(self.picam2)
            background_img.save(f"{self.recorded_time}_background.png")
            
            self.button_background.configure(state="disabled")
            self.button_run.configure(state="normal")
            self.button_side1.configure(state="normal")
            self.button_enter.configure(state="disabled")
        else:
            top_parent = self.button_background.winfo_toplevel()
            self.set_error_pop_up(top_parent, "ERROR: No User Priority", "Please enter your selected values for the user priority.")
    
    def set_error_pop_up(self, parent, title="Error", message="An error occurred"):
        popup = ctk.CTkToplevel(parent)
        popup.title(title)
        popup.geometry("300x150")
        popup.fg_color = self.colors["main_app_background"]
        popup.resizable(False, False)
        
        popup.transient(parent)
        popup.grab_set()
        
        label = ctk.CTkLabel(popup, text=message, wraplength=250, font=self.DEFAULT_BOLD, text_color=self.colors["text_color"])
        label.pack(pady=20, padx=20)
        
        ok_button = ctk.CTkButton(popup, text="Ok", command=popup.destroy, fg_color=self.colors["default_button"], hover_color=self.colors["hover_gray"], font=self.DEFAULT_BOLD)
        ok_button.pack(pady=10)
        
        popup.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (popup.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (popup.winfo_height() // 2)
        popup.geometry(f"+{x}+{y}")
    
    def enter_priority(self):
        ripeness = self.ripeness_combo.get()
        bruises = self.bruises_combo.get()
        size = self.size_combo.get()
        print(f"Ripeness: {ripeness}, Bruises: {bruises}, Size: {size}")
        if self.priority_enabled == False:
            self.ripeness_combo.configure(state="normal")
            self.bruises_combo.configure(state="normal")
            self.size_combo.configure(state="normal")
            self.ripeness_combo.set("3.0")
            self.bruises_combo.set("3.0")
            self.size_combo.set("3.0")
            self.button_enter.configure(text="Enter")
            self.priority_enabled = True
        else:
            self.ripeness_combo.configure(state="disabled")
            self.bruises_combo.configure(state="disabled")
            self.size_combo.configure(state="disabled")
            self.button_enter.configure(text="Cancel")
            self.priority_enabled = False
        
    def reset_program(self):
        print("Resetting")
        GPIO.cleanup()
        self.picam2.stop()
        os.execv(sys.executable, [sys.executable] + sys.argv)

    def exit_program(self):
        print("Goodbye")
        GPIO.cleanup()
        self.picam2.stop()
        sys.exit(0)

    def picture_side1(self):
        print("Process and pictured side 1")
        top_image = self.get_image(self.picam2)
        top_image.save(f"{self.recorded_time}_top.png")
        formatted_date_time = self.recorded_time
        top_class_ripeness = self.get_predicted_class(top_image, self.model_ripeness, self.CLASS_LABEL_RIPENESS)
        top_class_bruises = self.get_predicted_class(top_image, self.model_bruises, self.CLASS_LABEL_BRUISES)
        top_width, top_length = calculate_size(f"{formatted_date_time}_top.png", f"{formatted_date_time}_background.png", 
        formatted_date_time, True,self.DISTANCE_CAMERA_TO_OBJECT, self.FOCAL_LENGTH_PIXELS)
        
        print(f"Top Width: {top_width:.2f} cm, Top Length: {top_length:.2f} cm")
        top_size_class = determine_size(top_width, top_length) 
        top_final_grade = self.get_overall_grade(top_class_ripeness, top_class_bruises, top_size_class)
        self.top_final_score=top_final_grade
        top_letter_grade = self.get_grade_letter(top_final_grade)
        self.set_textbox_results(top_image, top_class_ripeness, top_class_bruises, top_size_class, top_final_grade, top_letter_grade, True)
        
        self.button_side1.configure(state="disabled")
        self.button_side2.configure(state="normal")

    def picture_side2(self):
        print("Process and pictured side 2")
        bottom_image = self.get_image(self.picam2)
        bottom_image.save(f"{self.recorded_time}_bottom.png")
        formatted_date_time = self.recorded_time
        bottom_class_ripeness = self.get_predicted_class(bottom_image, self.model_ripeness, self.CLASS_LABEL_RIPENESS)
        bottom_class_bruises = self.get_predicted_class(bottom_image, self.model_bruises, self.CLASS_LABEL_BRUISES)
        bottom_width, bottom_length = calculate_size(f"{formatted_date_time}_bottom.png", f"{formatted_date_time}_background.png", 
        formatted_date_time, True,self.DISTANCE_CAMERA_TO_OBJECT, self.FOCAL_LENGTH_PIXELS)
        
        print(f"Bottom Width: {bottom_width:.2f} cm, Bottom Length: {bottom_length:.2f} cm")
        bottom_size_class = determine_size(bottom_width, bottom_length) 
        bottom_final_grade = self.get_overall_grade(bottom_class_ripeness, bottom_class_bruises, bottom_size_class)
        self.bottom_final_score=bottom_final_grade
        bottom_letter_grade = self.get_grade_letter(bottom_final_grade)
        self.set_textbox_results(bottom_image, bottom_class_ripeness, bottom_class_bruises, bottom_size_class, bottom_final_grade, bottom_letter_grade, False)
        
        average_score = (self.top_final_score + self.bottom_final_score) / 2
        average_letter = self.get_grade_letter(average_score)
        
        self.results_data.configure(text=f"Average Score: {average_score:.2f}\nPredicted Grade: {average_letter}")
        
        self.button_side2.configure(state="disabled")
        self.button_background.configure(state="normal")
        self.button_enter.configure(state="normal")
     
    def get_grade_letter(self, input_grade):
        priorities = self.get_input_priorities()
        boundaries = self.get_grade_formula(priorities)
        self.print_grade_formula(boundaries)
        
        return self.get_grade_with_formula(input_grade, boundaries)

    def get_input_priorities(self):
        return {
            'ripeness': float(self.ripeness_combo.get()),
            'bruises': float(self.bruises_combo.get()),
            'size': float(self.size_combo.get())
        }

    def get_grade_formula(self, priorities):
        max_score = (priorities['ripeness'] * self.RIPENESS_SCORES['green'] + 
                    priorities['bruises'] * self.BRUISES_SCORES['unbruised'] + 
                    priorities['size'] * self.SIZE_SCORES['large'])
        
        min_score = (priorities['ripeness'] * self.RIPENESS_SCORES['yellow'] + 
                    priorities['bruises'] * self.BRUISES_SCORES['bruised'] + 
                    priorities['size'] * self.SIZE_SCORES['small'])
        
        segment_size = (max_score - min_score) / 3
        
        return {
            'A': {'min': max_score - segment_size, 'max': max_score},
            'B': {'min': max_score - 2 * segment_size, 'max': max_score - segment_size},
            'C': {'min': min_score, 'max': max_score - 2 * segment_size}
        }

    def print_grade_formula(self, boundaries):
        print("Calculated Grade Range")
        for grade in ['A', 'B', 'C']:
            min_val = boundaries[grade]['min']
            max_val = boundaries[grade]['max']
            range_size = max_val - min_val
            print(f"Grade {grade}: {max_val:.2f} - {min_val:.2f}, Range: {range_size:.2f}")

    def get_grade_with_formula(self, input_grade, boundaries):
        if boundaries['A']['min'] <= input_grade <= boundaries['A']['max']:
            return "A"
        elif boundaries['B']['min'] <= input_grade < boundaries['B']['max']:
            return "B"
        else:
            return "C"    

    def get_overall_grade(self,r,b,s):
        r_priority = float(self.ripeness_combo.get())
        b_priority = float(self.bruises_combo.get())
        s_priority = float(self.size_combo.get())
        resulting_grade = r_priority*self.RIPENESS_SCORES[r] + b_priority*self.BRUISES_SCORES[b] + s_priority*self.SIZE_SCORES[s]
        print(f"Resulting Grade: {resulting_grade}")
        return resulting_grade
    
    def get_image(self, picam2):
        image = picam2.capture_array()
        image = Image.fromarray(image).convert("RGB")
        return image

    def set_textbox_results(self, image, ripeness, bruises, size, score, letter, is_top):
        def update():
            if is_top:
                self.side1_results.configure(text=f"Ripeness: {ripeness}\nBruises: {bruises}\nSize: {size}\nScore: {letter} or {score} ")
                top_photo = ImageTk.PhotoImage(image.resize((300, 200)))
                self.side1_box.create_image(0, 0, anchor=ctk.NW, image=top_photo)
                self.side1_box.image = top_photo  # Keep a reference
            else:
                self.side2_results.configure(text=f"Ripeness: {ripeness}\nBruises: {bruises}\nSize: {size}\nScore: {letter} or {score} ")
                bottom_photo = ImageTk.PhotoImage(image.resize((300, 200)))
                self.side2_box.create_image(0, 0, anchor=ctk.NW, image=bottom_photo)
                self.side2_box.image = bottom_photo  # Keep a reference
        self.app.after(0, update)
        
    def set_motors(self, motor_array):
        GPIO.output(self.RELAY1, motor_array[0])  
        GPIO.output(self.RELAY2, motor_array[1])   
        GPIO.output(self.RELAY3, motor_array[2])  
        GPIO.output(self.RELAY4, motor_array[3])   
        
        if motor_array[0]:
            print("Motor 1 is moving in Clockwise")
        if motor_array[1]:
            print("Motor 1 is moving in Counter Clockwise")
        if motor_array[2]:
            print("Motor 2 is moving in Clockwise")
        if motor_array[3]:
            print("Motor 2 is moving in Counter Clockwise")

    def get_number_from_textbox(self, textbox):
        try:
            text = textbox.get("1.0", "end-1c").strip()
            if text:
                return float(text)
            else:
                return None
        except ValueError:
            print("Please enter a valid number")
            top_parent = self.button_background.winfo_toplevel()
            self.set_error_pop_up(top_parent, "ERROR: Value Error", "Please enter a valid number.")
            return None
        
    def set_countdown_thread(self, start_count, buttontorun, textbox):
        button_list = [self.button_cwc1, self.button_ccwc1, self.button_cwc2, self.button_ccwc2]
        SLEEP_TIME = 1
        STOP_TIME = 0
        STEP_TIME = -1
        for i in range(start_count, STOP_TIME, STEP_TIME):
            print(i)
            time.sleep(SLEEP_TIME)
        self.app.after(STOP_TIME, lambda: self.set_motor_to_finished(buttontorun, textbox, button_list))

    def set_motor_to_finished(self, buttontorun, textbox, button_list):
        buttontorun.configure(text="Run Conveyor(s) (C1/C2)",state="normal")
        print("Done Running!")
        self.set_to_stop_dc_motors()
        for button in button_list:
            button.configure(fg_color=self.colors["default_button"], hover_color=self.colors["button_hover_blue"])
        textbox.delete("0.0", "end")
        textbox.configure(state="normal")

    def toggle_button_color(self, button):
        def toggle_color():
            current_color = button.cget("fg_color")
            if current_color == self.colors["default_button"] or current_color == self.colors["button_hover_blue"]:
                button.configure(fg_color="green", hover_color=self.colors["green_hover"])
            else:
                button.configure(fg_color=self.colors["default_button"], hover_color=self.colors["button_hover_blue"])

        return toggle_color

    def init_run_conveyor(self, buttontorun, textbox):
        run_time = self.get_number_from_textbox(textbox)
        textbox.configure(state="disabled")
        button_color = [self.button_cwc1.cget("fg_color"), self.button_ccwc1.cget("fg_color"), self.button_cwc2.cget("fg_color"), self.button_ccwc2.cget("fg_color")]
        
        if run_time is None:
            top_parent = self.button_background.winfo_toplevel()
            self.set_error_pop_up(top_parent, "ERROR: No Time Input", "Please enter the time to run conveyor(s).")
            textbox.configure(state="normal")
        elif 'green' in button_color:
            if ((button_color[0] == 'green' and button_color[1] == 'green') or 
                (button_color[2] == 'green' and button_color[3] == 'green')):
                top_parent = self.button_background.winfo_toplevel()
                self.set_error_pop_up(top_parent, "ERROR: Input Error", "Please click only one direction for each conveyor.")
                textbox.configure(state="normal")
            else:
                button_state_array = [1 if 'green' in color else 0 for color in button_color]
                self.set_motors(button_state_array)
                buttontorun.configure(text="Running...", state="disabled")
                set_countdown_thread = threading.Thread(target=self.set_countdown_thread, args=(int(run_time), buttontorun, textbox))
                set_countdown_thread.daemon = True  
                set_countdown_thread.start()
                textbox.configure(state="normal")
                textbox.delete("0.0", "end")  
        else: 
            top_parent = self.button_background.winfo_toplevel()
            self.set_error_pop_up(top_parent, "ERROR: No Input Error", "Please select one of the buttons for the direction of the conveyor(s).")
            textbox.configure(state="normal")

    def get_video_feed(self):
        FRAME_LENGTH = 300
        FRAME_WIDTH = 200
        BUFFER_TIME = 10
        X_LOCATION = 0
        Y_LOCATION = 0
        frame = self.picam2.capture_array()
        frame = Image.fromarray(frame).convert("RGB")
        frame = frame.resize((FRAME_LENGTH, FRAME_WIDTH))
        frame = ImageTk.PhotoImage(frame)
        self.video_canvas.create_image(X_LOCATION, Y_LOCATION, anchor=ctk.NW, image=frame)
        self.video_canvas.image = frame
        app.after(BUFFER_TIME, self.get_video_feed)

    def run(self):
        self.app.mainloop()

if __name__ == "__main__":
    ctk.set_appearance_mode("light")
    app = ctk.CTk(fg_color="#e5e0d8")
    controller = ConveyorController(app)
    controller.run()
