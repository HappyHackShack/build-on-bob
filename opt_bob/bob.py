#!/bin/env python3

from jinja2 import Environment, FileSystemLoader
import os
from pprint import pprint
import sys
import yaml

Config_File = '/etc/bob/engine.yaml'
Hosts_File = '/etc/bob/hosts.yaml'
IPXE_Host_Dir = '/usr/share/nginx/html/ipxe'
My_dir = os.path.dirname(__file__)

print('Starting the BOB engine ...')
with open(Config_File,'rt') as cfg:
    Config = yaml.safe_load(cfg)
print(Config)

def create_host(params):
    mac_addr, ip_addr, hostname = params
    with open(Hosts_File, 'rt') as ipf:
        Hosts = yaml.safe_load(ipf)
    Hosts['hosts'].append({'mac':mac_addr, 'ip_addr':ip_addr, 'hostname':hostname, 'os':'alpine'})
    with open(Hosts_File, 'wt') as opf:
        yaml.dump(Hosts, opf)
    # Now re-write the dnsmasq data
    write_dnsmasq_hosts(Hosts)


def delete_host(params):
    hostname = params[0]
    with open(Hosts_File, 'rt') as ipf:
        Hosts = yaml.safe_load(ipf)
    for host in Hosts['hosts']:
        if host['hostname'] == hostname:
            Hosts['hosts'].remove(host)
    with open(Hosts_File, 'wt') as opf:
        yaml.dump(Hosts, opf)
    # Now re-write the dnsmasq data
    write_dnsmasq_hosts(Hosts)


def list_hosts():
    with open(Hosts_File, 'rt') as ipf:
        Hosts = yaml.safe_load(ipf)
    for host in Hosts['hosts']:
        print(host)
        write_host_ipxe_cfg(host)


def write_dnsmasq_hosts(Hosts):
    with open('/etc/dnsmasq.d/hosts.conf','wt') as dns:
        for host in Hosts['hosts']:
            dns.write(f"dhcp-host={host['mac']},{host['ip_addr']},{host['hostname']}\n")


def write_host_ipxe_cfg(Host):
    environment = Environment(loader=FileSystemLoader(My_dir))
    template = environment.get_template("alpine.ipxe.j2")
    rendered = template.render(Config)

    mac = Host['mac']
    fname = f"{IPXE_Host_Dir}/{mac}.cfg"
    with open(fname, 'wt') as cfg:
        cfg.write(rendered)
        cfg.write('\n')


##---------------------------------------------------------------------------------------------------------------------

Action = sys.argv[1]
if len(sys.argv) > 2:
    Noun = sys.argv[2]
if Action == 'create':
    if Noun == 'host':
        create_host(sys.argv[3:])
if Action == 'delete':
    if Noun == 'host':
        delete_host(sys.argv[3:])
if Action == 'list':
    if Noun == 'hosts':
        list_hosts()
