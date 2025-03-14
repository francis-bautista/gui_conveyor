import RPi.GPIO as GPIO
import time

# Define pin connections (using BOARD numbering)
dir_pin = 21    # Physical pin 21
step_pin = 20   # Physical pin 20
steps_per_revolution = 200

# Define absolute positions (steps from home)
position1 = 50
position2 = 100
position3 = 150
position4 = 200

current_position = 0  # Track current position
step_delay = 0.001    # 1ms delay between steps (adjust for speed)

def setupPy():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(dir_pin, GPIO.OUT)
    GPIO.setup(step_pin, GPIO.OUT)
    GPIO.output(dir_pin, GPIO.LOW)
    GPIO.output(step_pin, GPIO.LOW)

def move_to_position(target):
    global current_position
    steps_needed = target - current_position
    
    if steps_needed == 0:
        return  # Already at position
    
    # Set direction
    direction = GPIO.HIGH if steps_needed > 0 else GPIO.LOW
    GPIO.output(dir_pin, direction)
    
    # Move required steps
    for _ in range(abs(steps_needed)):
        GPIO.output(step_pin, GPIO.HIGH)
        time.sleep(step_delay)
        GPIO.output(step_pin, GPIO.LOW)
        time.sleep(step_delay)
    
    # Update current position
    current_position = target

def main():
    try:
        setupPy()
        while True:
            move_to_position(position1)
            time.sleep(1)
            move_to_position(position2)
            time.sleep(1)
            move_to_position(position3)
            time.sleep(1)
            move_to_position(position4)
            time.sleep(1)
            
    except KeyboardInterrupt:
        GPIO.cleanup()

main()