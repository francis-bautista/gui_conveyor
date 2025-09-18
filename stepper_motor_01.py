""" 
from time import sleep
import RPi.GPIO as GPIO

DIR = 21   # Direction GPIO Pin
STEP = 20  # Step GPIO Pin
CW = 1     # Clockwise Rotation
CCW = 0    # Counterclockwise Rotation
SPR = 48   # Steps per Revolution (360 / 7.5)

GPIO.setmode(GPIO.BCM)
GPIO.setup(DIR, GPIO.OUT)
GPIO.setup(STEP, GPIO.OUT)
GPIO.output(DIR, CW)

step_count = SPR
delay = 0.0208

for x in range(step_count):
    GPIO.output(STEP, GPIO.HIGH)
    sleep(delay)
    GPIO.output(STEP, GPIO.LOW)
    sleep(delay)

sleep(.5)
GPIO.output(DIR, CCW)
for x in range(step_count):
    GPIO.output(STEP, GPIO.HIGH)
    sleep(delay)
    GPIO.output(STEP, GPIO.LOW)
    sleep(delay)

GPIO.cleanup()
 """
 
from time import sleep
import pigpio

DIR = 20     # Direction GPIO Pin
STEP = 21    # Step GPIO Pin
SWITCH = 16  # GPIO pin of switch

# Connect to pigpiod daemon
pi = pigpio.pi()

# Set up pins as an output
pi.set_mode(DIR, pigpio.OUTPUT)
pi.set_mode(STEP, pigpio.OUTPUT)

# Set up input switch
pi.set_mode(SWITCH, pigpio.INPUT)
pi.set_pull_up_down(SWITCH, pigpio.PUD_UP)

MODE = (14, 15, 18)   # Microstep Resolution GPIO Pins
RESOLUTION = {'Full': (0, 0, 0),
              'Half': (1, 0, 0),
              '1/4': (0, 1, 0),
              '1/8': (1, 1, 0),
              '1/16': (0, 0, 1),
              '1/32': (1, 0, 1)}
for i in range(3):
    pi.write(MODE[i], RESOLUTION['Full'][i])

# Set duty cycle and frequency
pi.set_PWM_dutycycle(STEP, 128)  # PWM 1/2 On 1/2 Off
pi.set_PWM_frequency(STEP, 500)  # 500 pulses per second

try:
    while True:
        pi.write(DIR, pi.read(SWITCH))  # Set direction
        sleep(.1)

except KeyboardInterrupt:
    print ("\nCtrl-C pressed.  Stopping PIGPIO and exiting...")
finally:
    pi.set_PWM_dutycycle(STEP, 0)  # PWM off
    pi.stop()