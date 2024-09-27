# Build on Bob

An automated deployment system.

## Installation

* Check this code out onto the machine that you want to be the BOB server
* Go and open install-config.yaml and set the variables to relevant values for your environment.
* Have your environment variable BECOME_PASS set to be your password (and that you have sudo privileges)
* Run the install playbook: `ansible-playbook bob-server.yaml` to install on the local machine