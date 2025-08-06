import torch, time, sys, os, threading, json
from datetime import datetime
import customtkinter as ctk
from PIL import ImageTk
from get_size import calculate_size, determine_size, load_json_file
from motor_controller import MotorController
from ai_analyzer import AIAnalyzer
from camera_manager import CameraManager
from formula_controller import FormulaController
# RCNN is in controller_v2.py
# from rcnn_size import MangoMeasurementSystem
    
class ConveyorControllerV2:
    def __init__(self, app, data):
        self.colors = data['colors']
        self.errors = data['errors']
        self.names = data['names']
        self.app = app
        self.app.title("Conveyor Controller")
        self.WINDOW_SIZE = {'length':1200, 'width':700}
        self.app.geometry(f"{self.WINDOW_SIZE['length']}x{self.WINDOW_SIZE['width']}")
        self.app.fg_color = self.colors["main_app_background"]
        self.DEFAULT_BOLD = ctk.CTkFont(family=ctk.ThemeManager.theme["CTkFont"]["family"],
                                        size=ctk.ThemeManager.theme["CTkFont"]["size"],
                                        weight="bold")
        self.TITLE_FONT_SIZE = 20
        self.TITLE_FONT = ctk.CTkFont(family=ctk.ThemeManager.theme["CTkFont"]["family"],
                                      size=self.TITLE_FONT_SIZE,weight="bold")
        self.RIPENESS_SCORES = {'yellow': 1.0, 'yellow_green': 2.0, 'green': 3.0}
        self.BRUISES_SCORES = {'bruised': 1.5, 'unbruised': 3.0}
        self.SIZE_SCORES = {'small': 1.0, 'medium': 2.0, 'large': 3.0}
        self.recorded_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.top_final_score = 0
        self.bottom_final_score = 0
        self.priority_enabled = True
        self.BUTTON_WIDTH = 180
        self.BUTTON_HEIGHT = 40
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.ai = AIAnalyzer(self.device, self.RIPENESS_SCORES, self.BRUISES_SCORES, self.SIZE_SCORES)
        self.mc = MotorController()
        self.picam2 = CameraManager()
        self.formula = FormulaController(self.RIPENESS_SCORES, self.BRUISES_SCORES, self.SIZE_SCORES)
        # # TODO: check in rpi
        # RCNN_PATH = "mango_detection_model.pth"
        # self.rcnn_size = MangoMeasurementSystem(RCNN_PATH)
        self.init_ui()
    
    def init_ui(self):
        INIT_WEIGHT=1
        txt = self.names["video"]
        self.app.grid_columnconfigure(0, weight=INIT_WEIGHT)
        self.app.grid_columnconfigure(1, weight=INIT_WEIGHT)
        
        self.main_frame = ctk.CTkFrame(self.app, fg_color=self.colors["frame_background"])
        self.main_frame.grid(row=0, column=1, padx=txt["padx"], pady=txt["pady"], sticky="ns")
        self.view_frame = ctk.CTkFrame(self.app, fg_color=self.colors["frame_background"])
        self.view_frame.grid(row=0, column=0, padx=txt["padx"], pady=txt["pady"], sticky="ns")
        
        self.init_user_priority_frame(self.main_frame)
        self.init_control_frame(self.main_frame)
        self.init_video_frame(self.view_frame)
        self.picam2.set_controller_vars(self.app, self.video_canvas)
        self.picam2.get_video_feed()
        

    def init_control_frame(self, main_frame):
        txt = self.names["control"]
        left_frame = ctk.CTkFrame(main_frame)
        left_frame.grid(row=0, column=0, padx=txt["padx"], pady=txt["pady"])
        col_index=0
        row_index=0
        self.button_reset = ctk.CTkButton(left_frame, text=txt["reset"], width=self.BUTTON_WIDTH,
                                          height=self.BUTTON_HEIGHT, 
                                          fg_color=self.colors["default_button"],
                                          hover_color=self.colors["hover_red"]
                                         ,font=self.DEFAULT_BOLD)
        self.button_reset.configure(command=self.reset_program)
        self.button_reset.grid(row=row_index, column=col_index, padx=txt["padx"],
                               pady=txt["pady"], sticky="nswe")
        col_index += 1
        self.button_exit = ctk.CTkButton(left_frame, text=txt["exit"], width=self.BUTTON_WIDTH,
                                         height=self.BUTTON_HEIGHT,
                                         fg_color=self.colors["bg_red"],
                                         hover_color=self.colors["hover_red"]
                                        ,font=self.DEFAULT_BOLD)
        self.button_exit.configure(command=self.exit_program)
        self.button_exit.grid(row=row_index, column=col_index, padx=txt["padx"],
                              pady=txt["pady"], sticky="nswe")

        row_index += 1
        col_index = 0
        self.button_cwc1 = ctk.CTkButton(left_frame, text=txt["cwc1"],
                                         width=self.BUTTON_WIDTH, height=self.BUTTON_HEIGHT,
                                         fg_color=self.colors["default_button"]
                                        ,font=self.DEFAULT_BOLD, state="disabled")
        self.button_cwc1.configure(command=self.toggle_button_color(self.button_cwc1))
        self.button_cwc1.grid(row=row_index, column=col_index, padx=txt["padx"],
                              pady=txt["pady"], sticky="nswe")
        col_index += 1
        self.button_ccwc1 = ctk.CTkButton(left_frame, text=txt["ccwc1"],
                                          width=self.BUTTON_WIDTH, height=self.BUTTON_HEIGHT,
                                          fg_color=self.colors["default_button"]
                                         ,font=self.DEFAULT_BOLD, state="disabled")
        self.button_ccwc1.configure(command=self.toggle_button_color(self.button_ccwc1))
        self.button_ccwc1.grid(row=row_index, column=col_index, padx=txt["padx"], 
                               pady=txt["pady"], sticky="nswe")

        row_index += 1
        self.button_cwc2 = ctk.CTkButton(left_frame, text=txt["cwc2"],
                                         width=self.BUTTON_WIDTH, height=self.BUTTON_HEIGHT,
                                         fg_color=self.colors["default_button"]
                                        ,font=self.DEFAULT_BOLD, state="disabled")
        self.button_cwc2.configure(command=self.toggle_button_color(self.button_cwc2))
        col_index = 0
        self.button_cwc2.grid(row=row_index, column=col_index, padx=txt["padx"],
                              pady=txt["pady"], sticky="nswe")
        self.button_ccwc2 = ctk.CTkButton(left_frame, text=txt["ccwc2"],
                                          width=self.BUTTON_WIDTH, height=self.BUTTON_HEIGHT, 
                                          fg_color=self.colors["default_button"]
                                         ,font=self.DEFAULT_BOLD, state="disabled")
        col_index += 1
        self.button_ccwc2.configure(command=self.toggle_button_color(self.button_ccwc2))
        self.button_ccwc2.grid(row=row_index, column=col_index, padx=txt["padx"],
                               pady=txt["pady"], sticky="nswe")

        row_index += 1
        col_index = 0
        self.time_txt_button = ctk.CTkButton(left_frame, text=txt["move_time"],
                                             hover="disabled", font=self.DEFAULT_BOLD,
                                             fg_color=self.colors["text_background"],
                                             text_color=self.colors["text_color"]) 
        self.time_txt_button.grid(row=row_index, column=col_index, columnspan=2,
                                  padx=txt["padx"], pady=txt["pady"],
                                  sticky="nswe")

        row_index += 1

        self.textbox = ctk.CTkComboBox(left_frame, 
                                       values=txt["option_val"],
                                       width=self.BUTTON_WIDTH,
                                       height=self.BUTTON_HEIGHT)
        self.textbox.set(txt["default_val"])
        self.textbox.grid(row=row_index, column=col_index, columnspan=2, 
                                 padx=txt["padx"], pady=txt["pady"], sticky="nswe")

        row_index += 1
        self.button_background = ctk.CTkButton(left_frame, text=txt["button_bg"],
                                               width=self.BUTTON_WIDTH * 2 + 40,
                                               height=self.BUTTON_HEIGHT, 
                                              fg_color=self.colors["default_button"],
                                               hover_color=self.colors["hover_gray"], 
                                               font=self.DEFAULT_BOLD)
        self.button_background.configure(command=self.set_background_image)
        self.button_background.grid(row=row_index, column=col_index, columnspan=2,
                                    padx=txt["padx"], pady=txt["pady"],
                                    sticky="nswe")
        
        row_index += 1
        self.button_run = ctk.CTkButton(left_frame, text=txt["button_run"], 
                                        width=self.BUTTON_WIDTH * 2 + 40,
                                        height=self.BUTTON_HEIGHT, 
                                        fg_color=self.colors["default_button"], 
                                        hover_color=self.colors["hover_gray"]
                                       ,font=self.DEFAULT_BOLD, state="disabled")
        self.button_run.configure(command=lambda: self.init_run_conveyor(self.button_run, self.textbox))
        self.button_run.grid(row=row_index, column=col_index, columnspan=2, padx=txt["padx"],
                             pady=txt["pady"], sticky="nswe")

        row_index += 1
        self.button_side1 = ctk.CTkButton(left_frame, text=txt["button_s1"],
                                          width=self.BUTTON_WIDTH, 
                                          height=self.BUTTON_HEIGHT,
                                          fg_color=self.colors["default_button"], 
                                          hover_color=self.colors["hover_gray"],
                                          state="disabled",font=self.DEFAULT_BOLD)
        self.button_side1.configure(command=self.picture_side1)
        self.button_side1.grid(row=row_index, column=col_index, padx=txt["padx"],
                               pady=txt["pady"], sticky="nswe")

        self.button_side2 = ctk.CTkButton(left_frame, text=txt["button_s2"],
                                          width=self.BUTTON_WIDTH, height=self.BUTTON_HEIGHT, 
                                          fg_color=self.colors["default_button"], 
                                          hover_color=self.colors["hover_gray"],
                                          state="disabled",font=self.DEFAULT_BOLD)
        self.button_side2.configure(command=self.picture_side2)
        col_index += 1
        self.button_side2.grid(row=row_index, column=col_index, padx= txt["padx"],
                               pady=txt["pady"], sticky="nswe")
    
    def init_video_frame(self, frame):
        row_index=0
        col_index=0
        PADDING_X=7
        PADDING_Y=7
        txt = self.names["video"]
        video_frame = ctk.CTkFrame(frame)
        video_frame.grid(row=row_index, column=col_index, padx=txt["padx"], pady=txt["pady"], sticky="nsew")
        results_vid_frame = ctk.CTkFrame(video_frame, fg_color=self.colors["transparent"])
        results_vid_frame.grid(row=row_index, column=col_index, padx=txt["padx"]/2, pady=txt["pady"]/2,
                               sticky="nsew")
        
        video_button = ctk.CTkButton(results_vid_frame, text=txt["vid_feed"], width=300,
                                     height=self.BUTTON_HEIGHT, hover="disabled",
                                     font=self.TITLE_FONT,
                                     fg_color=self.colors["text_background"], 
                                     text_color=self.colors["text_color"])
        video_button.grid(row=row_index, column=col_index, padx=txt["padx"]/2, pady=txt["pady"]/2, sticky="ns")
        row_index += 1
        self.video_canvas = ctk.CTkCanvas(video_frame, width=300, height=200)
        self.video_canvas.grid(row=row_index, column=col_index, padx=txt["padx"]/2,
                               pady=txt["pady"]/2, sticky="ns")

        row_index = 0
        col_index += 1
        results_frame = ctk.CTkFrame(video_frame, fg_color=self.colors["transparent"])
        results_frame.grid(row=row_index, columnspan=2, column=col_index, padx=txt["padx"]/2,
                           pady=txt["pady"]/2, sticky="nsew")
        col_index = 0
        results_button = ctk.CTkButton(results_frame, text=txt["list_results"], width=300,
                                       height=self.BUTTON_HEIGHT, hover="disabled",
                                       font=self.TITLE_FONT,
                                       fg_color=self.colors["text_background"], 
                                       text_color=self.colors["text_color"])
        results_button.grid(row=row_index, column=col_index, padx=txt["padx"]/2,
                            pady=txt["pady"]/2, stick="nswe")
        
        row_index += 1
        col_index += 1
        dynamic_results_frame = ctk.CTkFrame(video_frame)
        dynamic_results_frame.grid(row=row_index, columnspan=2, column=col_index,
                                   padx=txt["padx"], pady=txt["pady"], sticky="nsew")
        self.results_data = ctk.CTkLabel(dynamic_results_frame, 
                                         text=txt["final_results"],
                                         compound="left", justify="left")
        col_index = 0
        self.results_data.grid(row=row_index, columnspan=2, column=col_index,
                               padx=txt["padx"], pady=txt["pady"], sticky="nsew")
        
        row_index = 1
        col_index = 0
        side_frame = ctk.CTkFrame(frame, width=300, height=200)
        side_frame.grid(row=row_index, column=col_index, padx=txt["padx"],
                        pady=txt["pady"], sticky="ns")
        self.side1_button = ctk.CTkButton(side_frame, text=txt["side1"],
                                          width=300, height=self.BUTTON_HEIGHT, 
                                          hover="disabled", font=self.TITLE_FONT,
                                          fg_color=self.colors["text_background"], 
                                          text_color=self.colors["text_color"])
        self.side1_button.grid(row=row_index, column=col_index, padx=txt["padx"],
                               pady=txt["pady"], sticky="nswe")
        self.side2_button = ctk.CTkButton(side_frame, text=txt["side2"],
                                          width=300, height=self.BUTTON_HEIGHT, 
                                          hover="disabled", font=self.TITLE_FONT,
                                          fg_color=self.colors["text_background"], 
                                          text_color=self.colors["text_color"])
        col_index += 1
        self.side2_button.grid(row=row_index, column=col_index, padx=txt["padx"],
                               pady=txt["pady"], sticky="nswe")
        
        row_index += 1
        col_index = 0
        self.side1_box = ctk.CTkCanvas(side_frame, width=300,
                                       height=200, bg=self.colors["text_background"])
        self.side1_box.grid(row=row_index, column=col_index, padx=txt["padx"], 
                            pady=txt["pady"], sticky="nswe")
        self.side2_box = ctk.CTkCanvas(side_frame, width=300, height=200,
                                       bg=self.colors["text_background"])
        col_index += 1
        self.side2_box.grid(row=row_index, column=col_index, padx=txt["padx"],
                            pady=txt["pady"], sticky="nswe")
        
        row_index += 1
        col_index = 0
        results_txt_frame1 = ctk.CTkFrame(side_frame)
        results_txt_frame1.grid(row=row_index, column=col_index, padx=txt["padx"],
                                pady=txt["pady"], sticky="nswe")
        self.side1_results = ctk.CTkLabel(results_txt_frame1, 
                                          text=txt["side_results"],
                                          compound="left", justify="left")
        row_index = 0
        col_index = 0
        self.side1_results.grid(row=row_index, column=col_index, padx=txt["padx"],
                                pady=txt["pady"], sticky="nswe")
        row_index += 3
        col_index += 1
        results_txt_frame2 = ctk.CTkFrame(side_frame)
        results_txt_frame2.grid(row=row_index, column=col_index, padx=txt["padx"],
                                pady=txt["pady"], sticky="nswe")
        self.side2_results = ctk.CTkLabel(results_txt_frame2, 
                                          text=txt["side_results"],
                                          compound="left", justify="left")
        row_index = 0
        self.side2_results.grid(row=row_index, column=col_index, padx=txt["padx"],
                                pady=txt["pady"], sticky="nswe")
        
        return video_frame
    
    def init_user_priority_frame(self, main_frame):
        row_index=6
        col_index=0
        WIDTH_COMBOBOX=120
        TXT_WIDTH=80
        txt = self.names["priority"]
        frame_choices = ctk.CTkFrame(main_frame)
        frame_choices.grid(row=row_index, column=col_index, padx=txt["padx"],
                           pady=txt["pady"], sticky="nswe")
        frame_choices.columnconfigure(0, weight=1)
        frame_choices.columnconfigure(1, weight=1) 
        frame_choices.columnconfigure(2, weight=1)
        priority_txt = ctk.CTkButton(frame_choices, text=txt["input_user"],
                                     hover="disabled", font=self.DEFAULT_BOLD, 
                                     fg_color=self.colors["text_background"], 
                                     text_color=self.colors["text_color"])
        priority_txt.grid(row=row_index, column=col_index, padx=txt["padx"], pady=txt["pady"],
                          sticky="nswe", columnspan=3)   
        row_index+=1
        
        ripeness_txt = ctk.CTkButton(frame_choices, text=txt["ripeness"], width=TXT_WIDTH,
                                     hover="disabled", font=self.DEFAULT_BOLD,
                                     fg_color=self.colors["text_background"], 
                                     text_color=self.colors["text_color"])
        ripeness_txt.grid(row=row_index, column=col_index,
                          padx=txt["padx"], pady=txt["pady"], sticky="ew")
        
        self.ripeness_combo = ctk.CTkComboBox(frame_choices, 
                                              values=txt["option_val"],
                                              width=WIDTH_COMBOBOX)
        self.ripeness_combo.set(txt["default_val"])
        self.ripeness_combo.grid(row=row_index+1, column=col_index,
                                 padx=txt["padx"], pady=txt["pady"], sticky="nswe")

        col_index+=1
        bruises_txt = ctk.CTkButton(frame_choices, text=txt["bruises"], width=TXT_WIDTH,
                                    hover="disabled", font=self.DEFAULT_BOLD, 
                                    fg_color=self.colors["text_background"], 
                                    text_color=self.colors["text_color"])
        bruises_txt.grid(row=row_index, column=col_index, padx=txt["padx"],
                         pady=txt["pady"], sticky="ew")
        self.bruises_combo = ctk.CTkComboBox(frame_choices, 
                                             values=txt["option_val"],
                                             width=WIDTH_COMBOBOX)
        self.bruises_combo.set(txt["default_val"])
        self.bruises_combo.grid(row=row_index+1, column=col_index,
                                padx=txt["padx"], pady=txt["pady"], sticky="nswe")
        
        col_index+=1
        size_txt = ctk.CTkButton(frame_choices, text=txt["size"], width=TXT_WIDTH,
                                 hover="disabled", font=self.DEFAULT_BOLD,
                                 fg_color=self.colors["text_background"], 
                                 text_color=self.colors["text_color"])
        size_txt.grid(row=row_index, column=col_index, padx=txt["padx"],
                      pady=txt["pady"], sticky="ew")
 
        self.size_combo = ctk.CTkComboBox(frame_choices, 
                                          values=txt["option_val"],
                                          width=WIDTH_COMBOBOX)
        self.size_combo.set(txt["default_val"])
        self.size_combo.grid(row=row_index+1, column=col_index, padx=txt["padx"],
                             pady=txt["pady"], sticky="nswe")

        row_index+=2
        col_index=0
        combo_boxes = {'ripeness': self.ripeness_combo,
                       'bruises': self.bruises_combo,
                       'size': self.size_combo}
        self.button_enter = ctk.CTkButton(frame_choices, text=txt["enter"],
                                          command=lambda:self.enter_priority(combo_boxes), 
                                          fg_color=self.colors["green"],
                                          hover_color=self.colors["green_hover"],
                                          font=self.DEFAULT_BOLD)
        self.button_enter.grid(row=row_index, column=col_index, padx=txt["padx"],
                               pady=txt["pady"], sticky="nswe", columnspan=3)
        row_index+=1
        self.button_help = ctk.CTkButton(frame_choices, text=txt["help"],
                                         command=self.get_help_page_info,
                                         fg_color=self.colors["default_button"],
                                         hover_color=self.colors["hover_gray"],
                                         font=self.DEFAULT_BOLD)
        self.button_help.grid(row=row_index, column=col_index, padx=txt["padx"],
                              pady=txt["pady"], sticky="nswe", columnspan=3)
        
        return frame_choices
        
    def get_help_page_info(self):
        #TODO: FILL UP THE HELP PAGE ALSO ITS BROKEN MB 
        popup = ctk.CTkToplevel()
        length = self.WINDOW_SIZE['length']
        width = self.WINDOW_SIZE['width']
        popup.geometry(f"{length}x{width}")
        close_button = ctk.CTkButton(popup, text="Close", command=popup.destroy)
        close_button.pack(pady=10)
        
        return class_labels[predicted.item()]
    
    def set_background_image(self):
        if self.priority_enabled == False:
            txt = self.names["control"]
            self.recorded_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            
            background_img = self.picam2.get_image()
            background_img.save(f"{self.recorded_time}_background.png")
            
            button_configs = {
                self.button_background: "disabled",
                self.button_run: "normal",
                self.button_side1: "normal", 
                self.button_enter: "disabled",
                self.button_cwc1: "normal",
                self.button_cwc2: "normal",
                self.button_ccwc1: "normal",
                self.button_ccwc2: "normal"
            }
            
            for button, state in button_configs.items():
                button.configure(state=state)
                
            self.button_background.configure(text=txt["button_dn"])
            vid_txt = self.names["video"]
            self.results_data.configure(text=vid_txt["final_results"])
            self.side1_results.configure(text=vid_txt["side_results"])
            self.side2_results.configure(text=vid_txt["side_results"])
        else:
            top_parent = self.button_background.winfo_toplevel()
            self.set_error_pop_up(top_parent, self.errors["null_priority"]["title"],
                                  self.errors["null_priority"]["message"])

    def set_error_pop_up(self, parent, title="Error", message="An error occurred"):
        popup = ctk.CTkToplevel(parent)
        popup.title(title)
        size = {'l':300, 'w':150}
        popup.geometry(f"{size['l']}x{size['w']}")
        popup.fg_color = self.colors["main_app_background"]
        popup.resizable(False, False)
        popup.transient(parent)
        PX = 20
        PY = 20
        WRAPLENGTH = 250
        label = ctk.CTkLabel(popup, text=message, wraplength=WRAPLENGTH, 
                             font=self.DEFAULT_BOLD,
                             text_color=self.colors["text_color"])
        label.pack(pady=PY, padx=PX)
        
        ok_button = ctk.CTkButton(popup, text="Ok", command=popup.destroy,
                                  fg_color=self.colors["default_button"],
                                  hover_color=self.colors["hover_gray"],
                                  font=self.DEFAULT_BOLD)
        ok_button.pack(pady=PY-PX/2)
        
        popup.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (popup.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (popup.winfo_height() // 2)
        popup.geometry(f"+{x}+{y}")
    
    def enter_priority(self, combo_boxes):
        [all_valid, error_log] = self.formula.is_valid_priority(combo_boxes)
        if all_valid:
            if not self.priority_enabled:
                txt = self.names["priority"]["default_val"]
                self.ripeness_combo.configure(state="normal")
                self.bruises_combo.configure(state="normal")
                self.size_combo.configure(state="normal")
                self.ripeness_combo.set(txt)
                self.bruises_combo.set(txt)
                self.size_combo.set(txt)
                self.button_enter.configure(text="Enter")
                self.priority_enabled = True
            else:
                self.ripeness_combo.configure(state="disabled")
                self.bruises_combo.configure(state="disabled")
                self.size_combo.configure(state="disabled")
                self.button_enter.configure(text="Cancel", fg_color=self.colors["bg_red"], hover_color=self.colors["hover_red"])
                self.formula.set_input_priority(self.get_input_priorities())
                self.priority_enabled = False
        else:
            top_parent = self.button_background.winfo_toplevel()
            self.set_error_pop_up(top_parent, self.errors[error_log]["title"],
                                          self.errors[error_log]["message"])
        
    def reset_program(self):
        print("Resetting")
        self.mc.clean_gpio()
        self.picam2.stop_camera()
        os.execv(sys.executable, [sys.executable] + sys.argv)

    def exit_program(self):
        print("Goodbye")
        self.mc.clean_gpio()
        self.picam2.stop_camera()
        sys.exit(0)
        return priorities

    def picture_side1(self):
        print("Process and pictured side 1")
        s1 = self.ai.get_is_s1()
        t_img = self.picam2.get_image()
        t_img.save(f"{self.recorded_time}_top.png")
        f_dt = self.recorded_time
        t_r = self.ai.get_predicted_class(t_img, self.ai.get_is_ripeness())
        t_b = self.ai.get_predicted_class(t_img, self.ai.get_is_bruises())
        imgs = {'m': f"{f_dt}_top.png",
                'g': f"{f_dt}_background.png",
                'f_dt': f_dt}
        t_x, t_y = calculate_size(imgs, s1)
        # # TODO: check this rcnn and then display on ctk
        # print("\n\nRCNN")
        # rcnn_size = self.rcnn_size.get_size(imgs['m'])
        # print("\n\n")
        print(f"Top Width: {t_x:.2f} cm, Top Length: {t_y:.2f} cm")
        t_s = determine_size(t_x, t_y) 
        priorities = self.formula.get_priorities()
        ai_pred = {'ripeness': t_r,
                   'bruises': t_b,
                   'size': t_s}
        num_grade = self.ai.get_overall_grade(ai_pred, priorities)
        self.top_final_score=num_grade
        letter_grade = self.formula.get_grade_letter(num_grade)
        results_data = {'img': t_img,
                        'num_grade': num_grade,
                        'letter_grade': letter_grade}
        self.set_textbox_results(results_data, ai_pred, s1)
        
        self.button_side1.configure(state="disabled")
        self.button_side2.configure(state="normal")

    def picture_side2(self):
        print("Process and pictured side 2")
        s2 = self.ai.get_is_s2()
        b_img = self.picam2.get_image()
        b_img.save(f"{self.recorded_time}_bottom.png")
        f_dt = self.recorded_time
        b_r = self.ai.get_predicted_class(b_img, self.ai.get_is_ripeness())
        b_b = self.ai.get_predicted_class(b_img, self.ai.get_is_bruises())
        imgs = {'m': f"{f_dt}_bottom.png",
                'g': f"{f_dt}_background.png",
                'f_dt': f_dt}
        b_x, b_y = calculate_size(imgs, s2)
        # # TODO: check this rcnn and then display it on ctk
        # print("\n\nRCNN")
        # self.rcnn_size.get_size(imgs['m'])
        # print("\n\n")
        print(f"Bottom Width: {b_x:.2f} cm, Bottom Length: {b_y:.2f} cm")
        b_s = determine_size(b_x, b_y) 
        
        priorities = self.formula.get_priorities()
        ai_pred = {'ripeness': b_r,
                   'bruises': b_b,
                   'size': b_s}
        num_grade = self.ai.get_overall_grade(ai_pred, priorities)
        self.bottom_final_score=num_grade
        letter_grade = self.formula.get_grade_letter(num_grade)
        results_data = {'img': b_img,
                        'num_grade': num_grade,
                        'letter_grade': letter_grade}
        self.set_textbox_results(results_data, ai_pred, s2)
        
        ave_score = (self.top_final_score + self.bottom_final_score) / 2
        ave_letter = self.formula.get_grade_letter(ave_score)
        grade_info = self.formula.get_grade_formula_dict()
        grade_string = "\n".join([f"Grade {grade}: {info}" for grade, info in grade_info.items()])
        print(grade_string)
        self.results_data.configure(
            text=(f"Top Score: {self.top_final_score:.2f}\n" +
                f"Bottom Score: {self.top_final_score:.2f}\n" +
                grade_string + f"\n" +
                f"Average Score: {ave_score:.2f}\n" + 
                f"Predicted Grade: {ave_letter}"))
        
        button_configs = {
            self.button_background: "normal",
            self.button_side2: "disabled", 
            self.button_enter: "normal"
        }
        self.button_background.configure(text="Capture Background")
        for button, state in button_configs.items():
            button.configure(state=state)
     
    def get_input_priorities(self):
        arr = {
            'ripeness': float(self.ripeness_combo.get()),
            'bruises': float(self.bruises_combo.get()),
            'size': float(self.size_combo.get())}
        return arr
    
    def set_textbox_results(self, results_data, ai_pred, is_top):
        image = results_data['img']
        ripeness = ai_pred['ripeness']
        bruises = ai_pred['bruises']
        size = ai_pred['size']
        score = results_data['num_grade']
        letter = results_data['letter_grade']
        def update():
            if is_top:
                self.side1_results.configure(
                    text=f"Ripeness: {ripeness}\nBruises: {bruises}\nSize: {size}\nScore: {letter} or {score} ")
                top_photo = ImageTk.PhotoImage(image.resize((300, 200)))
                self.side1_box.create_image(0, 0, anchor=ctk.NW, image=top_photo)
                self.side1_box.image = top_photo  
            else:
                self.side2_results.configure(text=f"Ripeness: {ripeness}\nBruises: {bruises}\nSize: {size}\nScore: {letter} or {score} ")
                bottom_photo = ImageTk.PhotoImage(image.resize((300, 200)))
                self.side2_box.create_image(0, 0, anchor=ctk.NW, image=bottom_photo)
                self.side2_box.image = bottom_photo  
        self.app.after(0, update)

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
            self.set_error_pop_up(top_parent, self.errors["value_error"]["title"],
                                  self.errors["value_error"]["message"])
            return None
        
    def set_countdown_thread(self, start_count, buttontorun, textbox):
        button_list = [self.button_cwc1, self.button_ccwc1, self.button_cwc2, self.button_ccwc2]
        SLEEP_TIME = 1
        STOP_TIME = 0
        STEP_TIME = -1
        for i in range(start_count, STOP_TIME, STEP_TIME):
            print(i)
            time.sleep(SLEEP_TIME)
        self.app.after(STOP_TIME, 
                       lambda: self.set_motor_to_finished(buttontorun, textbox, button_list))

    def set_motor_to_finished(self, buttontorun, textbox, button_list):
        buttontorun.configure(text="Run Conveyor(s) (C1/C2)",state="normal")
        print("Done Running!")
        self.mc.stop_motors()
        for button in button_list:
            button.configure(fg_color=self.colors["default_button"], 
                             hover_color=self.colors["button_hover_blue"])
        default=self.names["control"]["default_val"]
        textbox.set(default)
        textbox.configure(state="normal")

    def toggle_button_color(self, button):
        def toggle_color():
            current_color = button.cget("fg_color")
            if (current_color == self.colors["default_button"] or
                current_color == self.colors["button_hover_blue"]):
                button.configure(fg_color="green", hover_color=self.colors["green_hover"])
            else:
                button.configure(fg_color=self.colors["default_button"], 
                                 hover_color=self.colors["button_hover_blue"])

        return toggle_color

    def init_run_conveyor(self, buttontorun, textbox):
        top_parent = self.button_background.winfo_toplevel()
        if (self.formula.is_number(textbox)):
            run_time = float(self.textbox.get())
            textbox.configure(state="disabled")
            button_color = [self.button_cwc1.cget("fg_color"), 
                            self.button_ccwc1.cget("fg_color"),
                            self.button_cwc2.cget("fg_color"),
                            self.button_ccwc2.cget("fg_color")]
            
            if run_time is None:
                self.set_error_pop_up(top_parent, self.errors["null_time"]["title"],
                                      self.errors["null_time"]["message"])
                textbox.configure(state="normal")
            elif self.colors["green"] in button_color:
                if ((button_color[0] == self.colors["green"] and button_color[1] == self.colors["green"]) or 
                    (button_color[2] == self.colors["green"] and button_color[3] == self.colors["green"])):
                    self.set_error_pop_up(top_parent, self.errors["input_error"]["title"],
                                          self.errors["input_error"]["message"])
                    textbox.configure(state="normal")
                else:
                    button_state_array = [1 if self.colors["green"] in color else 0 for color in button_color]
                    self.mc.set_motors(button_state_array)
                    buttontorun.configure(text="Running...", state="disabled")
                    set_countdown_thread = threading.Thread(target=self.set_countdown_thread, 
                                                            args=(int(run_time), 
                                                            buttontorun, textbox))
                    set_countdown_thread.daemon = True  
                    set_countdown_thread.start()
                    textbox.configure(state="normal")
            else: 
                self.textbox.set("1.0")
                self.set_error_pop_up(top_parent, self.errors["null_button"]["title"],
                                      self.errors["null_button"]["message"])
                textbox.configure(state="normal")

        else:
            self.set_error_pop_up(top_parent, self.errors["not_number"]["title"],
                                  self.errors["not_number"]["message"])
            textbox.configure(state="normal")

    def run(self):
        self.app.mainloop()

if __name__ == "__main__":
    json_files = {
        'colors': "colors_str.json",
        'errors': "errors_str.json",
        'names': "naming.json"
    }
    data = {}
    for key, filename in json_files.items():
        data[key] = load_json_file(filename)
    ctk.set_appearance_mode("light")
    app = ctk.CTk(fg_color=data["colors"]["main_app_background"])
    controller = ConveyorControllerV2(app, data)
    controller.run()
