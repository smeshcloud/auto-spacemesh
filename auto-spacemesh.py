#!/usr/bin/env python3
import sys
import os
import subprocess
import argparse

version = "1.0.0"
smesher_location = None
smesher_cloud_provider = None
smesher_ssh_user = None
smesher_ssh_host = None
smesher_ssh_key = None
node_location = None
node_cloud_provider = None
node_ssh_user = None
node_ssh_host = None
node_ssh_key = None
config_path = ""
coinbase_address = ""
valid_choices = ["1", "2", "3", "4"]
valid_cloud_providers = ["runpod", "valt"]
run_choice = None

def display_version():
    print("auto-spacemesh version", version)

def parse_options():
    global config_path, coinbase_address
    global smesher_location, smesher_cloud_provider, smesher_ssh_user, smesher_ssh_host, smesher_ssh_key
    global node_location, node_cloud_provider, node_ssh_user, node_ssh_host, node_ssh_key

    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--version", help="Display version information and exit", action="store_true")
    parser.add_argument("-c", "--config", help="Configuration file")
    parser.add_argument("-C", "--coinbase", help="Set the Coinbase address")
    parser.add_argument("-l", "--smesher-local", help="Execute locally (default)", action="store_true")
    parser.add_argument("-b", "--smesher-cloud", help="Execute in the cloud (runpod or valt)")
    parser.add_argument("-s", "--smesher-ssh", help="Execute remotely via SSH", action="store_true")
    parser.add_argument("-k", "--smesher-ssh-key", help="Use a specific SSH key")
    parser.add_argument("-L", "--node-local", help="Execute locally (default)", action="store_true")
    parser.add_argument("-B", "--node-cloud", help="Execute in the cloud (runpod or valt)")
    parser.add_argument("-S", "--node-ssh", help="Execute remotely via SSH", action="store_true")
    parser.add_argument("-K", "--node-ssh-key", help="Use a specific SSH key")
    parser.add_argument("-r", "--run", help="Run choice directly (1-4)")
    args = parser.parse_args()

    if args.version:
        display_version()
        sys.exit(0)

    if args.config:
        config_path = args.config
        print("Config option selected with argument:", config_path)

    if args.coinbase:
        coinbase_address = args.coinbase
        print("Coinbase option selected with argument:", coinbase_address)

    if args.smesher_local:
        print("Local option selected")
        smesher_location = "local"
        smesher_cloud_provider = ""
        smesher_ssh_user = ""
        smesher_ssh_host = ""
        smesher_ssh_key = ""

    if args.smesher_ssh:
        ssh_arg = args.smesher_ssh
        if "@" not in ssh_arg:
            print("Invalid argument for --ssh option")
            sys.exit(1)
        ssh_user, ssh_host = ssh_arg.split("@")
        print("SSH option selected with argument:", ssh_arg)
        smesher_location = "local"
        smesher_cloud_provider = ""
        smesher_ssh_user = ssh_user
        smesher_ssh_host = ssh_host

    if args.smesher_ssh_key:
        ssh_key = args.smesher_ssh_key
        print("SSH key option selected with argument:", ssh_key)
        smesher_ssh_key = ssh_key

    if args.smesher_cloud:
        cloud_arg = args.smesher_cloud
        if "=" in cloud_arg:
            cloud_arg = cloud_arg.split("=")[1]
        if cloud_arg not in valid_cloud_providers:
            print("Invalid argument for --smesher-cloud option")
            sys.exit(1)
        cloud_provider = cloud_arg
        print("Cloud provider option selected with argument:", cloud_provider)
        smesher_location = "cloud"
        smesher_cloud_provider = cloud_provider

    if args.run:
        run_choice = args.run
        if run_choice not in valid_choices:
            print("Invalid choice:", run_choice)
            sys.exit(1)
        print("Run option selected with choice:", run_choice)

    if not smesher_location:
        smesher_location = "local"
        print("No smesher location specified. Defaulting to local.")

def install_dependencies():
    print("Installing dependencies")
    if sys.platform.startswith("linux"):
        print("Linux detected")
        subprocess.run(["sudo", "apt-get", "update"])
        subprocess.run(["sudo", "apt-get", "install", "-y", "-q", "jq", "wget", "python3", "python3-pip", "git"])
    elif sys.platform.startswith("darwin"):
        print("MacOS detected")
        subprocess.run(["brew", "install", "-q", "jq", "wget", "python3", "git"])
    elif sys.platform.startswith("win32"):
        print("Windows detected")
        sys.exit(1)
    else:
        print("Unsupported OS")
        sys.exit(1)

def clone_repo():
    print("Cloning auto-spacemesh repo")
    subprocess.run(["rm", "-rf", "/tmp/auto-spacemesh"])
    subprocess.run(["git", "clone", "-q", "https://github.com/smeshcloud/auto-spacemesh.git", "/tmp/auto-spacemesh"])
    os.chdir("/tmp/auto-spacemesh")

def install_python_dependencies():
    print("Installing Python dependencies")
    subprocess.run(["pip3", "install", "-qqq", "-r", "requirements.txt"])

def generate_config():
    print("Generating a new Spacemesh node/smesher config")
    subprocess.run(["bash", "stage1.sh"])

def generate_config_and_start_smesher():
    print("Generating a new Spacemesh node/smesher stage1 config and start smeshing")
    subprocess.run(["bash", "stage1.sh"])
    subprocess.run(["python3", "stage2.py"])

def start_smesher_with_existing_config(path):
    print("Starting the smesher using stage1 config in", path)
    subprocess.run(["python3", "stage2.py", path])

def start_smesher_with_existing_config_and_start_smesher(path):
    print("Starting the smesher using stage1 config in", path)
    subprocess.run(["python3", "stage2.py", path])
    subprocess.run(["python3", "stage3.py"])

def main():
    global run_choice
    display_version()
    parse_options()
    print()

    install_dependencies()
    clone_repo()
    install_python_dependencies()

    while True:
        if not run_choice:
            print()
            print("Run option:")
            print()
            print("1. Generate a new Spacemesh node/smesher config")
            print("2. Generate a new Spacemesh node/smesher config and start smeshing")
            print("3. Start smeshing using an existing Spacemesh node/smesher config")
            print("4. Start smeshing using an existing Spacemesh node/smesher config and start smeshing")
            print("5. Exit")
            choice = input("> ")
            print()
        else:
            choice = run_choice
            run_choice = ""

        if choice == "1":
            generate_config()
        elif choice == "2":
            generate_config_and_start_smesher()
        elif choice == "3":
            default_path = "/tmp/stage1"
            if sys.platform.startswith("win32"):
                default_path = "C:\TEMP\stage1"
            path = input(f"Path to existing Spacemesh node/smesher stage1 config [{default_path}]: ") or default_path
            print()
            if not os.path.isdir(path):
                print("Directory does not exist")
            else:
                start_smesher_with_existing_config(path)
        elif choice == "4":
            default_path = "/tmp/stage1"
            if sys.platform.startswith("win32"):
                default_path = "C:\TEMP\stage1"
            path = input(f"Path to existing Spacemesh node/smesher stage1 config [{default_path}]: ") or default_path
            print()
            if not os.path.isdir(path):
                print("Directory does not exist")
            else:
                start_smesher_with_existing_config_and_start_smesher(path)
        elif choice == "5":
            print("Exiting...")
            sys.exit(0)
        else:
            print("Invalid choice")

if __name__ == "__main__":
    main()
