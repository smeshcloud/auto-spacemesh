#!/usr/bin/env python3
#
# Generate PoST via cloud based on the config file created by stage 1.
#
# Usage:
#
#   stage2.sh
#
# Author:
#
#   Zanoryt <zanoryt@protonmail.com>
#

import argparse
import json
import os
import subprocess
from time import sleep
import runpod
import sys

generate_post_url = "https://raw.githubusercontent.com/smeshcloud/multi-provider-generate-post/main/generate-post.sh"

# Parse command-line arguments
parser = argparse.ArgumentParser(description="Generate PoST")
parser.add_argument("--cloud", help="Cloud provider", required=False)
parser.add_argument("--cloud-key", help="Cloud provider API key", required=False)
parser.add_argument("--local", action="store_true", help="Generate PoST locally")
parser.add_argument("--ssh", action="store_true", help="Generate PoST remotely")
parser.add_argument("--ssh-key", help="SSH key for remote execution", required=False)
parser.add_argument("--gpu-quantity", help="Number of GPUs", default=1, type=int)
parser.add_argument("--data-dir", help="Directory for data files", default="data")
args = parser.parse_args()

cloud_provider = args.cloud
cloud_key = args.cloud_key
local_execution = args.local
ssh_execution = args.ssh
ssh_key = args.ssh_key
data_dir = args.data_dir
stage1_path = f"{data_dir}/stage1"
stage2_path = f"{data_dir}/stage2"
stage1_config_path = f"{stage1_path}/stage1.json"
stage1_config = json.load(open(stage1_config_path, "r"))

# Check if mutually exclusive options are provided together
if (cloud_provider and local_execution) or (cloud_provider and ssh_execution) or (local_execution and ssh_execution):
  print("Error: The options --cloud, --local, and --ssh cannot be used together.")
  sys.exit(1)
if not (cloud_provider or local_execution or ssh_execution):
  print("Error: One of the options --cloud, --local, or --ssh is required.")
  sys.exit(1)

print("Stage 2 Started")

os.makedirs(stage2_path, exist_ok=True)
print(f"S2.1 Loaded config from {stage1_config_path}")
print(f"S2.1   - Node ID: {stage1_config['node_id']}")
print(f"S2.1   - Commitment ATX ID: {stage1_config['commitment_atx_id']}")
print(f"S2.1   - Disk size: {stage1_config['disk_size']} GB")

if local_execution:
  print("S2.2 Local Execution - Running generate-post.sh locally")

  # Execute generate-post.sh locally
  subprocess.run(["bash", "generate-post.sh"])

  # Rest of the local execution logic

# 3. Execute generate-post.sh remotely via SSH
elif ssh_execution:
  if not ssh_key:
    print("Error: --ssh-key option is required for remote execution (--ssh).")
    sys.exit(1)

  print("S2.2 Remote Execution - Running generate-post.sh remotely via SSH")

  # Execute generate-post.sh remotely via SSH
  ssh_command = f"ssh -i {ssh_key} user@hostname 'bash generate-post.sh'"
  subprocess.run(ssh_command, shell=True)

  # Rest of the remote execution logic

# 4. Execute generate-post.sh via cloud provider
elif cloud_provider:
  if cloud_provider == "runpod":
    # Set runpod cloud provider API key
    if not cloud_key:
      print("Error: --cloud-key option is required for cloud provider execution (--cloud).")
      sys.exit(1)
    runpod.api_key = cloud_key

    # Look for runpod availability
    gpus = runpod.get_gpus()
    print("S2.2 Cloud (RunPod) - Available GPUs:")
    for gpu in gpus:
      print(f"S2.2  - {gpu['id']}")

    gpu_selected = {'id': "NVIDIA GeForce RTX 4090", 'quantity': args.gpu_quantity}
    gpu_selected = {'id': "NVIDIA GeForce RTX 4080", 'quantity': args.gpu_quantity}
    # gpu_selected = {'id': "NVIDIA RTX 6000 Ada Generation", 'quantity': args.gpu_quantity}
    print(f"S2.2 Cloud(RunPod) - Selected GPU: {gpu_selected['id']} ({gpu_selected['quantity']}x)")
    disk_size = stage1_config['disk_size']
    lowest_price = None
    ondemand_price = None

    print("S2.3 Cloud(RunPod) - Checking for pricing and availability...", end='', flush=True)
    while lowest_price is None:
      gpu = runpod.get_gpu(gpu_selected['id'])
      lowest_price = gpu['lowestPrice']['minimumBidPrice']
      ondemand_price = gpu['lowestPrice']['uninterruptablePrice']
      # print(gpu)
      print(".", end='', flush=True)
      sleep(5)
    print()

    # 3. If runpod is available, run the pod
    pod = None
    print(f"S2.3 Cloud(RunPod) - Trying to run a pod with {gpu_selected['quantity']} x GPU {gpu_selected['id']} and {disk_size}GB storage...")
    print(f"S2.3  - Lowest price: {lowest_price * gpu_selected['quantity']}/hr")
    print(f"S2.3  - On-demand price: {ondemand_price * gpu_selected['quantity']}/hr")
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
        docker_args=f"bash -c 'wget -O- {generate_post_url} | bash -s {disk_size} {stage1_config['node_id']}'",
      )
      # print("Pod is not available yet, trying again in 15 seconds...")
      print('.', end='', flush=True)
      sleep(15)
    print(' submitted!')
    # print(pod)

    print(f"S2.4 Cloud(RunPod) - Pod {pod['id']} is now running")
    print(f"S2.4  - Pod ID: {pod['id']}")
    print(f"S2.4  - Pod Host ID: {pod['machine']['podHostId']}")
    print(f"S2.4  - SSH Command: ssh {pod['machine']['podHostId']}@ssh.runpod.io -i ~/.ssh/id_ed25519")

    # 5. Write the pod details to a file
    pod_details = {
      'pod_id': pod['id'],
      'pod_host_id': pod['machine']['podHostId'],
      'gpu': {
        'quantity': gpu_selected['quantity'],
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
    if pod['failure']:
      print(f"S2.6 Cloud(RunPod) - Pod failed with error: {pod['failure']}")
      sys.exit(1)
    else:
      print("S2.6 Cloud(RunPod) - Pod completed successfully")

  elif cloud_provider == "valt":
    # Add Valt cloud provider logic here
    print("S2.2 Cloud (Valt) - Valt cloud provider is not implemented yet.")
    sys.exit(1)

  else:
    print("Invalid cloud provider. Supported options: runpod, valt")

print("Stage 2 Completed")
