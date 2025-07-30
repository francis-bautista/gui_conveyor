import torch
from PIL import Image, ImageTk
import customtkinter as ctk
try:
    from picamera2 import Picamera2
except ImportError:
    from fake_picamera2 import Picamera2

class CameraManager:
    def __init__(self, resolution={'length': 1920, 'width': 1080}):
        self.resolution = resolution
        self.picam2 = Picamera2()
        try :
            self.camera_config = self.picam2.create_video_configuration(
                main={"size": (self.resolution['length'],
                            self.resolution['width'])})
            self.picam2.configure(self.camera_config)
            self.picam2.start()
            print("Camera initialized successfully")
        except Exception as e:
            print(f"Error intializing camera: {e}")
            self.picam2 = None
    
    def get_image(self):
        image = self.picam2.capture_array()
        image = Image.fromarray(image).convert("RGB")

        return image
    
    def capture_array(self):
        arr = self.picam2.capture_array()

        return arr
    
    def set_controller_vars(self, app, video_canvas):
        self.app = app
        self.video_canvas = video_canvas

    def get_video_feed(self):
        vid_params = {'f_length':300, 'f_width':200, 'buffer':10, 'x':0, 'y':0}
        frame = self.get_image()
        frame = frame.resize((vid_params['f_length'], vid_params['f_width']))
        frame = ImageTk.PhotoImage(frame)
        self.video_canvas.create_image(vid_params['x'], vid_params['y'], anchor=ctk.NW, image=frame)
        self.video_canvas.image = frame
        self.app.after(vid_params['buffer'], self.get_video_feed)

   
    def stop_camera(self):
        self.picam2.stop()
