import time
import random

def rts_command_center():
    print("=== COMMAND CENTER INITIALIZED ===")
    print("Welcome, Commander. System is online.")
    
    # Starting inventory
    resources = {"Aluminum": 0, "Iron": 0, "Copper": 0}
    army_size = 0
    
    while True:
        print("\n--- Current Status ---")
        print(f"Resources: {resources}")
        print(f"Army Size: {army_size} Units")
        print("\nOptions:")
        print("1. Send drones to gather resources")
        print("2. Build an army unit (Costs: 10 Aluminum, 20 Iron, 5 Copper)")
        print("3. Shut down terminal")
        
        # This waits for the user to type something in the terminal
        choice = input("Enter command (1-3): ")
        
        if choice == '1':
            print("Drones deployed. Mining the area...")
            time.sleep(1.5) # Pauses the code for a dramatic effect!
            
            # Generate random amounts of resources
            gathered_al = random.randint(2, 15)
            gathered_fe = random.randint(5, 20)
            gathered_cu = random.randint(1, 10)
            
            resources["Aluminum"] += gathered_al
            resources["Iron"] += gathered_fe
            resources["Copper"] += gathered_cu
            
            print(f">>> Success! Collected {gathered_al} Aluminum, {gathered_fe} Iron, and {gathered_cu} Copper.")
            
        elif choice == '2':
            # Check if the player has enough resources to build
            if resources["Aluminum"] >= 10 and resources["Iron"] >= 20 and resources["Copper"] >= 5:
                print("Constructing unit...")
                time.sleep(2)
                
                # Deduct resources
                resources["Aluminum"] -= 10
                resources["Iron"] -= 20
                resources["Copper"] -= 5
                
                # Add to army
                army_size += 1
                print(">>> Unit successfully built and added to your army!")
            else:
                print(">>> SYSTEM WARNING: Insufficient resources! You need more materials.")
                
        elif choice == '3':
            print("Shutting down terminal... Good luck out there, Commander.")
            break # This exits the infinite while loop
            
        else:
            print(">>> Invalid command. Please type 1, 2, or 3.")

# This line officially starts the app
if __name__ == "__main__":
    rts_command_center()