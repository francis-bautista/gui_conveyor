# Save this as Fake_picamera2.py in your project directory

import time
import threading
from typing import Dict, Any, Optional, Tuple, List
import numpy as np

class FakePicamera2:
    """Fake implementation of Picamera2 for testing on non-RPi systems"""
    
    def __init__(self):
        self.camera_config = None
        self.is_started = False
        self.is_recording = False
        self.recording_thread = None
        self.preview_running = False
        print("[Fake] Picamera2() initialized")
    
    def create_preview_configuration(self, main=None, lores=None, raw=None, transform=None, colour_space=None, buffer_count=None, controls=None):
        """Fake preview configuration creation"""
        config = {
            'main': main or {'size': (640, 480), 'format': 'RGB888'},
            'lores': lores,
            'raw': raw,
            'transform': transform,
            'colour_space': colour_space,
            'buffer_count': buffer_count or 4,
            'controls': controls or {}
        }
        print(f"[Fake] create_preview_configuration() -> {config}")
        return config
    
    def create_still_configuration(self, main=None, lores=None, raw=None, transform=None, colour_space=None, buffer_count=None, controls=None):
        """Fake still configuration creation"""
        config = {
            'main': main or {'size': (1920, 1080), 'format': 'RGB888'},
            'lores': lores,
            'raw': raw,
            'transform': transform,
            'colour_space': colour_space,
            'buffer_count': buffer_count or 2,
            'controls': controls or {}
        }
        print(f"[Fake] create_still_configuration() -> {config}")
        return config
    
    def create_video_configuration(self, main=None, lores=None, raw=None, transform=None, colour_space=None, buffer_count=None, controls=None):
        """Fake video configuration creation"""
        config = {
            'main': main or {'size': (1920, 1080), 'format': 'RGB888'},
            'lores': lores,
            'raw': raw,
            'transform': transform,
            'colour_space': colour_space,
            'buffer_count': buffer_count or 6,
            'controls': controls or {}
        }
        print(f"[Fake] create_video_configuration() -> {config}")
        return config
    
    def configure(self, config):
        """Fake camera configuration"""
        self.camera_config = config
        print(f"[Fake] configure() with config: {config}")
    
    def start(self, config=None, show_preview=False):
        """Fake camera start"""
        if config:
            self.configure(config)
        self.is_started = True
        print(f"[Fake] start() - Camera started, show_preview={show_preview}")
    
    def stop(self):
        """Fake camera stop"""
        self.is_started = False
        self.is_recording = False
        if self.recording_thread:
            self.recording_thread = None
        print("[Fake] stop() - Camera stopped")
    
    def close(self):
        """Fake camera close"""
        self.stop()
        print("[Fake] close() - Camera closed")
    
    def capture_array(self, name="main"):
        """Fake array capture - returns fake image data"""
        if not self.is_started:
            raise RuntimeError("Camera not started")
        
        # Create fake image data based on configuration
        if self.camera_config and name in self.camera_config:
            size = self.camera_config[name].get('size', (640, 480))
        else:
            size = (640, 480)
        
        # Generate fake RGB image data
        fake_image = np.random.randint(0, 255, (size[1], size[0], 3), dtype=np.uint8)
        print(f"[Fake] capture_array('{name}') -> shape {fake_image.shape}")
        return fake_image
    
    def capture_file(self, name, format=None, wait=True):
        """Fake file capture"""
        if not self.is_started:
            raise RuntimeError("Camera not started")
        
        print(f"[Fake] capture_file('{name}', format={format}, wait={wait})")
        
        if wait:
            time.sleep(0.1)  # Simulate capture time
        
        # Create a fake file (in real implementation, this would save an actual image)
        print(f"[Fake] Image saved to {name}")
    
    def start_preview(self, preview=None):
        """Fake preview start"""
        self.preview_running = True
        print(f"[Fake] start_preview() - Preview started")
    
    def stop_preview(self):
        """Fake preview stop"""
        self.preview_running = False
        print("[Fake] stop_preview() - Preview stopped")
    
    def start_recording(self, output, format=None, pts=None, audio=False):
        """Fake recording start"""
        if not self.is_started:
            raise RuntimeError("Camera not started")
        
        self.is_recording = True
        print(f"[Fake] start_recording('{output}', format={format}, audio={audio})")
        
        # Simulate recording in a separate thread
        def fake_recording():
            while self.is_recording:
                time.sleep(0.1)
        
        self.recording_thread = threading.Thread(target=fake_recording)
        self.recording_thread.start()
    
    def stop_recording(self):
        """Fake recording stop"""
        if self.is_recording:
            self.is_recording = False
            if self.recording_thread:
                self.recording_thread.join()
            print("[Fake] stop_recording() - Recording stopped")
    
    def set_controls(self, controls):
        """Fake control setting"""
        print(f"[Fake] set_controls({controls})")
    
    def capture_metadata(self):
        """Fake metadata capture"""
        metadata = {
            'ExposureTime': 10000,
            'AnalogueGain': 1.0,
            'DigitalGain': 1.0,
            'ColourGains': (1.5, 1.3),
            'ColourTemperature': 5000,
            'Lux': 100.0,
            'SensorTimestamp': int(time.time() * 1000000)
        }
        print(f"[Fake] capture_metadata() -> {metadata}")
        return metadata
    
    @property
    def camera_properties(self):
        """Fake camera properties"""
        properties = {
            'Model': 'Fake Camera',
            'UnitCellSize': (1.12, 1.12),  # micrometers
            'PixelArraySize': (3280, 2464),
            'PixelArrayActiveAreas': [(0, 0, 3280, 2464)],
            'ScalerCropMaximum': (0, 0, 3280, 2464),
            'SensorOutputSize': (3280, 2464),
            'Location': 2,  # CAMERA_LOCATION_FRONT
        }
        print(f"[Fake] camera_properties -> {properties}")
        return properties
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


# Additional Fake classes that might be used with Picamera2
class FakeEncoder:
    """Fake encoder for video recording"""
    def __init__(self, format='h264'):
        self.format = format
        print(f"[Fake] Encoder({format}) created")


class FakeOutput:
    """Fake output for recording"""
    def __init__(self, filename):
        self.filename = filename
        print(f"[Fake] Output({filename}) created")


# Create the main Fake class that can be imported
Picamera2 = FakePicamera2