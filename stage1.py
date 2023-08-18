#!/usr/bin/env python3
#
# Generate node identity and details
#
# Usage:
#
#   stage1.sh
#
# Author:
#
#   Zanoryt <zanoryt@protonmail.com>
#

import argparse
import json
import os


# Parse command-line arguments
parser = argparse.ArgumentParser(description="Generate node identity and details")
parser.add_argument("--data-dir", help="Directory for data files", default="data")
args = parser.parse_args()

data_dir = args.data_dir
stage1_path = f"{data_dir}/stage1"
stage1_config_path = f"{stage1_path}/stage1.json"
if os.path.isfile(stage1_config_path):
  config = json.load(open(stage1_config_path, "r"))
else:
  config = {
    "node_id": None,
    "node_id_first_8": None,
    "commitment_atx_id": None,
    "labels_per_unit": 4_294_967_296,
    "num_units": 4,
    "max_file_size": 2_147_483_648,
  }
  config["disk_size"] = config["num_units"] * 64

# Check if node_id is provided otherwise generate it
if not config.get("node_id"):
  print("S1.1 Generating node ID")
  # generate a ed25518 key pair using pynacl
  import nacl.encoding
  import nacl.signing
  signing_key = nacl.signing.SigningKey.generate()
  verify_key = signing_key.verify_key
  signing_key_hex = signing_key.encode(encoder=nacl.encoding.HexEncoder).decode('utf-8')
  node_id = verify_key.encode(encoder=nacl.encoding.HexEncoder).decode("utf-8")
  bin_file = f"{stage1_path}/key.bin"
  with open(bin_file, "wb") as f:
    f.write(signing_key.encode())
  print(f"S1.1   - Node ID: {node_id} (saved to {bin_file})")
else :
  print(f"S1.1 Loaded node ID from {stage1_config_path}")
  print(f"S1.1   - Node ID: {node_id}")
