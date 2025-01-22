import hashlib
import random
from fastecdsa import keys, curve

def generate_random_hash(length=64):
    """
    Generate a random hash of a given length.
    """
    random_data = ''.join(random.choices('0123456789abcdef', k=length))
    return hashlib.sha256(random_data.encode()).hexdigest()

def save_to_file(filename, data):
    """
    Save key pairs and hashes to a file.
    """
    with open(filename, 'a') as file:
        file.write(data + '\n')

def find_collision_and_save(filename="PRADOX-WORK.txt"):
    """
    Generate random hashes, derive keys, and check for collisions.
    """
    key_map = {}  # Store private keys and their hashes
    attempts = 0

    while True:
        # Step 1: Generate a random hash
        random_hash = generate_random_hash()
        
        # Step 2: Use the hash (256-bit) as a private key
        truncated_hash = int(random_hash[:64], 16)  # Use first 256 bits
        private_key = truncated_hash % curve.secp256k1.q  # Fit within curve order

        # Step 3: Compute the public key
        public_key = keys.get_public_key(private_key, curve.secp256k1)

        # Step 4: Save the generated keys and hash
        keypair_data = f"Hash: {random_hash}, Private Key: {private_key}, Public Key: ({public_key.x}, {public_key.y})"
        save_to_file(filename, keypair_data)

        # Step 5: Re-hash and check for collision
        rehashed_value = hashlib.sha256(random_hash.encode()).hexdigest()
        if rehashed_value in key_map:
            # Collision found
            save_to_file(filename, "\nCollision Found!")
            save_to_file(filename, f"Original Hash: {key_map[rehashed_value]['hash']}")
            save_to_file(filename, f"Colliding Hash: {random_hash}")
            save_to_file(filename, f"Private Key: {private_key}")
            save_to_file(filename, f"Public Key: ({public_key.x}, {public_key.y})")
            print("Collision detected! Details saved.")
            break
        else:
            # Store the key and hash for later checks
            key_map[rehashed_value] = {'hash': random_hash, 'private_key': private_key, 'public_key': public_key}

        attempts += 1
        if attempts % 1000 == 0:
            print(f"Attempts: {attempts}, Unique Keys: {len(key_map)}")

# Run the script
find_collision_and_save()

