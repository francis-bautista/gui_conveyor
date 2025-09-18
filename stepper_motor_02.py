from time import sleep
import RPi.GPIO as GPIO

# GPIO Pin Configuration
DIR = 21   # Direction GPIO Pin (BCM)
STEP = 20  # Step GPIO Pin (BCM)
SPR = 48   # Steps per revolution (full step count)
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(DIR, GPIO.OUT)
GPIO.setup(STEP, GPIO.OUT)

# Logical values for direction (use GPIO.HIGH/LOW to be explicit)
CW = GPIO.HIGH
CCW = GPIO.LOW

# Tweak these if needed
delay = 0.0208       # pulse half-period (adjust speed)
invert_dir = False   # set True if your driver uses inverted DIR logic
DIR_SETTLE = 0.001   # small pause after changing DIR so driver latches it

step_angle = 360.0 / SPR  # degrees per step

def set_direction(cw: bool):
    """Set DIR pin (handles optional inversion) and wait a tiny bit."""
    val = CW if cw else CCW
    if invert_dir:
        val = CCW if val == CW else CW
    GPIO.output(DIR, val)
    sleep(DIR_SETTLE)  # allow driver to see the direction before stepping

def step_pulse(steps: int):
    """Send STEP pulses (blocking)."""
    for _ in range(steps):
        GPIO.output(STEP, GPIO.HIGH)
        sleep(delay)
        GPIO.output(STEP, GPIO.LOW)
        sleep(delay)

def move_to_angle(target_angle: float, current_angle: float) -> float:
    """Move from current_angle to target_angle. Returns the new (exact) position."""
    diff = target_angle - current_angle
    steps_needed = int(round(abs(diff) / step_angle))
    if steps_needed == 0:
        print(f"Already at {target_angle}°")
        return target_angle

    go_cw = (diff > 0)
    set_direction(go_cw)
    print(f"Moving {'CW' if go_cw else 'CCW'} {steps_needed} steps ({steps_needed * step_angle:.2f}°)")
    step_pulse(steps_needed)

    # To avoid rounding drift, return the exact requested target angle
    return target_angle

try:
    current_position = 0.0
    positions = [0.0, 90.0, -90.0]

    while True:
        for t in positions:
            print(f"From {current_position}° → {t}°")
            current_position = move_to_angle(t, current_position)
            sleep(1.0)

except KeyboardInterrupt:
    print("Stopped by user")

finally:
    GPIO.cleanup()