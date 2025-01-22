import hashlib
import random
import time

# Function to simulate the birthday paradox
def find_collision(target_bits=256):
    hashes = {}
    attempts = 0
    while True:
        # Random string (for simplicity, 32-bit random numbers as "inputs")
        input_data = str(random.randint(0, 2**32)).encode()
        
        # Compute hash
        hash_output = hashlib.sha256(input_data).hexdigest()
        
        # Check if this hash has already been seen
        if hash_output in hashes:
            print(f"Collision found after {attempts} attempts:")
            print(f"Hash: {hash_output}")
            print(f"Input 1: {hashes[hash_output]}")
            print(f"Input 2: {input_data.decode()}")
            break
        else:
            # Store the hash and its input
            hashes[hash_output] = input_data.decode()
        
        attempts += 1

# Run the simulation
start_time = time.time()
find_collision()
end_time = time.time()

print(f"Execution time: {end_time - start_time} seconds")

