#!/usr/bin/env python3
"""
Script to run relays through all possible states and then stop them.
This will cycle through all 16 possible combinations of 4 relays (2^4 = 16).
"""

import time
from sorting import SorterController

def generate_all_states():
    """Generate all possible 4-bit combinations (0000 to 1111)."""
    states = []
    for i in range(16):  # 2^4 = 16 combinations
        # Convert number to 4-bit binary representation
        binary = format(i, '04b')
        state = [int(bit) for bit in binary]
        states.append(state)
    return states

def run_all_relay_states(delay_seconds=2):
    """
    Run relays through all possible states with a delay between each state.
    
    Args:
        delay_seconds (float): Time to wait between state changes
    """
    controller = SorterController()
    
    try:
        print("=" * 60)
        print("RELAY STATE RUNNER - Testing All Combinations")
        print("=" * 60)
        print(f"Delay between states: {delay_seconds} seconds")
        print("Relay mapping: R1=Pin4, R2=Pin17, R3=Pin27, R4=Pin22")
        print("State format: [R1, R2, R3, R4] (0=OFF, 1=ON)")
        print("=" * 60)
        
        # Generate all possible states
        all_states = generate_all_states()
        
        print(f"Running through {len(all_states)} relay states...\n")
        
        for i, state in enumerate(all_states):
            print(f"State {i+1:2d}/16: {state} - ", end="")
            
            # Create readable description
            active_relays = []
            for j, relay_state in enumerate(state):
                if relay_state:
                    active_relays.append(f"R{j+1}")
            
            if active_relays:
                description = f"Active: {', '.join(active_relays)}"
            else:
                description = "All OFF"
            
            print(description)
            
            # Set the motor state
            controller.set_motors(state)
            
            # Wait before next state
            time.sleep(delay_seconds)
        
        print("\n" + "=" * 60)
        print("All states completed! Stopping all motors...")
        controller.stop_motors()
        
        print("Cleaning up GPIO...")
        controller.clean_gpio()
        
        print("✓ Test sequence completed successfully!")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user! Stopping motors and cleaning up...")
        controller.stop_motors()
        controller.clean_gpio()
        print("✓ Emergency stop completed.")
        
    except Exception as e:
        print(f"\nError occurred: {e}")
        print("Stopping motors and cleaning up...")
        controller.stop_motors()
        controller.clean_gpio()
        print("✓ Error recovery completed.")

def run_specific_patterns():
    """Run some specific interesting patterns."""
    controller = SorterController()
    
    try:
        print("\n" + "=" * 60)
        print("RUNNING SPECIFIC PATTERNS")
        print("=" * 60)
        
        patterns = [
            ([1, 0, 1, 0], "Alternating Pattern 1"),
            ([0, 1, 0, 1], "Alternating Pattern 2"), 
            ([1, 1, 0, 0], "First Two ON"),
            ([0, 0, 1, 1], "Last Two ON"),
            ([1, 0, 0, 0], "Only R1 ON"),
            ([0, 1, 0, 0], "Only R2 ON"),
            ([0, 0, 1, 0], "Only R3 ON"),
            ([0, 0, 0, 1], "Only R4 ON"),
            ([1, 1, 1, 0], "First Three ON"),
            ([0, 1, 1, 1], "Last Three ON"),
            ([1, 1, 1, 1], "All ON"),
        ]
        
        for pattern, description in patterns:
            print(f"Pattern: {pattern} - {description}")
            controller.set_motors(pattern)
            time.sleep(2)
        
        print("\nStopping all motors...")
        controller.stop_motors()
        controller.clean_gpio()
        print("✓ Pattern test completed!")
        
    except KeyboardInterrupt:
        print("\nInterrupted! Cleaning up...")
        controller.stop_motors()
        controller.clean_gpio()

def main():
    """Main function with user options."""
    print("Relay State Runner")
    print("Choose an option:")
    print("1. Run all 16 possible states (comprehensive test)")
    print("2. Run specific interesting patterns")
    print("3. Quick test (faster timing)")
    print("4. Exit")
    
    try:
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            delay = float(input("Enter delay between states in seconds (default 2): ") or "2")
            run_all_relay_states(delay)
            
        elif choice == "2":
            run_specific_patterns()
            
        elif choice == "3":
            print("Running quick test with 0.5 second delays...")
            run_all_relay_states(0.5)
            
        elif choice == "4":
            print("Exiting...")
            return
            
        else:
            print("Invalid choice. Please run again.")
            
    except ValueError:
        print("Invalid input. Using default settings...")
        run_all_relay_states()
    except KeyboardInterrupt:
        print("\nProgram interrupted by user.")

if __name__ == "__main__":
    main()