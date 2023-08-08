#!/usr/bin/env bash
#
# This script is used to build the first stage of the boot loader.
#
# Usage:
#
#   stage1.sh
#
#
# Author:
#
#   Zanoryt <zanoryt@protonmail.com>
#

echo "Stage 1 Started"

# Set the coinbase and data_dir variables
config_file="config.json"
coinbase="sm1qqqqqqxre24mtprsmuht8gfhu28z95hm22zvrdq34rmr8"
data_dir="/tmp/stage1"

go_spacemesh_dir="/Users/kevin/work/crypto/spacemesh/official/go-spacemesh"
go_spacemesh_bin="$go_spacemesh_dir/build/go-spacemesh"
go_spacemesh_log="/tmp/go-spacemesh.log"
grpc_public_listener="0.0.0.0:19092"
grpc_private_listener="127.0.0.1:19093"
grpc_json_listener="0.0.0.0:19094"
spacemesh_data_dir="/tmp/smesh-node-data"
filelock="/tmp/sm.lock"
listen="/ip4/0.0.0.0/tcp/7555"
smeshing_opts_datadir="/tmp/stage1"

# Retrieve the latest mainnet config template from https://smapp.spacemesh.network/config.mainnet.json
echo "S1.1 Retrieving latest mainnet config template"
wget https://smapp.spacemesh.network/config.mainnet.json -O config.mainnet.json -q

# Generate a new config.json from template
echo "S1.2 Generating config.json"

# Load and parse the config.json template
template=$(cat config.mainnet.json)

# Adjust api values in the template
# Set the grpc-public-listener, grpc-private-listener, and grpc-json-listener values
template=$(echo "$template" | jq --arg grpc_public_listener "$grpc_public_listener" '.api."grpc-public-listener" = $grpc_public_listener')
template=$(echo "$template" | jq --arg grpc_private_listener "$grpc_private_listener" '.api."grpc-private-listener" = $grpc_private_listener')
template=$(echo "$template" | jq --arg grpc_json_listener "$grpc_json_listener" '.api."grpc-json-listener" = $grpc_json_listener')


# Create the smeshing-opts object using the provided values
smeshing_opts='{
  "smeshing-opts-datadir": "'"$data_dir"'",
  "smeshing-opts-maxfilesize": 2147483648,
  "smeshing-opts-numunits": 6,
  "smeshing-opts-provider": 0,
  "smeshing-opts-throttle": false,
  "smeshing-opts-compute-batch-size": 1048576
}'

# Create the smeshing-proving-opts object
smeshing_proving_opts='{
  "smeshing-opts-proving-nonces": 0,
  "smeshing-opts-proving-threads": 0
}'

# Create the smeshing object with smeshing-opts, smeshing-coinbase, smeshing-proving-opts, and smeshing-start
smeshing='{
  "smeshing-opts": '"$smeshing_opts"',
  "smeshing-coinbase": "'"$coinbase"'",
  "smeshing-proving-opts": '"$smeshing_proving_opts"',
  "smeshing-start": false
}'

# Update the template with the new smeshing object
template=$(echo "$template" | jq '.smeshing = '"$smeshing")

# Persist the new config.json
echo "$template" > $config_file


# Spin up a new go-spacemesh node with the config.json
echo "S1.3 Starting go-spacemesh node"
$go_spacemesh_bin -d $spacemesh_data_dir --config $config_file --filelock $filelock --listen $listen --smeshing-opts-datadir $smeshing_opts_datadir 2>/dev/null > $go_spacemesh_log &

# Wait for the node to be ready
echo "S1.4 Waiting for node to be ready"
while true; do
  status=$(grpcurl -plaintext -d '' "$grpc_public_listener" spacemesh.v1.NodeService.Status 2>/dev/null)
  is_synced=$(echo "$status" | jq -r '.status.isSynced')
  if [ "$is_synced" = "true" ]; then
    echo "S1.4 Node is synced"
    break
  fi
  sleep 1
done

# Start the node's smesher service
echo "S1.5 Starting node smesher"
payload=$(jq -n --arg coinbase "$coinbase" --arg data_dir "$data_dir" '{ "coinbase": { "address": $coinbase }, "opts": { "data_dir": $data_dir, "num_units": 6, "max_file_size": 2147483648, "provider_id": 0, "throttle": false } }')
status=$(grpcurl -plaintext -d "$payload" "$grpc_private_listener" spacemesh.v1.SmesherService.StartSmeshing)
while true; do
  status=$(grpcurl -plaintext -d '' "$grpc_private_listener" spacemesh.v1.SmesherService.PostSetupStatus)
  state=$(echo "$status" | jq -r '.status.state')
  if [ "$state" = "STATE_NOT_STARTED" ] || [ "$state" = "STATE_PREPARED" ] || [ "$state" = "STATE_IN_PROGRESS" ]; then
    echo "S1.5 Node smesher is prepared"
    break
  fi
  sleep 1
done

# Get the node's smeshing service post setup status and wait for it to be complete (STATE_COMPLETE)
echo "S1.6 Waiting for node smesher setup to be complete"
while true; do
  status=$(grpcurl -plaintext -d '' "$grpc_private_listener" spacemesh.v1.SmesherService.PostSetupStatus)
  state=$(echo "$status" | jq -r '.status.state')
  if [ "$state" = "STATE_IN_PROGRESS" ]; then
    echo "S1.6 Node smesher init is complete"
    break
  fi
  if [ "$state" = "STATE_ERROR" ]; then
    echo "S1.6 Node smesher has errored"
    break
  fi
  sleep 1
done

# Stop the node's smesher service
echo "S1.7 Stopping node smesher"
status=$(grpcurl -plaintext -d '' "$grpc_private_listener" spacemesh.v1.SmesherService.StopSmeshing)

# Stop the node
echo "S1.8 Stopping node"
port=$(echo "$listen" | awk -F/ '{print $NF}')
echo "S1.8 Stopping node on port $port"
pid=$(lsof -t -i :"$port")
echo "S1.8 Killing node with pid $pid"
kill $pid
# Wait for the node to stop
while true; do
  if [ -z "$(lsof -t -i :"$port")" ]; then
    echo "S1.8 Node stopped"
    break
  fi
  sleep 1
done
rm -rf $filelock

# Extract the details from the node's metadata file
echo "S1.9 Extracting node smesher details"
node_id=$(jq -r '.NodeId' "$data_dir/postdata_metadata.json" | base64 -d | xxd -p -c 32 -g 32)
commitment_atx_id=$(jq -r '.CommitmentAtxId' "$data_dir/postdata_metadata.json" | base64 -d | xxd -p -c 32 -g 32)
labels_per_unit=$(jq -r '.LabelsPerUnit' "$data_dir/postdata_metadata.json")
num_units=$(jq -r '.NumUnits' "$data_dir/postdata_metadata.json")
max_file_size=$(jq -r '.MaxFileSize' "$data_dir/postdata_metadata.json")
echo "S1.9 Node smesher details extracted"
echo "S1.9   - Node ID: $node_id"
echo "S1.9   - Commitment ATX ID: $commitment_atx_id"
echo "S1.9   - Labels per unit: $labels_per_unit"
echo "S1.9   - Number of units: $num_units"
echo "S1.9   - Max file size: $max_file_size"

# Bundle up the node's smesher data directory and metadata file into a tarball
echo "S1.10 Bundling node smesher data"
echo '{
  "node_id": "'"$node_id"'",
  "commitment_atx_id": "'"$commitment_atx_id"'",
  "labels_per_unit": "'"$labels_per_unit"'",
  "num_units": "'"$num_units"'",
  "max_file_size": "'"$max_file_size"'",
  "disk_size": "'"$(($num_units*64))"'"
}' > $data_dir/stage1.json
echo "S1.10   - Saved details to stage1.json"
tar -czf /tmp/stage1.tar.gz -C $data_dir key.bin postdata_metadata.json stage1.json
file_size=$(du -m /tmp/stage1.tar.gz | awk '{print $1}')
echo "S1.10   - Created tarball at /tmp/stage1.tar.gz ($((file_size))MB) containing stage1.json, postdata_metadata.json and key.bin"

# Store the tarball + details locally or upload to a remote storage service
echo "S1.11 Uploading node smesher data to network storage"

echo "Stage 1 Complete"
