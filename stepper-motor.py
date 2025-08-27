#        self.dir_pin = 21    # Physical pin 21
#        self.step_pin = 20   # Physical pin 20
import RPi.GPIO as GPIO
import time

class StepperController:
    def __init__(self):
        # Define pin connections
        self.dir_pin = 21    # Direction pin
        self.step_pin = 20   # Step pin
        self.steps_per_revolution = 200
        
        # Define absolute positions (steps from home)
        self.position1 = 50
        self.position2 = 100
        self.position3 = 150
        # self.position4 = 200
        
        self.current_position = 0  # Track current position
        self.step_delay = 0.001    # 1ms delay between steps (adjust for speed)
        
        # Setup GPIO
        GPIO.setmode(GPIO.BCM)  # Use BCM pin numbering
        GPIO.setup(self.dir_pin, GPIO.OUT)
        GPIO.setup(self.step_pin, GPIO.OUT)
        GPIO.output(self.dir_pin, GPIO.LOW)
        GPIO.output(self.step_pin, GPIO.LOW)
        
        print("Stepper motor controller initialized")
    
    def move_to_position(self, target):
        steps_needed = target - self.current_position
        
        if steps_needed == 0:
            return  # Already at position
        
        # Set direction
        direction = GPIO.HIGH if steps_needed > 0 else GPIO.LOW
        GPIO.output(self.dir_pin, direction)
        
        # Move required steps
        for i in range(abs(steps_needed)):
            GPIO.output(self.step_pin, GPIO.HIGH)
            time.sleep(self.step_delay)
            GPIO.output(self.step_pin, GPIO.LOW)
            time.sleep(self.step_delay)
        
        # Update current position
        self.current_position = target
        print(f"Moved to position: {target}")
    
    def run_sequence(self):
        """Run the main movement sequence"""
        try:
            while True:
                self.move_to_position(self.position1)
                time.sleep(1)
                
                self.move_to_position(self.position2)
                time.sleep(1)
                
                self.move_to_position(self.position3)
                time.sleep(1)
                
                # self.move_to_position(self.position4)
                # time.sleep(1)
                
        except KeyboardInterrupt:
            print("\nStopping motor controller...")
            self.cleanup()
    
    def cleanup(self):
        """Clean up GPIO pins"""
        GPIO.cleanup()
        print("GPIO cleanup complete")

# Main execution
if __name__ == "__main__":
    controller = StepperController()
    controller.run_sequence()
