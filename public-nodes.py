#!/usr/bin/env python3

import sys
import os
import subprocess
import argparse
import json
import urllib.request

version = "1.0.0"
nodes = [
  "public.smesh.cloud:9092",
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

def column_data_from_node(node):
  data = {
    'name': node['name'],
    'port': node['port'],
    'version': node['version'] if 'version' in node else None,
    'peers': None,
    'topLayer': None,
    'syncedLayer': None,
    'verifiedLayer': None
  }

  if 'topLayer' in node and 'syncedLayer' in node and 'verifiedLayer' in node:
    data['status'] = 'SYNCED & VERIFIED' if abs(int(node['topLayer']['number']) - int(node['syncedLayer']['number'])) < 3 and abs(int(node['verifiedLayer']['number']) - int(node['syncedLayer']['number'])) < 3 else 'SYNCED' if abs(int(node['topLayer']['number']) - int(node['syncedLayer']['number'])) < 3 else 'NOT SYNCED'
    data['peers'] = node['connectedPeers']
    data['topLayer'] = node['topLayer']['number'] if node and node['topLayer'] else None
    data['syncedLayer'] = node['syncedLayer']['number'] if node and node['syncedLayer'] else None
    data['verifiedLayer'] = node['verifiedLayer']['number'] if node and node['verifiedLayer'] else None
  else:
    data['status'] = 'NOT AVAILABLE'

  return data

def print_node_status(node):
  global args, not_synced_nodes, synced_nodes, verified_nodes, columns
  if node and 'topLayer' in node:
    if abs(int(node['topLayer']['number']) - int(node['syncedLayer']['number'])) < 3 and abs(int(node['verifiedLayer']['number']) - int(node['syncedLayer']['number'])) < 3:
      synced_nodes += 1
      verified_nodes += 1
    elif abs(int(node['topLayer']['number']) - int(node['syncedLayer']['number'])) < 3:
      synced_nodes += 1
    else:
      not_synced_nodes += 1

  column_data = column_data_from_node(node)
  node_row = ""
  for column in columns:
    if column['enabled']:
      if column_data[column['key']] is not None:
        node_row += f"{column_data[column['key']]:{column['width']}} "
      else:
        node_row += f"{'':{column['width']}} "
  if len(node_row) > terminal_size.columns:
    node_row = node_row[:terminal_size.columns]
  print(node_row)

def print_all_node_status(nodes):
  global columns
  print("PUBLIC NODES HEALTH CHECK")
  print()

  # cycle through columns and update the width of each column to match the width of the max value in that column
  for column in columns:
    if column['enabled']:
      for node_id in nodes.keys():
        node = nodes[node_id]
        column_data = column_data_from_node(node)
        if column['key'] in column_data:
          column_width = len(str(column_data[column['key']]))
          if column_width > column['width']:
            column['width'] = column_width

  title_row = ""
  for column in columns:
    if column['enabled']:
      title_row += f"{column['name']:{column['width']}} "

  separator_row = ""
  for column in columns:
    if column['enabled']:
      separator_row += f"{'':-<{column['width']}} "

  print(title_row)
  print(separator_row)
  for node in nodes.values():
    print_node_status(node)

def print_all_nodes_summary():
  global not_synced_nodes, synced_nodes, verified_nodes, total_nodes
  print()
  print(f"Not synced: {not_synced_nodes}/{total_nodes}, Synced: {synced_nodes}/{total_nodes}, Verified: {verified_nodes}/{total_nodes}")


def main():
  global args, not_synced_nodes, synced_nodes, verified_nodes, total_nodes, terminal_size, columns

  args = parse_options()
  columns = [
    { "name": "Node", "key": "name", "width": 4, "align": "left", "align_char": " ", "enabled": True },
    { "name": "Port", "key": "port", "width": 4, "align": "right", "align_char": " ", "enabled": True },
    { "name": "Version", "key": "version", "width": 7, "align": "left", "align_char": " ", "enabled": args.node_version },
    { "name": "Status", "key": "status", "width": 6, "align": "left", "align_char": " ", "enabled": True },
    { "name": "Peers", "key": "peers", "width": 5, "align": "right", "align_char": " ", "enabled": True },
    { "name": "Top", "key": "topLayer", "width": 3, "align": "right", "align_char": " ", "enabled": True },
    { "name": "Synced", "key": "syncedLayer", "width": 6, "align": "right", "align_char": " ", "enabled": True },
    { "name": "Verified", "key": "verifiedLayer", "width": 8, "align": "right", "align_char": " ", "enabled": True }
  ]

  # Check if grpcurl is installed
  try:
      result = subprocess.run(["grpcurl", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
  except:
      download_grpcurl()

  terminal_size = os.get_terminal_size()

  node_status = {}
  for node in nodes:
      node_name, node_port = node.split(':')
      node_status[node] = { 'name': node_name, 'port': node_port }
      try:
        result = subprocess.run(["grpcurl", "-plaintext", "-d", "", node, "spacemesh.v1.NodeService.Status"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        node_status[node] = json.loads(result.stdout.decode('utf-8'))['status']
        node_status[node]['name'] = node_name
        node_status[node]['port'] = node_port
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
