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
ansible-playbook install-bob.yaml --tags pre-req
ansible-playbook install-bob.yaml
```

## Issues

- Rocky seems to have an issue if the drive was already partitioned
- Check the 'edit' is valid (exists)

## Ideas To-Do

- Bugs
  - [x] List hosts with empty list

- Main
  - [ ] Test of second machine
  - [x] Fix the fetcher

- Deploy
  - [ ] Alpine
  - [ ] FCOS
  - [ ] Fedora
  - [x] Ubuntu

- Miscellaneous
  - [x] Move some of the installer into a 'pre-req' phase
  - [ ] Improve the build status

- Build the Wendy Web interface
