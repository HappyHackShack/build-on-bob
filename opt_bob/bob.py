#!/bin/env python3

from jinja2 import Environment, FileSystemLoader
import os
from pprint import pprint
import sys
import yaml

Config_File = '/etc/bob/engine.yaml'
Hosts_File = '/etc/bob/hosts.yaml'
IPXE_Host_Dir = '/usr/share/nginx/html/ipxe'
Build_Script_Dir = '/usr/share/nginx/html/builder'
My_dir = os.path.dirname(__file__)

print('Starting the BOB engine ...')
with open(Config_File,'rt') as cfg:
    Config = yaml.safe_load(cfg)
# print(Config)

def build_host(Hostname):
    Hosts, host = load_hosts_yaml(Hostname)
    if host:
        host['target'] = 'build'
        write_host_ipxe_cfg(host)
        write_host_build_script(host)
        save_hosts_yaml(Hosts)


def complete_host(MAC):
    Hosts, host = load_hosts_yaml(MAC=MAC)
    if host:
        host['target'] = 'local'
        save_hosts_yaml(Hosts)
        write_host_ipxe_cfg(host)


def create_host(MAC, IP, Hostname, OS='alpine'):
    Hosts = load_hosts_yaml()
    new_host = {'mac':MAC, 'ip_addr':IP, 'hostname':Hostname, 'os':OS, 'disk':'/dev/sda', 'target':'local'}
    Hosts['hosts'].append(new_host)
    save_hosts_yaml(Hosts)
    # Now re-write the dnsmasq data
    write_dnsmasq_hosts(Hosts)
    write_host_ipxe_cfg(new_host)


def delete_host(Hostname):
    Hosts, host = load_hosts_yaml(Hostname)
    if host:
        Hosts['hosts'].remove(host)
        save_hosts_yaml(Hosts)
        write_dnsmasq_hosts(Hosts)
        #
        mac = host['mac']
        ipxe_cfg = f"{IPXE_Host_Dir}/{mac}.cfg"
        if os.path.exists(ipxe_cfg):
            os.remove(ipxe_cfg)


def edit_host(Hostname, New_OS):
    Hosts, host = load_hosts_yaml(Hostname)
    if host:
        host['os'] = New_OS
        save_hosts_yaml(Hosts)
        write_host_build_script(host)


def load_hosts_yaml(Hostname=None, MAC=None):
    with open(Hosts_File, 'rt') as ipf:
        Hosts = yaml.safe_load(ipf)
    if Hostname or MAC:
        for host in Hosts['hosts']:
            if (host['hostname'] == Hostname) or (host['mac'] == MAC):
                return (Hosts, host)
        return (Hosts, None)
    return (Hosts)


def list_hosts():
    Hosts = load_hosts_yaml()
    for host in Hosts['hosts']:
        print(host)
        #write_host_ipxe_cfg(host)


def render_template(Template, Config, Target):
    environment = Environment(loader=FileSystemLoader(My_dir))
    template_name = f"{Template}"
    template = environment.get_template(template_name)
    rendered = template.render(Config)

    with open(Target, 'wt') as cfg:
        cfg.write(rendered)
        cfg.write('\n')


def save_hosts_yaml(Data):
    with open(Hosts_File, 'wt') as opf:
        yaml.dump(Data, opf)


def write_dnsmasq_hosts(Hosts):
    with open('/etc/dnsmasq.d/hosts.conf','wt') as dns:
        for host in Hosts['hosts']:
            dns.write(f"dhcp-host={host['mac']},{host['ip_addr']},{host['hostname']}\n")


def write_host_build_script(Host):
    fname = f"{Build_Script_Dir}/{Host['mac']}.sh"
    render_template( f"{Host['os']}.sh.j2", Config|Host, fname)


def write_host_ipxe_cfg(Host):
    fname = f"{IPXE_Host_Dir}/{Host['mac']}.cfg"
    render_template( f"{Host['target']}.ipxe.j2", Config, fname)


##---------------------------------------------------------------------------------------------------------------------

Action = sys.argv[1]
if len(sys.argv) > 2:
    Noun = sys.argv[2]
if Action == 'build':
    if Noun == 'host':
        build_host(sys.argv[3])
if Action == 'complete':
    if Noun == 'host':
        complete_host(sys.argv[3])
if Action == 'create':
    if Noun == 'host':
        create_host(sys.argv[3],sys.argv[4],sys.argv[5])
if Action == 'delete':
    if Noun == 'host':
        delete_host(sys.argv[3])
if Action == 'edit':
    if Noun == 'host':
        edit_host(sys.argv[3],sys.argv[4])
if Action == 'list':
    if Noun == 'hosts':
        list_hosts()
