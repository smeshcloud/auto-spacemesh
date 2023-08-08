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
cloud_provider=""
ssh_user=""
ssh_host=""
ssh_key=""
exec_destination="local"
config_path=""
coinbase_address=""
valid_choices=("1" "2" "3" "4")
valid_cloud_providers=("runpod" "valt")

display_help() {
  echo "Usage: auto-spacemesh.sh [OPTIONS]"
  echo "Options:"
  echo "  -h, --help            Display this help message and exit"
  echo "  -v, --version         Display version information and exit"
  echo "  -c, --config PATH     Configure the script"
  echo "  -C, --coinbase ADDR   Set the Coinbase address"
  echo "  -l, --local           Execute locally (default)"
  echo "  -s, --ssh USER@HOST   Execute remotely via SSH"
  echo "  -k, --ssh-key KEY     Use a specific SSH key"
  echo "  -b, --cloud PROVIDER  Execute in the cloud (runpod or valt)"
  echo "  -r, --run CHOICE      Run choice directly (1-4)"
}

display_version() {
  echo "auto-spacemesh version $version"
}

parse_options() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      -h | --help)
        display_help
        exit 0
        ;;
      -v | --version)
        display_version
        exit 0
        ;;
      -c | --config)
        if [[ -z $2 ]]; then
          echo "Option --config requires an argument"
          exit 1
        fi
        echo "Config option selected with argument: $2"
        config_path="$2"
        shift 2
        ;;
      -C | --coinbase)
        if [[ -z $2 ]]; then
          echo "Option --coinbase requires an argument"
          exit 1
        fi
        echo "Coinbase option selected with argument: $2"
        coinbase_address="$2"
        shift 2
        ;;
      -l | --local)
        if [[ $exec_destination == "ssh" || $exec_destination == "cloud" ]]; then
          echo "Cannot specify both --local and --ssh or --cloud options"
          exit 1
        fi
        echo "Local option selected"
        exec_destination="local"
        cloud_provider=""
        ssh_user=""
        ssh_host=""
        ssh_key=""
        shift
        ;;
      -s | --ssh)
        if [[ $exec_destination == "local" || $exec_destination == "cloud" ]]; then
          echo "Cannot specify both --local and --ssh or --cloud options"
          exit 1
        fi
        if [[ -z $2 ]]; then
          echo "Option --ssh requires an argument"
          exit 1
        fi
        echo "SSH option selected with argument: $2"
        exec_destination="ssh"
        ssh_user="${2%@*}"
        ssh_host="${2##*@}"
        cloud_provider=""
        shift 2
        ;;
      -k | --ssh-key)
        if [[ $exec_destination == "local" || $exec_destination == "cloud" ]]; then
          echo "Cannot specify both --local and --ssh or --cloud options"
          exit 1
        fi
        if [[ -z $2 ]]; then
          echo "Option --ssh-key requires an argument"
          exit 1
        fi
        echo "SSH key option selected with argument: $2"
        exec_destination="ssh"
        ssh_key="$2"
        cloud_provider=""
        shift 2
        ;;
      -b | --cloud)
        if [[ $exec_destination == "local" || $exec_destination == "ssh" ]]; then
          echo "Cannot specify both --local and --ssh or --cloud options"
          exit 1
        fi
        if [[ -z $2 ]]; then
          echo "Option --cloud requires an argument"
          exit 1
        fi
        echo "Cloud provider option selected with argument: $2"
        exec_destination="cloud"
        if [[ " ${valid_cloud_providers[@]} " =~ " $2 " ]]; then
          cloud_provider="$2"
        else
          echo "Invalid cloud provider: $2"
          exit 1
        fi
        ssh_user=""
        ssh_host=""
        ssh_key=""
        shift 2
        ;;
      -r | --run)
        if [[ -z $2 ]]; then
          echo "Option --run requires an argument"
          exit 1
        fi
        echo "Run option selected with choice: $2"
        if [[ " ${valid_choices[@]} " =~ " $2 " ]]; then
          run_choice="$2"
        else
          echo "Invalid choice: $2"
          exit 1
        fi
        shift 2
        ;;
      --)
        shift
        break
        ;;
      *)
        echo "Invalid option: $1"
        exit 1
        ;;
    esac
  done

  # Handle non-option arguments (if any)
  for arg in "$@"; do
    echo "Non-option argument: $arg"
  done
}

display_version
parse_options "$@"
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

# Parse command line arguments



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
      echo ""

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
      echo ""

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
