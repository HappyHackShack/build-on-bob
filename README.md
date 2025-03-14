# Build on Bob

An automated OS deployment system for Physicals and Virtuals - aimed at the cloud-native world.

## Installation

Once you have cloned this repo onto the machine that you want to be the BoB server and ***you have sudo rights***.

```bash
# Install ansible (from PIP)
dnf install -y git python3-pip python3-libdnf5
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
load the initialising data:
curl -x POST http://127.0.0.1:7999/initialise/database
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

## BIOS Installs

https://forum.level1techs.com/t/linux-installation-using-i-pxe/186721 - has a BIG menu of network booting many linuxes

## Lara (BIOS)

Client-Ethernet-Address f0:1f:af:45:86:5a (oui Unknown)
Vendor-rfc1048 Extensions
Magic Cookie 0x63825363
DHCP-Message (53), length 1: Discover
Parameter-Request (55), length 36: 
    Subnet-Mask (1), Time-Zone (2), Default-Gateway (3), Time-Server (4)
    IEN-Name-Server (5), Domain-Name-Server (6), RL (11), Hostname (12)
    BS (13), Domain-Name (15), SS (16), RP (17)
    EP (18), RSZ (22), TTL (23), BR (28)
    YD (40), YS (41), NTP (42), Vendor-Option (43)
    Requested-IP (50), Lease-Time (51), Server-ID (54), RN (58)
    RB (59), Vendor-Class (60), TFTP (66), BF (67)
    Unknown (128), Unknown (129), Unknown (130), Unknown (131)
    Unknown (132), Unknown (133), Unknown (134), Unknown (135)
MSZ (57), length 2: 1260
GUID (97), length 17: 0.68.69.76.76.76.0.16.87.128.57.183.192.79.83.89.49
ARCH (93), length 2: 0
NDI (94), length 3: 1.2.1
Vendor-Class (60), length 32: "PXEClient:Arch:00000:UNDI:002001"
END (255), length 0
PAD (0), length 0, occurs 200

## Lara (UEFI)

Client-Ethernet-Address f0:1f:af:45:86:5a (oui Unknown)
Vendor-rfc1048 Extensions
Magic Cookie 0x63825363
DHCP-Message (53), length 1: Discover
MSZ (57), length 2: 1464
Parameter-Request (55), length 35: 
    Subnet-Mask (1), Time-Zone (2), Default-Gateway (3), Time-Server (4)
    IEN-Name-Server (5), Domain-Name-Server (6), Hostname (12), BS (13)
    Domain-Name (15), RP (17), EP (18), RSZ (22)
    TTL (23), BR (28), YD (40), YS (41)
    NTP (42), Vendor-Option (43), Requested-IP (50), Lease-Time (51)
    Server-ID (54), RN (58), RB (59), Vendor-Class (60)
    TFTP (66), BF (67), GUID (97), Unknown (128)
    Unknown (129), Unknown (130), Unknown (131), Unknown (132)
    Unknown (133), Unknown (134), Unknown (135)
GUID (97), length 17: 0.68.69.76.76.76.0.16.87.128.57.183.192.79.83.89.49
NDI (94), length 3: 1.3.16
ARCH (93), length 2: 7
Vendor-Class (60), length 32: "PXEClient:Arch:00007:UNDI:003016"
END (255), length 0

## Lara (iPXE)

Client-Ethernet-Address f0:1f:af:45:86:5a (oui Unknown)
Vendor-rfc1048 Extensions
Magic Cookie 0x63825363
DHCP-Message (53), length 1: Discover
MSZ (57), length 2: 1472
ARCH (93), length 2: 7
NDI (94), length 3: 1.3.10
Vendor-Class (60), length 32: "PXEClient:Arch:00007:UNDI:003010"
User-Class (77), length 4: 
    instance#1: [ERROR: invalid option]
Parameter-Request (55), length 24: 
    Subnet-Mask (1), Default-Gateway (3), Domain-Name-Server (6), LOG (7)
    Hostname (12), Domain-Name (15), RP (17), MTU (26)
    NTP (42), Vendor-Option (43), Vendor-Class (60), TFTP (66)
    BF (67), Unknown (119), Unknown (128), Unknown (129)
    Unknown (130), Unknown (131), Unknown (132), Unknown (133)
    Unknown (134), Unknown (135), Unknown (175), Unknown (203)
Unknown (175), length 45: 177.5.1.128.134.21.2.235.3.1.0.0.23.1.1.36.1.1.19.1.1.20.1.1.17.1.1.39.1.1.41.1.1.21.1.1.38.1.1.27.1.1.18.1.1
Client-ID (61), length 7: ether f0:1f:af:45:86:5a
GUID (97), length 17: 0.68.69.76.76.76.0.16.87.128.57.183.192.79.83.89.49
END (255), length 0
