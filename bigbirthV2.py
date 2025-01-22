#!/usr/bin/env python3

import os
import hashlib
import time
import logging
import argparse
from multiprocessing import Pool, cpu_count
from fastecdsa.curve import secp256k1
from fastecdsa.point import Point
from collections import defaultdict

# Constants (can be overridden via arguments)
DEFAULT_M = 500000
DEFAULT_BITS = 24  # Default hash space size increased to 24 bits
DEFAULT_BS_FILE = 'baby_steps_table.txt'
DEFAULT_FOUND_KEYS_FILE = 'found_keys.txt'
DEFAULT_COLLISIONS_FILE = 'collisions.txt'
DEFAULT_TARGET_KEYS_FILE = 'pubkeys.txt'
DEFAULT_LOG_FILE = 'collision_log.txt'

# Logging Configuration
logging.basicConfig(
    filename=DEFAULT_LOG_FILE,
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def parse_arguments():
    parser = argparse.ArgumentParser(description="Optimized Baby-Step Giant-Step script for finding private keys.")
    parser.add_argument('--m', type=int, default=DEFAULT_M, help='Number of Baby-Steps.')
    parser.add_argument('--bits', type=int, default=DEFAULT_BITS, help='Number of bits for hash truncation.')
    parser.add_argument('--bs_file', type=str, default=DEFAULT_BS_FILE, help='Filename for the Baby-Step table.')
    parser.add_argument('--found_keys_file', type=str, default=DEFAULT_FOUND_KEYS_FILE, help='Filename for found keys.')
    parser.add_argument('--collisions_file', type=str, default=DEFAULT_COLLISIONS_FILE, help='Filename for collisions.')
    parser.add_argument('--target_keys', type=str, default=DEFAULT_TARGET_KEYS_FILE, help='Filename for target public keys.')
    args, unknown = parser.parse_known_args()
    return args

# Hash Function with Configurable Hash Space
def truncated_hash(input_data, bits=DEFAULT_BITS):
    full_hash = hashlib.sha256(input_data.encode()).hexdigest()
    return full_hash[:bits // 4]  # Adjust truncation based on bit size

# Create Baby-Step Table
def create_baby_step_table(m, curve=secp256k1):
    logging.info(f"Creating Baby-Step table with m={m}")
    baby_steps = {}
    for i in range(m):
        point = i * curve.G
        baby_steps[point.x] = baby_steps.get(point.x, []) + [i]  # Maintain lists for multiple steps
        if i % (m // 10) == 0 and i > 0:
            logging.debug(f"Created {i} out of {m} Baby-Steps")
    logging.info("Baby-Step table created successfully.")
    return baby_steps

# Load Public Keys with Validation
def load_pubkeys(filename):
    keys = []
    try:
        with open(filename, 'r') as f:
            for line_num, line in enumerate(f, 1):
                key = line.strip()
                if key and (len(key) in {66, 130}) and key[:2] in {'02', '03', '04'}:
                    keys.append(key)
                else:
                    logging.warning(f"Invalid key on line {line_num}: {key}")
    except FileNotFoundError:
        logging.error(f"File not found: {filename}")
        raise
    except Exception as e:
        logging.error(f"Error reading {filename}: {e}")
        raise
    logging.info(f"{len(keys)} valid public keys loaded.")
    return keys

# Convert Public Key to Point with Error Handling
def pubkey_to_point(pubkey):
    try:
        if pubkey.startswith('04'):  # Uncompressed format
            x = int(pubkey[2:66], 16)
            y = int(pubkey[66:], 16)
        else:  # Compressed format
            x = int(pubkey[2:66], 16)
            alpha = (x**3 + 7) % secp256k1.q
            beta = pow(alpha, (secp256k1.q + 1) // 4, secp256k1.q)
            if (pubkey[:2] == '02' and beta % 2 == 0) or (pubkey[:2] == '03' and beta % 2 != 0):
                y = beta
            else:
                y = secp256k1.q - beta
        return Point(x, y, curve=secp256k1)
    except ValueError as e:
        logging.error(f"ValueError in pubkey_to_point for key {pubkey}: {e}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error in pubkey_to_point for key {pubkey}: {e}")
        return None

# Giant-Step Function for Parallel Search
def giant_step(args):
    Qlist, k1G, mG, baby_steps, bits = args
    found_keys = []
    collisions = []
    key_hash_map = defaultdict(list)
    target_hash = truncated_hash("TARGET", bits=bits)

    for Q in Qlist:
        if Q is None:
            continue
        S = Q - k1G
        for j in range(DEFAULT_M):
            if S.x in baby_steps:
                for i in baby_steps[S.x]:
                    private_key = i + j * DEFAULT_M
                    found_keys.append(private_key)

            hash_value = truncated_hash(str(S.x), bits=bits)
            key_hash_map[hash_value].append(S.x)
            if hash_value == target_hash:
                found_keys.append(S.x)

            S -= mG

    for hash_value, keys in key_hash_map.items():
        if len(keys) > 1:
            collisions.append((hash_value, keys))

    return found_keys, collisions

# Save Keys
def save_keys(keys, filename=DEFAULT_FOUND_KEYS_FILE):
    if not keys:
        logging.info("No keys found to save.")
        return
    try:
        with open(filename, 'a') as f:
            for key in keys:
                f.write(f"{key}\n")
        logging.info(f"{len(keys)} keys saved to {filename}.")
    except Exception as e:
        logging.error(f"Error saving keys to {filename}: {e}")

# Save Collisions
def save_collisions(collisions, filename=DEFAULT_COLLISIONS_FILE):
    if not collisions:
        logging.info("No collisions found to save.")
        return
    try:
        with open(filename, 'w') as f:
            for hash_value, keys in collisions:
                f.write(f"Hash: {hash_value} -> Keys: {keys}\n")
        logging.info(f"{len(collisions)} collisions saved to {filename}.")
    except Exception as e:
        logging.error(f"Error saving collisions to {filename}: {e}")

# Main Function
def main(m=DEFAULT_M, bits=DEFAULT_BITS, bs_file=DEFAULT_BS_FILE, 
         found_keys_file=DEFAULT_FOUND_KEYS_FILE, collisions_file=DEFAULT_COLLISIONS_FILE, 
         target_keys=DEFAULT_TARGET_KEYS_FILE):
    
    start_time = time.time()
    logging.info("Starting private key search script.")

    # Load Public Keys
    logging.info("Loading public keys...")
    pubkeys = load_pubkeys(target_keys)
    Qlist = [pubkey_to_point(pub) for pub in pubkeys]

    # Create Baby-Step Table
    logging.info("Generating Baby-Step table...")
    baby_steps = create_baby_step_table(m)

    # Define mG and k1G
    mG = m * secp256k1.G
    k1G_scalar = 0x40000  # Configurable scalar value
    k1G = k1G_scalar * secp256k1.G

    # Prepare Parallel Processing Arguments
    num_processes = cpu_count()
    chunk_size = max(1, len(Qlist) // num_processes)
    args_list = [
        (Qlist[i * chunk_size: (i + 1) * chunk_size], k1G, mG, baby_steps, bits)
        for i in range(num_processes)
    ]

    # Start Parallel Processing
    logging.info(f"Starting parallel processing with {num_processes} processes...")
    with Pool(processes=num_processes) as pool:
        results = pool.map(giant_step, args_list)

    # Collect and Save Results
    found_keys = []
    collisions = []
    for result in results:
        found_keys.extend(result[0])
        collisions.extend(result[1])

    save_keys(found_keys, found_keys_file)
    save_collisions(collisions, collisions_file)

    elapsed_time = time.time() - start_time
    logging.info(f"Keys found: {len(found_keys)}")
    logging.info(f"Collisions found: {len(collisions)}")
    logging.info(f"Process completed in {elapsed_time:.2f} seconds.")

if __name__ == "__main__":
    args = parse_arguments()
    main(
        m=args.m,
        bits=args.bits,
        bs_file=args.bs_file,
        found_keys_file=args.found_keys_file,
        collisions_file=args.collisions_file,
        target_keys=args.target_keys
    )
