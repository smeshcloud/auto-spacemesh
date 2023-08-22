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

def display_version():
  print("public-nodes.py version", version)

def parse_options():
  parser = argparse.ArgumentParser()
  # add argument to embed the remote server version in the status output
  parser.add_argument("--node-version", help="Embed the remote server version in the status output", action="store_true")
  parser.add_argument("-v", "--version", help="Display version information and exit", action="store_true")
  args = parser.parse_args()

  if args.version:
      display_version()
      sys.exit(0)

  return args

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

def print_node_status(node_name, node):
  global args, not_synced_nodes, synced_nodes, verified_nodes
  if node and node['topLayer']:
    if abs(int(node['topLayer']['number']) - int(node['syncedLayer']['number'])) < 3 and abs(int(node['verifiedLayer']['number']) - int(node['syncedLayer']['number'])) < 3:
      synced = 'SYNCED & VERIFIED'
      synced_nodes += 1
      verified_nodes += 1
    elif abs(int(node['topLayer']['number']) - int(node['syncedLayer']['number'])) < 3:
      synced = 'SYNCED           '
      synced_nodes += 1
    else:
      synced = 'NOT SYNCED       '
      not_synced_nodes += 1
    if args.node_version:
      print(f"Node {node_name} - {node['version']} - {synced} - Peers: {node['connectedPeers'] if 'connectedPeers' in node else 'N/A'}, Top Layer: {node['topLayer']['number']}, Synced Layer: {node['syncedLayer']['number']}, Verified Layer: {node['verifiedLayer']['number']}")
    else:
      print(f"Node {node_name} - {synced} - Peers: {node['connectedPeers'] if 'connectedPeers' in node else 'N/A'}, Top Layer: {node['topLayer']['number']}, Synced Layer: {node['syncedLayer']['number']}, Verified Layer: {node['verifiedLayer']['number']}")
  else:
    if args.node_version:
      print(f"Node {node_name} - {node['version']} - Not connected")
    else:
      print(f"Node {node_name} - Not connected")

def print_all_node_status(nodes):
  print("================================================================================================================================")
  print("PUBLIC NODES HEALTH CHECK")
  print("================================================================================================================================")
  for node in nodes.keys():
    print_node_status(node, nodes[node])

def print_all_nodes_summary():
  global not_synced_nodes, synced_nodes, verified_nodes, total_nodes
  print("================================================================================================================================")
  print(f"Not synced: {not_synced_nodes}/{total_nodes}, Synced: {synced_nodes}/{total_nodes}, Verified: {verified_nodes}/{total_nodes}")
  print("================================================================================================================================")


def main():
  global args, not_synced_nodes, synced_nodes, verified_nodes, total_nodes

  args = parse_options()

  # Check if grpcurl is installed
  try:
      result = subprocess.run(["grpcurl", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
  except:
      download_grpcurl()

  node_status = {}
  for node in nodes:
      node_status[node] = {}
      try:
        result = subprocess.run(["grpcurl", "-plaintext", "-d", "", node, "spacemesh.v1.NodeService.Status"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        node_status[node] = json.loads(result.stdout.decode('utf-8'))['status']
      except:
        continue

      if args.node_version:
        try:
          result = subprocess.run(["grpcurl", "-plaintext", "-d", "", node, "spacemesh.v1.NodeService.Version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        except:
          print(f"Error: Failed to connect to {node}.")
          sys.exit(1)
        version = json.loads(result.stdout.decode('utf-8'))['versionString']['value']
        node_status[node]['version'] = version

  not_synced_nodes = 0
  synced_nodes = 0
  verified_nodes = 0
  total_nodes = len(node_status.keys())

  print_all_node_status(node_status)
  print_all_nodes_summary()

if __name__ == "__main__":
  main()
