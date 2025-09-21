try:
    import RPi.GPIO as GPIO
except ImportError:
    from fake_gpio import GPIO
import time

class MotorController:
    def __init__(self):
        self.relays = {'r1': 6, 'r2': 13, 'r3': 19, 'r4': 26}
        self.DIR_PIN = 21
        self.STEP_PIN = 20
        self.steps_per_revolution = 200
        self.current_position = 0
        self.step_delay = 0.001
        self.stepper_motor = {'pos1': 50, 'pos2': 100, 'pos3': 150}
        self.setup_gpio()
    
    def setup_gpio(self):
        self.relays = {'r1': 6, 'r2': 13, 'r3': 19, 'r4': 26}
        GPIO.cleanup()
        GPIO.setmode(GPIO.BCM)
        for pin_number in self.relays.values():
            GPIO.setup(pin_number,GPIO.OUT)
            GPIO.setup(pin_number,GPIO.LOW)
        GPIO.setwarnings(False)

    def clean_gpio(self):
        GPIO.cleanup()
    
    def set_motors(self, motor_array):
        for i, pin in enumerate(self.relays.values()):
            GPIO.output(pin, motor_array[i])
        
        motor_messages = [
            "Motor 1 is moving in Clockwise",
            "Motor 1 is moving in Counter Clockwise", 
            "Motor 2 is moving in Clockwise",
            "Motor 2 is moving in Counter Clockwise"]
        
        for i, message in enumerate(motor_messages):
            if motor_array[i]:
                print(message)

    def stop_motors(self):
        for pin_number in self.relays.values():
            GPIO.output(pin_number,GPIO.LOW)
        print("Motors stopped!")
    
    def set_stepper_position(self, target):
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
