#!/usr/bin/env python3
import time
from sorting import SorterController

controller = SorterController()

states = [
    # individual motor activation
    # only long conveyor towards two options (towards motor)
    [1, 0, 0, 0],
    [0, 0, 0, 0],
    # only long conveyor towards A. (against motor)
    [0, 1, 0, 0],
    [0, 0, 0, 0],
    # only short conveyor towards motor
    [0, 0, 1, 0],
    [0, 0, 0, 0],
    # only short conveyor against motor 
    [0, 0, 0, 1],
    [0, 0, 0, 0],
    
    # multiple motor activation
    
    [0, 1, 0, 1],
    [0, 0, 0, 0],

    [1, 0, 1, 0],
    [0, 0, 0, 0],

    [0, 1, 1, 0],
    [0, 0, 0, 0],

    [1, 0, 0, 1]
]

try:
    for i, state in enumerate(states):
        print(f"State {i+1}: {state}")
        controller.set_motors(state)
        time.sleep(30)
    
    controller.stop_motors()
    controller.clean_gpio()
    
except KeyboardInterrupt:
    controller.stop_motors()
    controller.clean_gpio()