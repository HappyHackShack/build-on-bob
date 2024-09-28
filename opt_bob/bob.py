#!/bin/env python3

from jinja2 import Environment, FileSystemLoader
import os
from pprint import pprint
import sys
import yaml

BLACK = '\x1b[30m'
RED  ='\x1b[31m'
GREEN = '\x1b[32m'
YELLOW = '\x1b[33m'
BLUE = '\x1b[34m'
MAGENTA = '\x1b[35m'
CYAN = '\x1b[36m'
GRAY = '\x1b[90m'
L_GRAY = '\x1b[37m'
L_RED = '\x1b[91m'
L_GREEN = '\x1b[92m'
L_YELLOW = '\x1b[93m'
L_BLUE = '\x1b[94m'
L_MAGENTA = '\x1b[95m'
L_CYAN = '\x1b[96m'
WHITE = '\x1b[97m'
BG_BLACK = '\x1b[40m'
BG_RED = '\x1b[41;30m'
BG_GREEN = '\x1b[42;30m'
BG_YELLOW = '\x1b[43;30m'
BG_BLUE = '\x1b[44;30m'
BG_MAGENTA = '\x1b[45;30m'
BG_CYAN = '\x1b[46;30m'
BG_GRAY = '\x1b[47;30m'
END = '\x1b[0m'

Config_File = '/etc/bob/engine.yaml'
Hosts_File = '/etc/bob/hosts.yaml'
IPXE_Host_Dir = '/usr/share/nginx/html/ipxe'
Build_Script_Dir = '/usr/share/nginx/html/builder'
My_dir = os.path.dirname(__file__)
Etc_Bob_Hosts = {}

#print('Starting the BOB engine ...')
with open(Config_File,'rt') as cfg:
    Config = yaml.safe_load(cfg)
# print(Config)

def add_host(Hostname, IP, MAC, OS='rescue'):
    Hosts = load_hosts_yaml()
    # Check IP address not already allocated
    for host in Hosts:
        if IP == host['ip_addr']:
            print(f"{RED}FAILED to add{END}: IP address is already allocated to {WHITE}{host['hostname']}{END}")
            return
    # All OK
    new_host = {'mac':MAC, 'ip_addr':IP, 'hostname':Hostname, 'os':OS, 'disk':'/dev/sda', 'target':'local'}
    Hosts.append(new_host)
    save_hosts_yaml()
    # Now re-write the dnsmasq data
    write_dnsmasq_hosts(Hosts)
    write_host_ipxe_cfg(new_host)
    print(f"{GREEN}New host '{WHITE}{Hostname}{GREEN}' added{END}")


def build_host(Hostname):
    Hosts, host = load_hosts_yaml(Hostname)
    if not host:
        print(f"{YELLOW}WARNING: I didn't recognize that hostname")
        return
    host['target'] = 'build'
    write_host_ipxe_cfg(host)
    write_host_build_scripts(host)
    save_hosts_yaml()
    print(f"{CYAN}Host '{Hostname}' set to BUILD mode")


def complete_host(Host_or_MAC):
    Hosts, host = load_hosts_yaml(Host_or_MAC, Host_or_MAC)
    if not host:
        print(f"{YELLOW}WARNING: I didn't recognize that hostname")
        return
    host['target'] = 'local'
    save_hosts_yaml()
    write_host_ipxe_cfg(host)
    print(f"{CYAN}Host '{Host_or_MAC}' set to LOCAL boot mode")


def delete_host(Hostname):
    Hosts, host = load_hosts_yaml(Hostname)
    if not host:
        print(f"{YELLOW}WARNING: I didn't recognize that hostname")
        return
    Hosts.remove(host)
    save_hosts_yaml()
    write_dnsmasq_hosts(Hosts)
    #
    mac = host['mac']
    ipxe_cfg = f"{IPXE_Host_Dir}/{mac}.cfg"
    if os.path.exists(ipxe_cfg):
        os.remove(ipxe_cfg)
    print(f"{CYAN}Host '{Hostname}' deleted")


def edit_host(Hostname, New_OS):
    Hosts, host = load_hosts_yaml(Hostname)
    if not host:
        print(f"{YELLOW}WARNING: I didn't recognize that hostname")
        return
    host['os'] = New_OS
    save_hosts_yaml()
    write_host_build_scripts(host)
    print(f"{CYAN}Host '{Hostname}' set to be '{New_OS}' at next build")


def load_hosts_yaml(Hostname=None, MAC=None):
    # Only need to define a global to write to it
    global Etc_Bob_Hosts
    
    with open(Hosts_File, 'rt') as ipf:
        Etc_Bob_Hosts = yaml.safe_load(ipf)
    Hosts = Etc_Bob_Hosts['hosts']
    if Hostname or MAC:
        for host in Hosts:
            if (host['hostname'] == Hostname) or (host['mac'] == MAC):
                return (Hosts, host)
        return (Hosts, None)
    return (Hosts)


def list_hosts():
    Hosts = load_hosts_yaml()
    print(f'{BG_GRAY}  Hostname        MAC               / IP              OS        Disk        Build ?   {END}')
    for h in Hosts:
        bld = GRAY if h['target'] == 'local' else RED
        print(f"  {h['hostname']:15} {BLUE}{h['mac']} / {CYAN}{h['ip_addr']:15}{END} {h['os']:9} {h['disk']:11} {bld}{h['target']}{END}")


def render_template(Template, Config, Target):
    environment = Environment(loader=FileSystemLoader(My_dir))
    template_name = f"{Template}"
    template = environment.get_template(template_name)
    rendered = template.render(Config)

    with open(Target, 'wt') as cfg:
        cfg.write(rendered)
        cfg.write('\n')


def save_hosts_yaml():
    with open(Hosts_File, 'wt') as opf:
        yaml.dump(Etc_Bob_Hosts, opf)


def write_dnsmasq_hosts(Hosts):
    with open('/etc/dnsmasq.d/hosts.conf','wt') as dns:
        for host in Hosts:
            dns.write(f"dhcp-host={host['mac']},{host['ip_addr']},{host['hostname']}\n")


def write_host_build_scripts(Host):
    # Build script
    script = f"{Build_Script_Dir}/{Host['mac']}.sh"
    render_template( f"{Host['os']}.sh.j2", Config|Host, script)
    # Meta-data
    meta = f"{Build_Script_Dir}/meta-{Host['mac']}"
    #render_template( f"ci-meta-data.j2", Config|Host, meta)
    with open(meta,'wt') as opf:
        opf.write('---\n')
    # User-data
    user = f"{Build_Script_Dir}/user-{Host['mac']}"
    render_template( f"{Host['os']}-ci-user.j2", Config|Host, user)


def write_host_ipxe_cfg(Host):
    fname = f"{IPXE_Host_Dir}/{Host['mac']}.cfg"
    render_template( f"{Host['target']}.ipxe.j2", Config, fname)


##---------------------------------------------------------------------------------------------------------------------

Action = sys.argv[1]
if len(sys.argv) > 2:
    Noun = sys.argv[2]
if Action == 'add':
    if Noun == 'host':
        add_host(sys.argv[3],sys.argv[4],sys.argv[5])
if Action == 'build':
    if Noun == 'host':
        build_host(sys.argv[3])
if Action == 'complete':
    if Noun == 'host':
        complete_host(sys.argv[3])
if Action == 'delete':
    if Noun == 'host':
        delete_host(sys.argv[3])
if Action == 'edit':
    if Noun == 'host':
        edit_host(sys.argv[3],sys.argv[4])
if Action == 'list':
    if Noun == 'hosts':
        list_hosts()
