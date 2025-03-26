import customtkinter as ctk
import threading
import time

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Configure window
        self.title("Start/Stop Example")
        self.geometry("400x300")
        
        # Create a flag to control the running thread
        self.running = False
        self.thread = None
        
        # Create a frame
        self.frame = ctk.CTkFrame(self)
        self.frame.pack(pady=20, padx=20, fill="both", expand=True)
        
        # Create label
        self.status_label = ctk.CTkLabel(self.frame, text="Ready", font=("Arial", 14))
        self.status_label.pack(pady=10)
        
        # Create a progressbar
        self.progress = ctk.CTkProgressBar(self.frame, width=300)
        self.progress.pack(pady=10)
        self.progress.set(0)
        
        # Create Start button
        self.start_button = ctk.CTkButton(
            self.frame, 
            text="Start", 
            command=self.start_process,
            fg_color="green",
            hover_color="dark green"
        )
        self.start_button.pack(pady=10)
        
        # Create Stop button
        self.stop_button = ctk.CTkButton(
            self.frame, 
            text="Stop", 
            command=self.stop_process,
            fg_color="red",
            hover_color="dark red",
            state="disabled"
        )
        self.stop_button.pack(pady=10)
    
    def start_process(self):
        """Start the long-running process in a separate thread"""
        if not self.running:
            self.running = True
            self.start_button.configure(state="disabled")
            self.stop_button.configure(state="normal")
            self.status_label.configure(text="Running...")
            
            # Start the process in a new thread
            self.thread = threading.Thread(target=self.long_running_process)
            self.thread.daemon = True  # Thread will close when main program exits
            self.thread.start()
    
    def stop_process(self):
        """Stop the long-running process"""
        if self.running:
            self.running = False
            self.stop_button.configure(state="disabled")
            self.status_label.configure(text="Stopping...")
    
    def long_running_process(self):
        """The long-running process that simulates work for 30 seconds"""
        start_time = time.time()
        total_duration = 30  # seconds
        
        try:
            # Run for 30 seconds or until stopped
            while self.running and time.time() - start_time < total_duration:
                # Calculate progress (0 to 1)
                elapsed = time.time() - start_time
                progress = min(elapsed / total_duration, 1.0)
                
                # Update UI from the main thread
                self.after(0, lambda p=progress: self.update_progress(p))
                
                # Sleep a short time to check for stop condition frequently
                time.sleep(0.1)
            
            # Process completed or was stopped
            self.after(0, self.process_completed)
            
        except Exception as e:
            print(f"Error in long_running_process: {e}")
            self.after(0, self.process_completed)
    
    def update_progress(self, progress_value):
        """Update the progress bar"""
        self.progress.set(progress_value)
    
    def process_completed(self):
        """Reset UI after process completes or is stopped"""
        if self.running:
            self.status_label.configure(text="Completed!")
        else:
            self.status_label.configure(text="Stopped")
        
        self.running = False
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.progress.set(0)

if __name__ == "__main__":
    app = App()
    app.mainloop()