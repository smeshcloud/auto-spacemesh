#!/usr/bin/env bash
#
# Execute the auto-spacemesh pipeline.
#
# Usage:
#
#  wget -O- https://raw.githubusercontent.com/smeshcloud/auto-spacemesh/main/auto-spacemesh.sh | bash
#
# Author:
#
#  Zanoryt <zanoryt@protonmail.com>
#

version="1.0.0"

echo "Auto-Spacemesh v$version"

# Install dependencies
echo "Installing dependencies"
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
  echo "Linux detected"
  sudo apt-get update
  sudo apt-get install -y jq wget python3 python3-pip
elif [[ "$OSTYPE" == "darwin"* ]]; then
  echo "MacOS detected"
  brew install jq wget python3
else
  echo "Unsupported OS"
  exit 1
fi
