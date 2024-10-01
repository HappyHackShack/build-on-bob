# Build on Bob

An automated deployment system.

## Installation

Once you have cloned this repo onto the machine that you want to be the BoB server and ***you have sudo rights***.

```bash
# Install ansible (from PIP)
dnf install -y python3-pip
pip install ansible

cd <code-repo>/installer
# Check your config (adjust as needed)
vi config.yaml
# Run this as ROOT - OR set your environment ready for ansible
export BECOME_PASS='<your password>'
# Run the ansible installer
ansible-playbook install-bob.yaml --tags pre-req
ansible-playbook install-bob.yaml
# Finally fetch the cloud images
bob fetch
```

## Usage

You are now ready to start deploying hosts; e,g,

```bash
# Create a host
bob add example 192.168.0.99 00:00:00:00:00:00
# Put it into build mode
bob build example rocky
```
