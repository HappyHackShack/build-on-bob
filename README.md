# Build on Bob

An automated OS deployment system for Physicals and Virtuals - aimed at teh cloud-native world.

## Installation

Once you have cloned this repo onto the machine that you want to be the BoB server and ***you have sudo rights***.

```bash
# Install ansible (from PIP)
dnf install -y git python3-pip
pip install ansible

cd <code-repo>/installer
# Check your config (adjust as needed)
vi config.yaml
# Run this as ROOT - OR set your environment ready for ansible
export BECOME_PASS='<your password>'
# Run the ansible installer
ansible-playbook install-bob.yaml --tags pre-req
ansible-playbook install-bob.yaml

# Ensure you have some Operating Systems defined, e.g.:
load the initialising data
# ... then generate the cache scripts
cd /opt/bob
bob gcs

# Finally fetch the cloud images
cd /usr/share/nginx/html
/opt/bob/populate-cache.sh OR /opt/bob/fetch-from-cache.sh
```

## Usage

You are now ready to start deploying hosts; e,g,

```bash
# Create a host
bob host add example 192.168.0.99 00:00:00:00:00:00
# Put it into build mode
bob host build example rocky
```
