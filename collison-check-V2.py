import hashlib
import random
import time

def truncated_hash(input_data, bits=8):
    """
    Computes a hash and truncates it to the desired number of bits.
    """
    full_hash = hashlib.sha256(input_data).hexdigest()
    truncated = full_hash[:bits // 4]  # Each hex digit represents 4 bits
    return truncated

def find_collision(target_bits=8):
    """
    Finds a hash collision using a reduced hash size for demonstration.
    """
    hashes = {}
    attempts = 0

    while True:
        # Generate random input
        input_data = str(random.randint(0, 2**32)).encode()
        
        # Compute the truncated hash
        hash_output = truncated_hash(input_data, bits=target_bits)
        
        # Print the attempt details
        print(f"Attempt {attempts}: Input: {input_data.decode()} -> Hash: {hash_output}")
        
        # Check for collision
        if hash_output in hashes:
            print(f"\nCollision found after {attempts} attempts!")
            print(f"Hash: {hash_output}")
            print(f"Input 1: {hashes[hash_output]}")
            print(f"Input 2: {input_data.decode()}")
            break
        else:
            # Store the hash and input
            hashes[hash_output] = input_data.decode()
        
        attempts += 1

# Run the collision finding script
start_time = time.time()
find_collision(target_bits=8)  # Use 8-bit hash for quick demonstration
end_time = time.time()

print(f"\nExecution time: {end_time - start_time} seconds")

