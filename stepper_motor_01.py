from time import sleep
import RPi.GPIO as GPIO

DIR = 21   # Direction GPIO Pin
STEP = 20  # Step GPIO Pin
CW = 0     # Try flipping logic here
CCW = 1
SPR = 48   # Steps per Revolution (360 / 7.5)

GPIO.setmode(GPIO.BCM)
GPIO.setup(DIR, GPIO.OUT)
GPIO.setup(STEP, GPIO.OUT)

step_count = SPR
delay = 0.0208

# Clockwise
GPIO.output(DIR, CW)
sleep(0.01)  # allow DIR pin to settle
for x in range(step_count):
    GPIO.output(STEP, GPIO.HIGH)
    sleep(delay)
    GPIO.output(STEP, GPIO.LOW)
    sleep(delay)

sleep(0.5)

# Counterclockwise
GPIO.output(DIR, CCW)
sleep(0.01)
for x in range(step_count):
    GPIO.output(STEP, GPIO.HIGH)
    sleep(delay)
    GPIO.output(STEP, GPIO.LOW)
    sleep(delay)

GPIO.cleanup()
