from PIL import Image
from PIL import ImageTk
import customtkinter as ctk
import json

class Help(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Help Information")
        self.geometry("800x600")
        
        # create a main frame to hold all content
        self.main_frame = ctk.CTkScrollableFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        close_button = ctk.CTkButton(self, text="Close",
                                    fg_color="#979da2",
                                    hover_color="#6e7174", 
                                    command=self.destroy)
        close_button.pack(pady=10)
            
        try:
            with open("help_info.json", "r") as json_file:
                help_info = json.load(json_file) 
                print(f"Loaded {len(help_info)} help entries")
                
                # create and place the entries
                for i, entry in enumerate(help_info):
                    img_path = entry['img_path']
                    name = entry['name']
                    desc_text = entry['text']
                    
                    # create a frame for each entry
                    entry_frame = ctk.CTkFrame(self.main_frame)
                    entry_frame.grid(row=i, column=0, padx=10, pady=10, sticky="ew")
                    
                    # config the entry frame grid
                    entry_frame.grid_columnconfigure(1, weight=1)  # Name column
                    entry_frame.grid_columnconfigure(2, weight=3)  # Description column
                    
                    # name label
                    name_label = ctk.CTkLabel(entry_frame, text=name, font=ctk.CTkFont(weight="bold"))
                    name_label.grid(row=0, column=1, padx=10, pady=5, sticky="nsew")
                    
                    # desc text (using textbox for multiline)
                    desc_textbox = ctk.CTkTextbox(entry_frame, height=80, wrap="word")
                    desc_textbox.insert("1.0", desc_text)
                    desc_textbox.configure(state="disabled")  # to make it read-only
                    desc_textbox.grid(row=0, column=2, padx=10, pady=5, sticky="nsew")
                    
                    # loading and display image if path exists
                    try:
                        pil_image = Image.open(img_path)
                        ctk_image = ctk.CTkImage(
                            light_image=pil_image, 
                            dark_image=pil_image, 
                            size=(200, 75)
                        )
                        image_label = ctk.CTkLabel(entry_frame, image=ctk_image, text="")
                        image_label.grid(row=0, column=0, columnspan=1, padx=10, pady=5, sticky="nsew")
                    except Exception as e:
                        print(f"Could not load image: {img_path}, Error: {e}")
                        error_label = ctk.CTkLabel(
                            entry_frame, 
                            text=f"Image not found: {img_path}", 
                            text_color="red"
                        )
                        error_label.grid(row=0, column=0, columnspan=2, padx=10, pady=5)

        except FileNotFoundError:
            error_label = ctk.CTkLabel(
                self.main_frame, 
                text="help_info.json file not found!", 
                text_color="red",
                font=ctk.CTkFont(size=16, weight="bold")
            )
            error_label.pack(pady=20)
        except Exception as e:
            error_label = ctk.CTkLabel(
                self.main_frame, 
                text=f"Error loading help info: {str(e)}", 
                text_color="red"
            )
            error_label.pack(pady=20)


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("my_app")
        self.geometry("500x600")
        self.button = ctk.CTkButton(self, text="POPUP", command=self.help_popup)
        self.button.pack(pady=20)
        
    def help_popup(self):
        help_page = Help(self)
        help_page.grab_set()  # Make the help window modal

if __name__ == "__main__":
    app = App()
    app.mainloop()
