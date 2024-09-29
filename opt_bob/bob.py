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

My_Dir = os.path.dirname(__file__)
Config_File = '/etc/bob/engine.yaml'
Recipe_File = f'{My_Dir}/recipes.yaml'
Hosts_File = '/etc/bob/hosts.yaml'
Nginx_Base_Dir = '/usr/share/nginx/html'
Nginx_Ipxe_Dir = f'{Nginx_Base_Dir}/ipxe'
Nginx_Build_Dir = f'{Nginx_Base_Dir}/build'
Template_Dir = f"{My_Dir}/templates"
Etc_Bob_Hosts = {}

#print('Starting the BOB engine ...')
with open(Config_File,'rt') as cfg:
    Config = yaml.safe_load(cfg)
with open(Recipe_File,'rt') as rcp:
    Recipes = yaml.safe_load(rcp)



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
    # Now re-write the dnsmasq and host data
    write_dnsmasq_hosts(Hosts)
    write_host_build_files(new_host)
    print(f"{GREEN}New host '{WHITE}{Hostname}{GREEN}' added{END}")


def build_host(Hostname, New_OS):
    Hosts, host = load_hosts_yaml(Hostname)
    if not host:
        print(f"{YELLOW}WARNING: I didn't recognize that hostname")
        return
    if New_OS:
        host['os'] = New_OS
    host['target'] = 'build'
    #
    save_hosts_yaml()
    write_host_build_files(host)
    print(f"{CYAN}Host '{Hostname}' set to BUILD mode")


def complete_host(Host_or_MAC):
    Hosts, host = load_hosts_yaml(Host_or_MAC, Host_or_MAC)
    if not host:
        print(f"{YELLOW}WARNING: I didn't recognize that hostname")
        return
    host['target'] = 'local'
    save_hosts_yaml()
    write_host_build_files(host)
    print(f"{CYAN}Host '{Host_or_MAC}' set to LOCAL boot mode")


def delete_host(Hostname):
    Hosts, host = load_hosts_yaml(Hostname)
    if not host:
        print(f"{YELLOW}WARNING: I didn't recognize that hostname${END}")
        return
    Hosts.remove(host)
    wipe_host_build_files(host)
    write_dnsmasq_hosts(Hosts)
    save_hosts_yaml()
    print(f"{CYAN}Host '{Hostname}' deleted")


def edit_host(Hostname, Key, Value):
    Hosts, host = load_hosts_yaml(Hostname)
    if not host:
        print(f"{YELLOW}WARNING: I didn't recognize that hostname")
        return
    if Key not in ['hostname', 'mac', 'ip_addr', 'disk']:
        print(f"{YELLOW}WARNING: I don't know the key '{Key}'")
        return
    host[Key] = Value
    save_hosts_yaml()
    if host['target'] == 'build':
        write_host_build_files(host)
    print(f"{CYAN}Host '{Hostname}' set '{Key}' to be '{Value}' at next build")


def load_hosts_yaml(Hostname=None, MAC=None):
    # Only need to define a global to write to it
    global Etc_Bob_Hosts
    
    with open(Hosts_File, 'rt') as ipf:
        Etc_Bob_Hosts = yaml.safe_load(ipf)
    Hosts = Etc_Bob_Hosts
    if Hostname or MAC:
        for host in Hosts:
            if (host['hostname'] == Hostname) or (host['mac'] == MAC):
                return (Hosts, host)
        return (Hosts, None)
    return (Hosts)


def list_hosts():
    Hosts = load_hosts_yaml()
    if len(Hosts) == 0:
        print(f"{YELLOW}You don't have any hosts yet{END}")
    else:
        print(f'{BG_GRAY}  Hostname        MAC               / IP              OS        Disk        Build ?   {END}')
        for h in Hosts:
            bld = GRAY if h['target'] == 'local' else RED
            print(f"  {h['hostname']:15} {BLUE}{h['mac']} / {CYAN}{h['ip_addr']:15}{END} {h['os']:9} {h['disk']:11} {bld}{h['target']}{END}")


def list_recipes():
    print('I know about the following recipes:')
    for recipe in Recipes:
        print(f"{CYAN}    {recipe}{END}")


def render_template(Template_Filename, Config, Target_Filename):
    environment = Environment(loader=FileSystemLoader(Template_Dir))
    template = environment.get_template(Template_Filename)
    rendered = template.render(Config)

    with open(Target_Filename, 'wt') as cfg:
        cfg.write(rendered)
        cfg.write('\n')


def save_hosts_yaml():
    with open(Hosts_File, 'wt') as opf:
        yaml.dump(Etc_Bob_Hosts, opf)


def wipe_host_build_files(Host):
    for directory in [ Nginx_Ipxe_Dir, Nginx_Ipxe_Dir]:
        for filename in os.listdir(directory):
            if Host['mac'] in filename:
                os.unlink(f"{directory}/{filename}")


def write_dnsmasq_hosts(Hosts):
    with open('/etc/dnsmasq.d/hosts.conf','wt') as dns:
        for host in Hosts:
            dns.write(f"dhcp-host={host['mac']},{host['ip_addr']},{host['hostname']}\n")


def write_host_build_files(Host):
    wipe_host_build_files(Host)
    recipe = Recipes['local'] if Host['target'] == 'local' else Recipes[Host['os']]
    for template in recipe['templates']:
        tpl_name = template['name']
        output = template['output'].replace('MAC', Host['mac'])
        print(f'{GRAY}Writing template {tpl_name} --> {output}{END}')
        render_template( tpl_name, Config|Host, f"{Nginx_Base_Dir}/{output}")


##---------------------------------------------------------------------------------------------------------------------

Action = sys.argv[1]
if len(sys.argv) > 2:
    Noun = sys.argv[2]
if Action in ['a', 'add']:
    if Noun in ['h', 'host']:
        add_host(sys.argv[3],sys.argv[4],sys.argv[5])
if Action in ['b', 'build']:
    if Noun in ['h', 'host']:
        build_host(sys.argv[3], sys.argv[4])
if Action in ['c', 'complete']:
    if Noun in ['h', 'host']:
        complete_host(sys.argv[3])
if Action in ['d', 'delete']:
    if Noun in ['h', 'host']:
        delete_host(sys.argv[3])
if Action in ['e', 'edit']:
    if Noun in ['h', 'host']:
        edit_host(sys.argv[3], sys.argv[4], sys.argv[5])
if Action in ['l', 'list']:
    if Noun in ['h', 'host', '']:
        list_hosts()
    if Noun in ['r', 'recipes']:
        list_recipes()
