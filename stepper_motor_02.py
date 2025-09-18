from time import sleep
import RPi.GPIO as GPIO

# GPIO Pin Configuration
DIR = 21   # Direction GPIO Pin
STEP = 20  # Step GPIO Pin
CW = 1     # Clockwise Rotation
CCW = 0    # Counterclockwise Rotation
SPR = 48   # Steps per Revolution (360 / 7.5)

# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(DIR, GPIO.OUT)
GPIO.setup(STEP, GPIO.OUT)

# Step delay (adjust for speed)
delay = 0.0208  

# Convert degrees to steps
def move_to_angle(target_angle, current_angle):
    step_angle = 360 / SPR   # 7.5° per step
    steps_needed = int(abs(target_angle - current_angle) / step_angle)

    if target_angle > current_angle:
        GPIO.output(DIR, CW)
    else:
        GPIO.output(DIR, CCW)

    for _ in range(steps_needed):
        GPIO.output(STEP, GPIO.HIGH)
        sleep(delay)
        GPIO.output(STEP, GPIO.LOW)
        sleep(delay)

    return target_angle  # new current position

try:
    current_position = 0  # Start at 0 degrees
    positions = [0, 90, -90]  # target positions

    while True:
        for target in positions:
            print(f"Moving to {target}° from {current_position}°")
            current_position = move_to_angle(target, current_position)
            sleep(1)  # pause between moves

except KeyboardInterrupt:
    print("Exiting...")

finally:
    GPIO.cleanup()