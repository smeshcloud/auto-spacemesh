#!/usr/bin/env python3

import sys
import os
import subprocess
import argparse
import json
import urllib.request

version = "1.0.0"
nodes = [
  "pub-node1.smesh.cloud:9092",
  "pub-node2.smesh.cloud:9092",
  "pub-node3.smesh.cloud:9092",
  "pub-node4.smesh.cloud:9092",
  "pub-node5.smesh.cloud:9092",
  "pub-node6.smesh.cloud:9092",
  "pub-node7.smesh.cloud:9092",
  "pub-node8.smesh.cloud:9092"
]

def download_grpcurl():
    # Download latest grpcurl from GitHub
    url = "https://github.com/fullstorydev/grpcurl/releases/latest/download/grpcurl_$(uname -s)_$(uname -m).tar.gz"
    try:
        response = urllib.request.urlopen(url)
        data = response.read()
        with open("/tmp/grpcurl.tar.gz", "wb") as file:
            file.write(data)
        print("Downloaded grpcurl successfully.")
    except:
        print("Error: Failed to download grpcurl from GitHub.")
        sys.exit(1)

    # Extract grpcurl
    try:
        subprocess.run(["tar", "-xzf", "/tmp/grpcurl.tar.gz", "-C", "/tmp/"], check=True)
        print("Extracted grpcurl successfully.")
    except:
        print("Error: Failed to extract grpcurl.")
        sys.exit(1)

    # Add grpcurl to PATH
    os.environ["PATH"] += ":/tmp/grpcurl"
    print("Added grpcurl to PATH.")

# Check if grpcurl is installed
try:
    result = subprocess.run(["grpcurl", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
except:
    download_grpcurl()

# Loop through the nodes
node_status = {}
for node in nodes:
    try:
        result = subprocess.run(["grpcurl", "-plaintext", "-d", "", node, "spacemesh.v1.NodeService.Status"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except:
        node_status[node] = {}
        continue

    if result and result.stdout:
        node_status[node] = json.loads(result.stdout.decode('utf-8'))['status']

not_synced_nodes = 0
synced_nodes = 0
verified_nodes = 0
total_nodes = len(node_status.keys())

print("================================================================================================================================")
print("PUBLIC NODES HEALTH CHECK")
print("================================================================================================================================")
for node in node_status.keys():
    if node_status[node] and node_status[node]['topLayer']:
        if abs(int(node_status[node]['topLayer']['number']) - int(node_status[node]['syncedLayer']['number'])) < 3 and abs(int(node_status[node]['verifiedLayer']['number']) - int(node_status[node]['syncedLayer']['number'])) < 3:
            synced = 'SYNCED & VERIFIED'
            synced_nodes += 1
            verified_nodes += 1
        elif abs(int(node_status[node]['topLayer']['number']) - int(node_status[node]['syncedLayer']['number'])) < 3:
            synced = 'SYNCED           '
            synced_nodes += 1
        else:
            synced = 'NOT SYNCED       '
            not_synced_nodes += 1
        print(f"Node {node} - {synced} - Peers: {node_status[node]['connectedPeers'] if 'connectedPeers' in node_status[node] else 'N/A'}, Top Layer: {node_status[node]['topLayer']['number']}, Synced Layer: {node_status[node]['syncedLayer']['number']}, Verified Layer: {node_status[node]['verifiedLayer']['number']}")
    else:
        print(f"Node {node} - Not connected")

print("================================================================================================================================")
print(f"Not synced: {not_synced_nodes}/{total_nodes}, Synced: {synced_nodes}/{total_nodes}, Verified: {verified_nodes}/{total_nodes}")
print("================================================================================================================================")
