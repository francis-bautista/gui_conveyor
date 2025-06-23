import torch, time, sys, os, threading
from datetime import datetime
import torchvision.transforms as transforms
import customtkinter as ctk
from efficientnet_pytorch import EfficientNet
from PIL import Image, ImageTk
from get_size import calculate_size, determine_size
try:
    import RPi.GPIO as GPIO
    from picamera2 import Picamera2 #picamera2
    print("Running on Raspberry Pi - using real GPIO")
except ImportError:
    from fake_gpio import GPIO
    from fake_picamera2 import Picamera2
    print("Running on non-RPi system - using mock GPIO")
class ConveyorController:
    def __init__(self, app):
        # Initialize the main application
        self.app = app
        self.app.title("Conveyor Controller")
        self.app.geometry("1100x670")
        self.app.fg_color = "#e5e0d8"
        self.defaultBold = ctk.CTkFont(family=ctk.ThemeManager.theme["CTkFont"]["family"],size=ctk.ThemeManager.theme["CTkFont"]["size"],weight="bold")
        self.titleFont = ctk.CTkFont(family=ctk.ThemeManager.theme["CTkFont"]["family"],size=20,weight="bold")
        ctk.set_appearance_mode("light")
        # Set consistent button dimensions
        self.button_width = 180
        self.button_height = 40
        self.class_labels_ripeness = ['green', 'yellow_green', 'yellow']
        self.class_labels_bruises = ['bruised', 'unbruised']
        self.class_labels_size = ['small', 'medium', 'large']
        self.ripeness_scores = {'yellow': 1.0, 'yellow_green': 2.0, 'green': 3.0}
        self.bruiseness_scores = {'bruised': 1.5, 'unbruised': 3.0}
        self.size_scores = {'small': 1.0, 'medium': 2.0, 'large': 3.0}
        self.recorded_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.top_final_score = 0
        self.bottom_final_score = 0
        self.priority_enabled = True
        # Load Training and Testing Models
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        # Ripeness model
        self.model_ripeness = EfficientNet.from_pretrained('efficientnet-b0', num_classes=len(self.class_labels_ripeness))
        self.model_ripeness.load_state_dict(torch.load("ripeness.pth", map_location=self.device))
        self.model_ripeness.eval()
        self.model_ripeness.to(self.device)
        # Bruises model
        self.model_bruises = EfficientNet.from_pretrained('efficientnet-b0', num_classes=len(self.class_labels_bruises))
        self.model_bruises.load_state_dict(torch.load("bruises.pth", map_location=self.device))
        self.model_bruises.eval()
        self.model_bruises.to(self.device)
        # Define transformations
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])
        # Size calculation parameters
        self.FOCAL_LENGTH_PIXELS = 3500  # Example value, replace with your camera's focal length
        self.DISTANCE_CAMERA_TO_OBJECT = 40  # 20.5 cm according to don
        
        # Set consistent button dimensions
        self.button_width = 180
        self.button_height = 40

        self.relay1 = 6   # Motor 1 Forward
        self.relay2 = 13   # Motor 1 Reverse
        self.relay3 = 19  # Motor 2 Forward
        self.relay4 = 26  # Motor 2 Reverse
        GPIO.cleanup()  # Reset GPIO settings
        GPIO.setmode(GPIO.BCM)  # Use Broadcom pin numbering
        GPIO.setup(self.relay1, GPIO.OUT)
        GPIO.setup(self.relay2, GPIO.OUT)
        GPIO.setup(self.relay3, GPIO.OUT)
        GPIO.setup(self.relay4, GPIO.OUT)
        # Initialize relays to OFF state
        GPIO.output(self.relay1, GPIO.LOW)
        GPIO.output(self.relay2, GPIO.LOW)
        GPIO.output(self.relay3, GPIO.LOW)
        GPIO.output(self.relay4, GPIO.LOW)
        GPIO.setwarnings(False)

        # Initialize camera
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
    
    def stop_motors(self):
        GPIO.output(self.relay1, GPIO.LOW)
        GPIO.output(self.relay2, GPIO.LOW)
        GPIO.output(self.relay3, GPIO.LOW)
        GPIO.output(self.relay4, GPIO.LOW)
        print("Motors stopped!")

    def init_ui(self):
        """Initialize all UI components"""
        # Configure grid layout
        self.app.grid_columnconfigure(0, weight=1)  # Control column (analysis results)
        self.app.grid_columnconfigure(1, weight=1)  # Right column (controls)
        # self.app.grid_columnconfigure(2, weight=1)
        
        self.main_frame = ctk.CTkFrame(self.app, fg_color="#B3B792")
        self.main_frame.grid(row=0, column=1, padx=7, pady=7, sticky="ns")
        
        self.view_frame = ctk.CTkFrame(self.app, fg_color="#B3B792")
        self.view_frame.grid(row=0, column=0, padx=7, pady=7, sticky="ns")
        
        self.user_priority_frame(self.main_frame)
        self.control_frame(self.main_frame)
        self.video_frame(self.view_frame)
        self.video_feed()
        

    def control_frame(self, main_frame):
        left_frame = ctk.CTkFrame(main_frame)
        left_frame.grid(row=0, column=0, padx=7, pady=7)
        button_padx=7
        button_pady=7
        row_index=0
        self.buttonExit = ctk.CTkButton(left_frame, text="Exit", width=self.button_width, height=self.button_height, fg_color="#979da2", hover_color="#CC0000"
                                        ,font=self.defaultBold)
        self.buttonExit.configure(command=self.exit_program)
        self.buttonExit.grid(row=row_index, column=1, padx=button_padx, pady=button_pady, sticky="nswe")

        self.buttonReset = ctk.CTkButton(left_frame, text="Reset", width=self.button_width, height=self.button_height, fg_color="#979da2", hover_color="#CC0000"
                                         ,font=self.defaultBold)
        self.buttonReset.configure(command=self.reset_program)
        self.buttonReset.grid(row=row_index, column=0, padx=button_padx, pady=button_pady, sticky="nswe")

        row_index += 1

        # Motor control buttons
        self.buttonCWC1 = ctk.CTkButton(left_frame, text="rotate forward TOP belt", width=self.button_width, height=self.button_height, fg_color="#979da2"
                                        ,font=self.defaultBold)
        self.buttonCWC1.configure(command=self.button_callback(self.buttonCWC1))
        self.buttonCWC1.grid(row=row_index, column=0, padx=button_padx, pady=button_pady, sticky="nswe")

        self.buttonCCWC1 = ctk.CTkButton(left_frame, text="rotate backward TOP belt", width=self.button_width, height=self.button_height, fg_color="#979da2"
                                         ,font=self.defaultBold)
        self.buttonCCWC1.configure(command=self.button_callback(self.buttonCCWC1))
        self.buttonCCWC1.grid(row=row_index, column=1, padx=button_padx, pady=button_pady, sticky="nswe")

        row_index += 1

        self.buttonCWC2 = ctk.CTkButton(left_frame, text="rotate forward BOTTOM belt", width=self.button_width, height=self.button_height, fg_color="#979da2"
                                        ,font=self.defaultBold)
        self.buttonCWC2.configure(command=self.button_callback(self.buttonCWC2))
        self.buttonCWC2.grid(row=row_index, column=0, padx=button_padx, pady=button_pady, sticky="nswe")

        self.buttonCCWC2 = ctk.CTkButton(left_frame, text="rotate backward BOTTOM belt", width=self.button_width, height=self.button_height, fg_color="#979da2"
                                         ,font=self.defaultBold)
        self.buttonCCWC2.configure(command=self.button_callback(self.buttonCCWC2))
        self.buttonCCWC2.grid(row=row_index, column=1, padx=button_padx, pady=button_pady, sticky="nswe")

        row_index += 1
        
        self.timeTxtButton = ctk.CTkButton(left_frame, text="Time to Move (in seconds)", hover="disabled", font=self.defaultBold, fg_color="#f9f9fa", text_color="#000000") 
        self.timeTxtButton.grid(row=row_index, column=0, columnspan=2, padx=button_padx, pady=button_pady, sticky="nswe")
        
        row_index += 1
        self.textbox = ctk.CTkTextbox(left_frame, width=self.button_width, height=self.button_height)
        self.textbox.grid(row=row_index, column=0, columnspan=2, padx=button_padx, pady=button_pady, sticky="nswe")

        row_index += 1

        # Camera control buttons
        self.buttonBackground = ctk.CTkButton(left_frame, text="Capture Background", width=self.button_width * 2 + 40, height=self.button_height, 
                                              fg_color="#979da2", hover_color="#6e7174", font=self.defaultBold)
        self.buttonBackground.configure(command=self.picture_background)
        self.buttonBackground.grid(row=row_index, column=0, columnspan=2, padx=button_padx, pady=button_pady, sticky="nswe")
        
        row_index += 1
        
        # Run button
        self.buttonRun = ctk.CTkButton(left_frame, text="Run Conveyor(s) (top/bottom)", width=self.button_width * 2 + 40, height=self.button_height, fg_color="#979da2", hover_color="#6e7174"
                                       ,font=self.defaultBold, state="disabled")
        self.buttonRun.configure(command=lambda: self.button_run(self.buttonRun, self.textbox))
        self.buttonRun.grid(row=row_index, column=0, columnspan=2, padx=button_padx, pady=button_pady, sticky="nswe")

        row_index += 1

        # Camera control buttons
        self.buttonSide1 = ctk.CTkButton(left_frame, text="Capture Side 1", width=self.button_width, height=self.button_height, fg_color="#979da2", 
                                         hover_color="#6e7174", state="disabled",font=self.defaultBold)
        self.buttonSide1.configure(command=self.picture_side1)
        self.buttonSide1.grid(row=row_index, column=0, padx=button_padx, pady=button_pady, sticky="nswe")

        self.buttonSide2 = ctk.CTkButton(left_frame, text="Capture Side 2", width=self.button_width, height=self.button_height, fg_color="#979da2", 
                                         hover_color="#6e7174", state="disabled",font=self.defaultBold)
        self.buttonSide2.configure(command=self.picture_side2)
        self.buttonSide2.grid(row=row_index, column=1, padx= button_padx, pady=button_pady, sticky="nswe")
    
    def video_frame(self, frame):
        """Setup the video feed frame"""
        row_index=0
        paddingx=7
        paddingy=7
        video_frame = ctk.CTkFrame(frame)
        video_frame.grid(row=row_index, column=0, padx=paddingx, pady=paddingy, sticky="nsew")
        
        results_vid_frame = ctk.CTkFrame(video_frame, fg_color="transparent")
        results_vid_frame.grid(row=row_index, column=0, padx=paddingx/2, pady=paddingy/2, sticky="nsew")
        
        video_button = ctk.CTkButton(results_vid_frame, text="Video Feed", width=300, height=self.button_height, hover="disabled", font=self.titleFont, fg_color="#f9f9fa", 
                                     text_color="#000000")
        video_button.grid(row=row_index, column=0, padx=paddingx/2, pady=paddingy/2, sticky="ns")
        
        self.video_canvas = ctk.CTkCanvas(video_frame, width=300, height=200)
        self.video_canvas.grid(row=row_index+1, column=0, padx=paddingx/2, pady=paddingy/2, sticky="ns")
        
        results_frame = ctk.CTkFrame(video_frame, fg_color="transparent")
        results_frame.grid(row=row_index, columnspan=2, column=1, padx=paddingx/2, pady=paddingy/2, sticky="nsew")
        
        results_button = ctk.CTkButton(results_frame, text="List of Results", width=300, height=self.button_height, hover="disabled", font=self.titleFont, fg_color="#f9f9fa", 
                                       text_color="#000000")
        results_button.grid(row=row_index, column=0, padx=paddingx/2, pady=paddingy/2, stick="nswe")
        
        row_index += 1
        dynamic_results_frame = ctk.CTkFrame(video_frame)
        dynamic_results_frame.grid(row=row_index, columnspan=2, column=1, padx=paddingx, pady=paddingy, sticky="nsew")
        self.results_data = ctk.CTkLabel(dynamic_results_frame, text="Average Score: null \nPredicted Grade: null ", compound="left", justify="left")
        self.results_data.grid(row=row_index, columnspan=2, column=0, padx=paddingx, pady=paddingy, sticky="nsew")
        
        
        row_index = 0
        side_frame = ctk.CTkFrame(frame, width=300, height=200)
        side_frame.grid(row=row_index+1, column=0, padx=paddingx, pady=paddingy, sticky="ns")
        
        self.side1_button = ctk.CTkButton(side_frame, text="Side 1 Image", width=300//2, height=self.button_height, hover="disabled", font=self.titleFont, fg_color="#f9f9fa", 
                                          text_color="#000000")
        self.side1_button.grid(row=row_index, column=0, padx=paddingx, pady=paddingy, sticky="nswe")
        self.side2_button = ctk.CTkButton(side_frame, text="Side 2 Image", width=300//2, height=self.button_height, hover="disabled", font=self.titleFont, fg_color="#f9f9fa", 
                                          text_color="#000000")
        self.side2_button.grid(row=row_index, column=1, padx=paddingx, pady=paddingy, sticky="nswe")
        
        row_index += 1
        
        self.side1_box = ctk.CTkCanvas(side_frame, width=300, height=200, bg="#f9f9fa")
        self.side1_box.grid(row=row_index, column=0, padx=paddingx, pady=paddingy, sticky="nswe")
        self.side2_box = ctk.CTkCanvas(side_frame, width=300, height=200, bg="#f9f9fa")
        self.side2_box.grid(row=row_index, column=1, padx=paddingx, pady=paddingy, sticky="nswe")
        
        row_index += 1
        results_txt_frame1 = ctk.CTkFrame(side_frame)
        results_txt_frame1.grid(row=row_index, column=0, padx=paddingx, pady=paddingy, sticky="nswe")
        self.side1_results = ctk.CTkLabel(results_txt_frame1, text="Ripeness: null\nBruises: null\nSize: null\nScore: null", compound="left", justify="left")
        self.side1_results.grid(row=0, column=0, padx=paddingx, pady=paddingy,  sticky="nswe")
        
        results_txt_frame2 = ctk.CTkFrame(side_frame)
        results_txt_frame2.grid(row=row_index, column=1, padx=paddingx, pady=paddingy, sticky="nswe")
        self.side2_results = ctk.CTkLabel(results_txt_frame2, text="Ripeness: null\nBruises: null\nSize: null\nScore: null", compound="left", justify="left")
        self.side2_results.grid(row=0, column=1, padx=paddingx, pady=paddingy, sticky="nswe")
        
        return video_frame
    
    def user_priority_frame(self, main_frame):
        """Setup the user priority section with combo boxes"""
        index_row=6
        padding=7
        width_combobox=120
        txt_width=80
        col=0
        frame_choices = ctk.CTkFrame(main_frame)
        frame_choices.grid(row=index_row, column=0, padx=padding, pady=padding, sticky="nswe")
        frame_choices.columnconfigure(0, weight=1)
        frame_choices.columnconfigure(1, weight=1) 
        frame_choices.columnconfigure(2, weight=1)
        # User Priority heading
        priority_txt = ctk.CTkButton(frame_choices, text="Input User Priority", hover="disabled", font=self.defaultBold, fg_color="#f9f9fa", text_color="#000000")
        priority_txt.grid(row=6, column=col, padx=padding, pady=padding, sticky="nswe", columnspan=3)   
        index_row+=1
        
        # Ripeness combo
        ripeness_txt = ctk.CTkButton(frame_choices, text="Ripeness", width=txt_width, hover="disabled", font=self.defaultBold, fg_color="#f9f9fa", text_color="#000000")
        ripeness_txt.grid(row=index_row, column=col, padx=padding, pady=padding, sticky="ew")
        
        self.ripeness_combo = ctk.CTkComboBox(frame_choices, values=["0.0", "1.0", "2.0", "3.0"], width=width_combobox)
        self.ripeness_combo.set("3.0")  # Set default value
        self.ripeness_combo.grid(row=index_row+1, column=col, padx=padding, pady=padding, sticky="nswe")

        # Bruises combo
        col+=1
        bruises_txt = ctk.CTkButton(frame_choices, text="Bruises", width=txt_width, hover="disabled", font=self.defaultBold, fg_color="#f9f9fa", text_color="#000000")
        bruises_txt.grid(row=index_row, column=col, padx=padding, pady=padding, sticky="ew")
        self.bruises_combo = ctk.CTkComboBox(frame_choices, values=["0.0", "1.0", "2.0", "3.0"], width=width_combobox)
        self.bruises_combo.set("3.0")  # Set default value
        self.bruises_combo.grid(row=index_row+1, column=col, padx=padding, pady=padding, sticky="nswe")
        
        # Size combo
        col+=1
        size_txt = ctk.CTkButton(frame_choices, text="Size", width=txt_width, hover="disabled", font=self.defaultBold, fg_color="#f9f9fa", text_color="#000000")
        size_txt.grid(row=index_row, column=col, padx=padding, pady=padding, sticky="ew")
        
        self.size_combo = ctk.CTkComboBox(frame_choices, values=["0.0", "1.0", "2.0", "3.0"], width=width_combobox)
        self.size_combo.set("3.0")  # Set default value
        self.size_combo.grid(row=index_row+1, column=col, padx=padding, pady=padding, sticky="nswe")
        
        self.button_enter = ctk.CTkButton(frame_choices, text="Enter", command=self.enter_priority, fg_color="#979da2", hover_color="#6e7174"
                                          ,font=self.defaultBold)
        self.button_enter.grid(row=index_row+2, column=0, padx=padding, pady=padding, sticky="nswe", columnspan=3)
        
        self.button_help = ctk.CTkButton(frame_choices, text="Help", command=self.help_page, fg_color="#979da2", hover_color="#6e7174"
                                         ,font=self.defaultBold)
        self.button_help.grid(row=index_row+3, column=0, padx=padding, pady=padding, sticky="nswe", columnspan=3)
        
        return frame_choices
        
    def help_page(self):
        print("Help page")
        
    def classify_image(self, image, model, class_labels):
        # This would be implemented to classify the image
        # Placeholder implementation
        image = self.transform(image).unsqueeze(0).to(self.device)
        output = model(image)
        _, predicted = torch.max(output, 1)
        return class_labels[predicted.item()]
    
    def picture_background(self):
        if self.priority_enabled == False:
            self.recorded_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            
            background_img = self.capture_image(self.picam2)
            background_img.save(f"{self.recorded_time}_background.png")
            
            self.buttonBackground.configure(state="disabled")
            self.buttonRun.configure(state="normal")
            self.buttonSide1.configure(state="normal")
            self.button_enter.configure(state="disabled")
        else:
            topParent = self.buttonBackground.winfo_toplevel()
            self.show_error_popup(topParent, "ERROR: No User Priority", "Please enter your selected values for the user priority.")
    
    def show_error_popup(self, parent, title="Error", message="An error occurred"):
        # Create popup window
        popup = ctk.CTkToplevel(parent)
        popup.title(title)
        popup.geometry("300x150")
        popup.fg_color = "#e5e0d8"
        popup.resizable(False, False)
        
        # Center the popup
        popup.transient(parent)
        popup.grab_set()  # Make popup modal
        
        # Add error message
        label = ctk.CTkLabel(popup, text=message, wraplength=250, font=self.defaultBold, text_color="#000000")
        label.pack(pady=20, padx=20)
        
        # Add OK button
        ok_button = ctk.CTkButton(popup, text="Ok", command=popup.destroy, fg_color="#979da2", hover_color="#6e7174", font=self.defaultBold)
        ok_button.pack(pady=10)
        
        # Center the popup on parent window
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
            # unlock the user priority input and clear the fields to default and set it to enter text
            self.ripeness_combo.configure(state="normal")
            self.bruises_combo.configure(state="normal")
            self.size_combo.configure(state="normal")
            self.ripeness_combo.set("3.0")  # Set default value
            self.bruises_combo.set("3.0")  # Set default value
            self.size_combo.set("3.0")  # Set default value
            self.button_enter.configure(text="Enter")
            self.priority_enabled = True
        else:
            # lock the user priority then set it to cancel text
            self.ripeness_combo.configure(state="disabled")
            self.bruises_combo.configure(state="disabled")
            self.size_combo.configure(state="disabled")
            self.button_enter.configure(text="Cancel")
            self.priority_enabled = False
        
    def reset_program(self):
        print("Resetting")
        GPIO.cleanup()  # Reset GPIO settings
        self.picam2.stop()
        os.execv(sys.executable, [sys.executable] + sys.argv)

    def exit_program(self):
        print("Goodbye")
        GPIO.cleanup()  # Reset GPIO settings
        self.picam2.stop()
        sys.exit(0)

    def picture_side1(self):
        """Handle capturing side 1 image"""
        print("Process and pictured side 1")
        top_image = self.capture_image(self.picam2)
        top_image.save(f"{self.recorded_time}_top.png")
        formatted_date_time = self.recorded_time
        top_class_ripeness = self.classify_image(top_image, self.model_ripeness, self.class_labels_ripeness)
        top_class_bruises = self.classify_image(top_image, self.model_bruises, self.class_labels_bruises)
        top_width, top_length = calculate_size(f"{formatted_date_time}_top.png", f"{formatted_date_time}_background.png", 
        formatted_date_time, True,self.DISTANCE_CAMERA_TO_OBJECT, self.FOCAL_LENGTH_PIXELS)
        
        print(f"Top Width: {top_width:.2f} cm, Top Length: {top_length:.2f} cm")
        top_size_class = determine_size(top_width, top_length) 
        top_final_grade = self.final_grade(top_class_ripeness, top_class_bruises, top_size_class)
        self.top_final_score=top_final_grade
        top_letter_grade = self.find_letter_grade(top_final_grade)
        self.update_side_box_results(top_image, top_class_ripeness, top_class_bruises, top_size_class, top_final_grade, top_letter_grade, True)
        
        self.buttonSide1.configure(state="disabled")
        self.buttonSide2.configure(state="normal")

    def picture_side2(self):
        """Handle capturing side 2 image"""
        print("Process and pictured side 2")
        bottom_image = self.capture_image(self.picam2)
        bottom_image.save(f"{self.recorded_time}_bottom.png")
        formatted_date_time = self.recorded_time
        bottom_class_ripeness = self.classify_image(bottom_image, self.model_ripeness, self.class_labels_ripeness)
        bottom_class_bruises = self.classify_image(bottom_image, self.model_bruises, self.class_labels_bruises)
        bottom_width, bottom_length = calculate_size(f"{formatted_date_time}_bottom.png", f"{formatted_date_time}_background.png", 
        formatted_date_time, True,self.DISTANCE_CAMERA_TO_OBJECT, self.FOCAL_LENGTH_PIXELS)
        
        print(f"Bottom Width: {bottom_width:.2f} cm, Bottom Length: {bottom_length:.2f} cm")
        bottom_size_class = determine_size(bottom_width, bottom_length) 
        bottom_final_grade = self.final_grade(bottom_class_ripeness, bottom_class_bruises, bottom_size_class)
        self.bottom_final_score=bottom_final_grade
        bottom_letter_grade = self.find_letter_grade(bottom_final_grade)
        self.update_side_box_results(bottom_image, bottom_class_ripeness, bottom_class_bruises, bottom_size_class, bottom_final_grade, bottom_letter_grade, False)
        
        average_score = (self.top_final_score + self.bottom_final_score) / 2
        average_letter = self.find_letter_grade(average_score)
        
        self.results_data.configure(text=f"Average Score: {average_score:.2f}\nPredicted Grade: {average_letter}")
        
        self.buttonSide2.configure(state="disabled")
        self.buttonBackground.configure(state="normal")
        self.button_enter.configure(state="normal")
     
    def find_letter_grade(self, input_grade):
        """
        Determines letter grade (A, B, or C) based on input score and priority weights.
        
        Args:
            input_grade (float): The calculated grade score to classify
            
        Returns:
            str: Letter grade ('A', 'B', or 'C')
        """
        # Get priority weights from UI components
        priorities = self._get_priority_weights()
        
        # Calculate grade boundaries
        boundaries = self._calculate_grade_boundaries(priorities)
        
        # Debug output
        self._print_grade_ranges(boundaries)
        
        # Determine letter grade
        return self._classify_grade(input_grade, boundaries)

    def _get_priority_weights(self):
        """Extract priority weights from combo boxes."""
        return {
            'ripeness': float(self.ripeness_combo.get()),
            'bruises': float(self.bruises_combo.get()),
            'size': float(self.size_combo.get())
        }

    def _calculate_grade_boundaries(self, priorities):
        """
        Calculate grade boundaries based on priority weights.
        
        Args:
            priorities (dict): Priority weights for each attribute
            
        Returns:
            dict: Grade boundaries with min/max values for each grade
        """
        # Calculate theoretical max (Grade A) and min (Grade C) scores
        max_score = (priorities['ripeness'] * self.ripeness_scores['green'] + 
                    priorities['bruises'] * self.bruiseness_scores['unbruised'] + 
                    priorities['size'] * self.size_scores['large'])
        
        min_score = (priorities['ripeness'] * self.ripeness_scores['yellow'] + 
                    priorities['bruises'] * self.bruiseness_scores['bruised'] + 
                    priorities['size'] * self.size_scores['small'])
        
        # Divide range into three equal segments
        segment_size = (max_score - min_score) / 3
        
        return {
            'A': {'min': max_score - segment_size, 'max': max_score},
            'B': {'min': max_score - 2 * segment_size, 'max': max_score - segment_size},
            'C': {'min': min_score, 'max': max_score - 2 * segment_size}
        }

    def _print_grade_ranges(self, boundaries):
        """Print grade ranges for debugging purposes."""
        print("Calculated Grade Range")
        for grade in ['A', 'B', 'C']:
            min_val = boundaries[grade]['min']
            max_val = boundaries[grade]['max']
            range_size = max_val - min_val
            print(f"Grade {grade}: {max_val:.2f} - {min_val:.2f}, Range: {range_size:.2f}")

    def _classify_grade(self, input_grade, boundaries):
        """
        Classify input grade into letter grade category.
        
        Args:
            input_grade (float): Score to classify
            boundaries (dict): Grade boundaries
            
        Returns:
            str: Letter grade
        """
        if boundaries['A']['min'] <= input_grade <= boundaries['A']['max']:
            return "A"
        elif boundaries['B']['min'] <= input_grade < boundaries['B']['max']:
            return "B"
        else:
            return "C"    

    def final_grade(self,r,b,s):
        r_priority = float(self.ripeness_combo.get())
        b_priority = float(self.bruises_combo.get())
        s_priority = float(self.size_combo.get())
        resulting_grade = r_priority*self.ripeness_scores[r] + b_priority*self.bruiseness_scores[b] + s_priority*self.size_scores[s]
        print(f"Resulting Grade: {resulting_grade}")
        return resulting_grade
    
    def capture_image(self, picam2):
        # This would be implemented to capture an image from the camera
        # Placeholder implementation
        image = picam2.capture_array()
        image = Image.fromarray(image).convert("RGB")
        return image

    def update_side_box_results(self, image, ripeness, bruises, size, score, letter, isTop):
        """Update the UI with top results"""
        def update():
            if isTop:
                self.side1_results.configure(text=f"Ripeness: {ripeness}\nBruises: {bruises}\nSize: {size}\nScore: {letter} or {score} ")
                top_photo = ImageTk.PhotoImage(image.resize((300, 200)))
                self.side1_box.create_image(0, 0, anchor=ctk.NW, image=top_photo)
                self.side1_box.image = top_photo  # Keep a reference
            else:
                self.side2_results.configure(text=f"Ripeness: {ripeness}\nBruises: {bruises}\nSize: {size}\nScore: {letter} or {score} ")
                bottom_photo = ImageTk.PhotoImage(image.resize((300, 200)))
                self.side2_box.create_image(0, 0, anchor=ctk.NW, image=bottom_photo)
                self.side2_box.image = bottom_photo  # Keep a reference
        self.app.after(0, update) # either video_frame or app
        
    def move_motor(self, motor_array):
        """Control motor movement based on array values"""
        GPIO.output(self.relay1, motor_array[0])  
        GPIO.output(self.relay2, motor_array[1])   
        GPIO.output(self.relay3, motor_array[2])  
        GPIO.output(self.relay4, motor_array[3])   
        
        if motor_array[0] == 1:
            print("Motor 1 is moving in Clockwise")
        if motor_array[1] == 1:
            print("Motor 1 is moving in Counter Clockwise")
        if motor_array[2] == 1:
            print("Motor 2 is moving in Clockwise")
        if motor_array[3] == 1:
            print("Motor 2 is moving in Counter Clockwise")

    def get_number_from_textbox(self, textbox):
        """Extract and validate number from textbox"""
        try:
            text = textbox.get("1.0", "end-1c").strip()
            if text:  # Check if not empty
                return float(text)  # or int(text) for integer
            else:
                return None  # default value for empty textbox
        except ValueError:
            print("Please enter a valid number")
            topParent = self.buttonBackground.winfo_toplevel()
            self.show_error_popup(topParent, "ERROR: Value Error", "Please enter a valid number.")
            return None
        
    def countdown_thread(self, start_count, buttontorun, textbox):
        """Countdown in separate thread"""
        button_list = [self.buttonCWC1, self.buttonCCWC1, self.buttonCWC2, self.buttonCCWC2]
        
        for i in range(start_count, 0, -1):
            print(i)
            time.sleep(1)

        # Use app.after to safely update GUI from thread
        self.app.after(0, lambda: self._finish_motor_run_threaded(buttontorun, textbox, button_list))

    def _finish_motor_run_threaded(self, buttontorun, textbox, button_list):
        """Finish motor run - called from main thread"""
        buttontorun.configure(text="Run Conveyor(s) (C1/C2)",state="normal")
        print("Done Running!")
        self.stop_motors()
        
        for button in button_list:
            button.configure(fg_color="#979da2", hover_color="#3B8ED0")
        
        textbox.delete("0.0", "end")
        textbox.configure(state="normal")

    def button_callback(self, button):
        """Create callback function for button color toggle"""
        def toggle_color():
            # Get current color
            current_color = button.cget("fg_color")
            # Toggle between blue and green
            if current_color == "#979da2" or current_color == "#3B8ED0":  # Default blue
                button.configure(fg_color="green", hover_color="#0B662B")
            else:
                button.configure(fg_color="#979da2", hover_color="#3B8ED0")
        return toggle_color

    def button_run(self, buttontorun, textbox):
        """Handle the run button functionality with threading"""
        run_time = self.get_number_from_textbox(textbox)
        textbox.configure(state="disabled")
        
        button_color = [self.buttonCWC1.cget("fg_color"), self.buttonCCWC1.cget("fg_color"), self.buttonCWC2.cget("fg_color"), self.buttonCCWC2.cget("fg_color")]
        
        if run_time is None:
            topParent = self.buttonBackground.winfo_toplevel()
            self.show_error_popup(topParent, "ERROR: No Time Input", "Please enter the time to run conveyor(s).")
            textbox.configure(state="normal")
        elif 'green' in button_color:
            if ((button_color[0] == 'green' and button_color[1] == 'green') or 
                (button_color[2] == 'green' and button_color[3] == 'green')):
                topParent = self.buttonBackground.winfo_toplevel()
                self.show_error_popup(topParent, "ERROR: Input Error", "Please click only one direction for each conveyor.")
                textbox.configure(state="normal")
            else:
                button_state_array = [1 if 'green' in color else 0 for color in button_color]
                self.move_motor(button_state_array)
                buttontorun.configure(text="Running...", state="disabled")
                
                # Start countdown in separate thread
                countdown_thread = threading.Thread(target=self.countdown_thread, args=(int(run_time), buttontorun, textbox))
                countdown_thread.daemon = True  # Thread will close when main program closes
                countdown_thread.start()
                textbox.configure(state="normal")
                textbox.delete("0.0", "end")  # delete all text
        else: 
            topParent = self.buttonBackground.winfo_toplevel()
            self.show_error_popup(topParent, "ERROR: No Input Error", "Please select one of the buttons for the direction of the conveyor(s).")
            textbox.configure(state="normal")

    def video_feed(self):
        """Updates the video feed on the Tkinter canvas."""
        
        # Capture frame from the camera
        frame = self.picam2.capture_array()
        frame = Image.fromarray(frame).convert("RGB")  # Convert RGBA to RGB
        
        # Resize and convert to PhotoImage
        frame = frame.resize((300, 200))
        frame = ImageTk.PhotoImage(frame)
        
        # Update the video canvas with the new frame
        self.video_canvas.create_image(0, 0, anchor=ctk.NW, image=frame)
        self.video_canvas.image = frame
        
        # Schedule the next update
        app.after(10, self.video_feed)

    def run(self):
        """Start the application main loop"""
        self.app.mainloop()


# Create and run the application
if __name__ == "__main__":
    app = ctk.CTk(fg_color="#e5e0d8")
    controller = ConveyorController(app)
    controller.run()
