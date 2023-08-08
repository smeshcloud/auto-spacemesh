#!/usr/bin/env python3
#
# Generate PoST via cloud based on the config file created by stage 1.
#
# Usage:
#
#   stage2.sh <path to config file>
#
# Author:
#
#   Zanoryt <zanoryt@protonmail.com>
#

import json
import os
from time import sleep
import runpod
import sys

runpod.api_key = "YOURKEY"
generate_post_url = "https://raw.githubusercontent.com/smeshcloud/multi-provider-generate-post/main/generate-post.sh"

print("Stage 2 Started")

# 1. Load the config details
stage1_path = "/tmp/stage1"
stage2_path = "/tmp/stage2"
os.makedirs(stage2_path, exist_ok=True)
config = json.load(open(f"{stage1_path}/stage1.json"))
# print(config)
print(f"S2.1 Loaded config from {stage1_path}/stage1.json")
print(f"S2.1   - Node ID: {config['node_id']}")
print(f"S2.1   - Commitment ATX ID: {config['commitment_atx_id']}")
print(f"S2.1   - Disk size: {config['disk_size']} GB")

# 2. Look for runpod availability
gpus = runpod.get_gpus()
print("S2.2 Cloud (RunPod) - Available GPUs:")
for gpu in gpus:
  print(f"S2.2  - {gpu['id']}")

quantity = 2
gpu_selected = { 'id': "NVIDIA GeForce RTX 4090", 'quantity': quantity }
# gpu_selected = { 'id': "NVIDIA RTX 6000 Ada Generation", 'quantity': quantity }
print(f"S2.2 Cloud(RunPod) - Selected GPU: {gpu_selected['id']} ({gpu_selected['quantity']}x)")
disk_size=config['disk_size']
lowest_price = None
ondemand_price = None

while lowest_price is None:
  gpu = runpod.get_gpu(gpu_selected['id'])
  lowest_price = gpu['lowestPrice']['minimumBidPrice']
  ondemand_price = gpu['lowestPrice']['uninterruptablePrice']
  # print(gpu)
  sleep(5)

# 3. If runpod is available, run the pod
pod = None
print(f"S2.3 Cloud(RunPod) - Trying to run a pod with {quantity} x GPU {gpu_selected['id']} and {disk_size}GB storage...")
print(f"S2.3  - Lowest price: {lowest_price * quantity}/hr")
print(f"S2.3  - On-demand price: {ondemand_price * quantity}/hr")
print()

# 4. If runpod is not available, wait until it is
print("S2.4 Cloud(RunPod) - Waiting for availability...", end='', flush=True)
while pod is None:
  pod = runpod.create_pod(
    name="post test",
    image_name="ghcr.io/smeshcloud/nvidia-cuda-opencl",
    gpu_type_id=gpu_selected['id'],
    gpu_count=gpu_selected['quantity'],
    container_disk_in_gb=disk_size,
    docker_args=f"bash -c 'wget -O- {generate_post_url} | bash -s ${disk_size} ${config['node_id']}'",
  )
  # print("Pod is not available yet, trying again in 15 seconds...")
  print('.', end='', flush=True)
  sleep(15)
print(' running!')
# print(pod)

print(f"S2.4 Cloud(RunPod) - Pod {pod['id']} is now running")
print(f"S2.4  - Pod id: {pod['id']}")
print(f"S2.4  - Pod Host ID: {pod['machine']['podHostId']}")
print(f"S2.4  - SSH command: ssh {pod['machine']['podHostId']}@ssh.runpod.io -i ~/.ssh/id_ed25519")

# 5. Write the pod details to a file
pod_details = {
  'pod_id': pod['id'],
  'pod_host_id': pod['machine']['podHostId'],
  'gpu': {
    'quantity': quantity,
    'type': gpu_selected['id'],
    'lowest_price': lowest_price,
    'ondemand_price': ondemand_price,
  },
  'disk_size': disk_size,
}
json.dump(pod_details, open(f"{stage2_path}/stage2.json", "w"))
print(f"S2.4 Cloud(RunPod) - Pod details written to {stage2_path}/stage2.json")

# 5. Wait for the pod to complete
print("S2.5 Cloud(RunPod) - Waiting for pod to complete", end='', flush=True)

print("S2.5 Cloud(RunPod) - Pod completed successfully")

# 6. Completion
# If the pod fails, exit with an error
if pod['status'] == 'failed':
  print("S2.6 Cloud(RunPod) - Pod failed, exiting with error, stage2 must run again (and data will be lost)")

# If the pod succeeds, transfer the PoST files from the pod to a storage platform (Backblaze B2)
print("S2.6 Cloud(RunPod) - Pod run completed, transferring PoST files to storage platform")
print("Stage 2 Complete")
