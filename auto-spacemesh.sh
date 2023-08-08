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
  sudo apt-get install -y -q jq wget python3 python3-pip git
elif [[ "$OSTYPE" == "darwin"* ]]; then
  echo "MacOS detected"
  brew install -q jq wget python3 git
elif [[ "$OSTYPE" == "win32" ]]; then
  echo "Windows detected"
  exit 1
else
  echo "Unsupported OS"
  exit 1
fi

# Clone the auto-spacemesh repo
echo "Cloning auto-spacemesh repo"
rm -rf /tmp/auto-spacemesh
git clone -q https://github.com/smeshcloud/auto-spacemesh.git /tmp/auto-spacemesh
cd /tmp/auto-spacemesh

# Install Python dependencies
echo "Installing Python dependencies"
pip3 install -qqq -r requirements.txt

# Present the user with choices and loop
while true; do
  echo ""
  echo "Choose an option:"
  echo "1. Generate a new Spacemesh node/smesher config"
  echo "2. Generate a new Spacemesh node/smesher config and start smeshing"
  echo "3. Start smeshing using an existing Spacemesh node/smesher config"
  echo "4. Start smeshing using an existing Spacemesh node/smesher config and start smeshing"
  echo "5. Exit"
  read -p "> " choice
  echo ""

  # Execute the user's choice
  case "$choice" in
    1)
      echo "Generating a new Spacemesh node/smesher config"
      bash stage1.sh
      ;;
    2)
      echo "Generating a new Spacemesh node/smesher stage1 config and start smeshing"
      bash stage1.sh
      python3 stage2.py
      ;;
    3)
      # Ask the user for the directory of the Spacemesh node/smesher config and default to /tmp/stage1 on Linux and MacOS and C:\TEMP\stage1 on Windows
      if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        default_path="/tmp/stage1"
      elif [[ "$OSTYPE" == "darwin"* ]]; then
        default_path="/tmp/stage1"
      elif [[ "$OSTYPE" == "win32" ]]; then
        default_path="C:\TEMP\stage1"
      else
        echo "Unsupported OS"
        exit 1
      fi
      echo -n "Path to existing Spacemesh node/smesher stage1 config [${default_path}]: "
      read -r path
      path=${path:-$default_path}
      # Check if the directory exists
      if [[ ! -d "$path" ]]; then
        echo "Directory does not exist"
      else
        echo "Starting the smesher using stage1 config in $path"
        python3 stage2.py "$path"
      fi
      ;;
    4)
      # Ask the user for the directory of the Spacemesh node/smesher config and default to /tmp/stage1 on Linux and MacOS and C:\TEMP\stage1 on Windows
      if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        default_path="/tmp/stage1"
      elif [[ "$OSTYPE" == "darwin"* ]]; then
        default_path="/tmp/stage1"
      elif [[ "$OSTYPE" == "win32" ]]; then
        default_path="C:\TEMP\stage1"
      else
        echo "Unsupported OS"
        exit 1
      fi
      echo -n "Path to existing Spacemesh node/smesher stage1 config [${default_path}]: "
      read -r path
      path=${path:-$default_path}
      # Check if the directory exists
      if [[ ! -d "$path" ]]; then
        echo "Directory does not exist"
      else
        echo "Starting the smesher using stage1 config in $path"
        python3 stage2.py "$path"
        python3 stage3.py
      fi
      ;;
    5)
      echo "Exiting"
      exit 0
      ;;
    *)
      echo "Invalid choice"
      ;;
  esac
done
