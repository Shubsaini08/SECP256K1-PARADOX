import hashlib
import random

def sha256(input_data):
    """
    Computes the SHA-256 hash of the given input.
    """
    return hashlib.sha256(input_data).hexdigest()

def find_hash_in_range(lower_bound, upper_bound):
    """
    Finds a SHA-256 hash within a specific range.
    """
    attempts = 0
    while True:
        # Generate random input
        input_data = str(random.randint(0, 2**32)).encode()
        
        # Compute hash
        hash_output = sha256(input_data)
        hash_value = int(hash_output, 16)
        
        # Check if the hash is within the range
        if lower_bound <= hash_value <= upper_bound:
            print(f"Hash found after {attempts} attempts!")
            print(f"Input: {input_data.decode()}")
            print(f"Hash: {hash_output}")
            return attempts
        
        attempts += 1

# Define range (example: upper 16-bit space)
lower_bound = int("f000000000000000000000000000000000000000000000000000000000000000", 16)
upper_bound = int("ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff", 16)

# Find hash in range
find_hash_in_range(lower_bound, upper_bound)

