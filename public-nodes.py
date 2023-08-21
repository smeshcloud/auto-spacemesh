#!/usr/bin/env python3

import sys
import os
import subprocess
import argparse
import json

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


# check if grpcurl is installed
try:
  result = subprocess.run(["grpcurl", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
except:
  print("Error: grpcurl is not installed. Please install it first (if linux, try \"apt install grpcurl\").")
  sys.exit(1)

# loop through the nodes
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
print("=========================`=======================================================================================================")
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
