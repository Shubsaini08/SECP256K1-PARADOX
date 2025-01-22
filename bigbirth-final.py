#!/usr/bin/env python3

import os
import hashlib
import time
import logging
from multiprocessing import Pool, cpu_count
from fastecdsa.curve import secp256k1
from fastecdsa.point import Point
from collections import defaultdict

# Constants
BS_FILE = 'baby_steps_table.txt'
FOUND_KEYS_FILE = 'found_keys.txt'
TARGET_KEYS = 'pubkeys.txt'
DEFAULT_M = 5000

# Logging Configuration
logging.basicConfig(
    filename="collision_log.txt",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Hash Function for Birthday Paradox
def truncated_hash(input_data, bits=16):
    full_hash = hashlib.sha256(input_data.encode()).hexdigest()
    return full_hash[:bits // 4]  # Truncate to required bits

# Create Baby-Step Table
def create_baby_step_table(m):
    logging.info(f"Creating Baby-Step table with m={m}")
    baby_steps = {}
    point = secp256k1.G
    for i in range(m):
        baby_steps[point.x] = i
        point += secp256k1.G
    return baby_steps

# Load Public Keys with Validation
def load_pubkeys(filename):
    keys = []
    try:
        with open(filename, 'r') as f:
            for line in f:
                key = line.strip()
                if key and (len(key) == 66 or len(key) == 130) and key[:2] in {'02', '03', '04'}:
                    keys.append(key)
                else:
                    logging.warning(f"Invalid or malformed key skipped: {key}")
    except Exception as e:
        logging.error(f"Error reading file {filename}: {e}")
        raise
    return keys

# Convert Public Key to Point with Error Handling
def pubkey_to_point(pubkey):
    try:
        x = int(pubkey[2:66], 16)
        if len(pubkey) < 70:  # Compressed format
            y = pow(x**3 + 7, (secp256k1.q + 1) // 4, secp256k1.q) % secp256k1.q
            if (pubkey[:2] == '03') != (y % 2 == 0):
                y = secp256k1.q - y
        else:
            y = int(pubkey[66:], 16)
        return Point(x, y, curve=secp256k1)
    except ValueError as e:
        logging.error(f"ValueError in pubkey_to_point for key {pubkey}: {e}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error in pubkey_to_point: {e}")
        raise

# Parallel Giant-Step Lookup
def giant_step(args):
    Qlist, k1G, mG, baby_steps = args
    found_keys = []
    key_hash_map = defaultdict(list)  # Map to store hashes and their corresponding keys
    publickey_map = defaultdict(list)  # Map to store similar public keys
    target_hash = truncated_hash("TARGET")  # Replace "TARGET" with the actual target data

    for Q in Qlist:
        S = Q - k1G
        for j in range(DEFAULT_M):
            # Check Baby Steps
            if S.x in baby_steps:
                private_key = baby_steps[S.x] + j * DEFAULT_M
                found_keys.append(private_key)

            # Hashing for Birthday Paradox
            hash_value = truncated_hash(str(S.x))
            key_hash_map[hash_value].append(S.x)
            if hash_value == target_hash:
                found_keys.append(S.x)

            S -= mG

    # Keys sharing similar hashes or public keys
    collisions = []
    for hash_value, keys in key_hash_map.items():
        if len(keys) > 1:
            collisions.append((hash_value, keys))

    return found_keys, collisions, key_hash_map, publickey_map

# Save Found Keys
def save_keys(keys, filename=FOUND_KEYS_FILE):
    with open(filename, 'a') as f:
        for key in keys:
            f.write(f"{key}\n")

# Save Collisions
def save_collisions(collisions, filename="collisions.txt"):
    with open(filename, 'w') as f:
        for hash_value, keys in collisions:
            f.write(f"Hash: {hash_value} -> Keys: {keys}\n")

# Main Execution
def main():
    logging.info("Loading public keys...")
    pubkeys = load_pubkeys(TARGET_KEYS)
    Qlist = [pubkey_to_point(pub) for pub in pubkeys]

    logging.info("Generating baby-step table...")
    baby_steps = create_baby_step_table(DEFAULT_M)

    logging.info("Starting giant-step search...")
    mG = DEFAULT_M * secp256k1.G
    k1G = 0x40000 * secp256k1.G

    # Parallel Processing
    with Pool(cpu_count()) as pool:
        results = pool.map(
            giant_step,
            [(Qlist[i::cpu_count()], k1G, mG, baby_steps) for i in range(cpu_count())]
        )

    # Collect and Save Results
    found_keys = []
    collisions = []
    for result in results:
        found_keys.extend(result[0])
        collisions.extend(result[1])

    save_keys(found_keys)
    save_collisions(collisions)

    logging.info(f"Keys found: {len(found_keys)}")
    logging.info(f"Collisions found: {len(collisions)}")
    logging.info("Process complete.")

if __name__ == "__main__":
    main()
