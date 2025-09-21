try:
    import RPi.GPIO as GPIO
    print("Imported RPi.GPIO successfully sorting controller")
except ImportError:
    from fake_gpio import GPIO
import time

class SorterController:
    def __init__(self):
        self.relays =  {'r1': 4, 'r2': 17, 'r3': 27, 'r4': 22}
        self.setup_gpio()
    
    def setup_gpio(self):
        self.relays =  {'r1': 4, 'r2': 17, 'r3': 27, 'r4': 22}
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
            "Motor 3 is moving in Clockwise",
            "Motor 3 is moving in Counter Clockwise", 
            "Motor 4 is moving in Clockwise",
            "Motor 4 is moving in Counter Clockwise"]
        
        for i, message in enumerate(motor_messages):
            if motor_array[i]:
                print(message)

    def stop_motors(self):
        for pin_number in self.relays.values():
            GPIO.output(pin_number,GPIO.LOW)
        print("Motors stopped!")
    
