import RPi.GPIO as GPIO
import time

# Pin definitions (BCM numbering)
LASER_PIN = 18    # GPIO2 (Physical Pin 3)
SENSOR_PIN = 23   # GPIO3 (Physical Pin 5)


# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Configure pins
GPIO.setup(LASER_PIN, GPIO.OUT)
GPIO.setup(SENSOR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Enable pull-up

# Turn laser on initially
GPIO.output(LASER_PIN, GPIO.HIGH)

try:
    while True:
        sensor_state = GPIO.input(SENSOR_PIN)
        
        if sensor_state == GPIO.LOW:  # Beam interrupted
            print("Beam interrupted! Value: 0")
        else:                        # Beam detected
            print("Beam detected. Value: 1")
        
        time.sleep(0.1)  # Short delay to reduce CPU usage

except KeyboardInterrupt:
    GPIO.cleanup()
    print("\nProgram stopped!")