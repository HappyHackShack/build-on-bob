# Build on Bob

An automated deployment system.

## Installation

Once you have cloned this repo onto the machine that you want to be the BOB server and ***you have sudo rights***.

```bash
cd <code-repo>/installer
# Check your config (adjust as needed)
vi config.yaml
# Set your environment ready for ansible
export BECOME_PASS='<your password>'
# Run the ansible installer
ansible-playbook install-bob.yaml
```

## Issues

- Rocky seems to have an issue if the drive was already partitioned
- Check the 'edit' is valid (exists)

## Ideas To-Do

- Bugs
  - ?

- Main
  - [ ] Test of second machine
  - [x] Fix the fetcher

- Deploy
  - [ ] Alpine from https://dl-cdn.alpinelinux.org/alpine/v3.20/releases/cloud/generic_alpine-3.20.3-x86_64-uefi-cloudinit-metal-r0.qcow2
  - [ ] FCOS
  - [ ] Fedora
  - [x] Ubuntu

- Build the Wendy Web interface
