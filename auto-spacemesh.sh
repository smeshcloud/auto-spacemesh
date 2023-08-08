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
echo ""

# Install dependencies
echo "Installing dependencies"
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
  echo "Linux detected"
  sudo apt-get update
  sudo apt-get install -y jq wget python3 python3-pip git
elif [[ "$OSTYPE" == "darwin"* ]]; then
  echo "MacOS detected"
  brew install jq wget python3 git
elif [[ "$OSTYPE" == "win32" ]]; then
  echo "Windows detected"
  exit 1
else
  echo "Unsupported OS"
  exit 1
fi

# Clone the auto-spacemesh repo
echo "Cloning auto-spacemesh repo"
git clone https://github.com/smeshcloud/auto-spacemesh.git /tmp/auto-spacemesh
cd /tmp/auto-spacemesh

# Install Python dependencies
echo "Installing Python dependencies"
pip3 install -r requirements.txt

# Execute the auto-spacemesh pipeline
echo "Executing auto-spacemesh pipeline"
./stage1.sh
python3 stage2.py
python3 stage3.py
python3 stage4.py
