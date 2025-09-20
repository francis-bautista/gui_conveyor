#!/usr/bin/env python3
import time
from sorting import SorterController

controller = SorterController()

states = [
    [0, 1, 0, 1],
    [0, 0, 0, 0],
    [1, 0, 1, 0],
    [0, 0, 0, 0],
    [0, 1, 1, 0],
    [1, 0, 0, 1]
]

try:
    for i, state in enumerate(states):
        print(f"State {i+1}: {state}")
        controller.set_motors(state)
        time.sleep(2)
    
    controller.stop_motors()
    controller.clean_gpio()
    
except KeyboardInterrupt:
    controller.stop_motors()
    controller.clean_gpio()