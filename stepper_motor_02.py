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

# Motor control parameters
delay = 0.0208  # Delay between steps

def move_steps(steps, direction, delay_time=0.0208):
    """
    Move the motor a specific number of steps in a given direction
    
    Args:
        steps: Number of steps to move
        direction: CW (1) or CCW (0)
        delay_time: Delay between steps in seconds
    """
    GPIO.output(DIR, direction)
    for _ in range(steps):
        GPIO.output(STEP, GPIO.HIGH)
        sleep(delay_time)
        GPIO.output(STEP, GPIO.LOW)
        sleep(delay_time)

def move_to_angle(target_angle, current_angle):
    """
    Move motor from current angle to target angle
    Takes the shortest path (CW or CCW)
    
    Args:
        target_angle: Target position in degrees
        current_angle: Current position in degrees
    
    Returns:
        New current angle after movement
    """
    # Normalize angles to 0-360 range
    target_angle = target_angle % 360
    current_angle = current_angle % 360
    
    # Calculate the difference
    diff = target_angle - current_angle
    
    # Determine shortest path
    if diff > 180:
        diff -= 360
    elif diff < -180:
        diff += 360
    
    # Convert angle difference to steps
    # SPR=48 means 48 steps for 360 degrees, so 7.5 degrees per step
    steps = abs(int(diff / 7.5))
    
    # Determine direction
    if diff > 0:
        direction = CW
    else:
        direction = CCW
    
    # Move the motor
    if steps > 0:
        print(f"Moving from {current_angle:.1f}° to {target_angle:.1f}° ({steps} steps {'CW' if direction == CW else 'CCW'})")
        move_steps(steps, direction, delay)
    
    return target_angle

try:
    # Define three positions in degrees
    # You can adjust these angles as needed
    positions = [0, 120, 240]  # Three positions evenly spaced
    
    # Alternative: Define custom positions
    # positions = [0, 90, 180]  # Front, right, back
    # positions = [0, 45, 270]  # Custom positions
    
    # Starting position (assume we're at 0 degrees)
    current_pos = 0
    
    print("Starting three-position loop control")
    print(f"Positions: {positions} degrees")
    print("Press Ctrl+C to stop\n")
    
    # Main loop
    while True:
        for position in positions:
            # Move to the next position
            current_pos = move_to_angle(position, current_pos)
            
            # Wait at this position
            sleep(2)  # Adjust pause duration as needed
        
        # Optional: Add a longer pause after completing all three positions
        print("Completed cycle, starting next...\n")
        sleep(1)

except KeyboardInterrupt:
    print("\nStopping motor control...")

finally:
    # Clean up GPIO on exit
    GPIO.cleanup()
    print("GPIO cleaned up")