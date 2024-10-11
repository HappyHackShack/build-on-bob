#!/bin/env python3

from flask import Flask, redirect, render_template
import os
import yaml

app = Flask('wendy')

Context = { }
Etc_Bob_Hosts = {}
Config_File = '/etc/bob/engine.yaml'
Hosts_File = '/etc/bob/hosts.yaml'


class Bob_Config(dict):
    def get_os(self, osName):
        for os in self['os_cache']:
            if os['name'] == osName:
                return os
        return None
    
    def get_os_list(self):
        return [ os['name'] for os in self['os_cache'] ]

    def get_os_version(self, osName, verTag):
        for os in self['os_cache']:
            if os['name'] == osName:
                for version in os['versions']:
                    if version['tag'] == verTag:
                        return version
        return None


with open(Config_File,'rt') as cfg:
    Config = Bob_Config( yaml.safe_load(cfg) )


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


###------------------------------------------------------------------------------------------------
def list_hosts():
    Hosts = load_hosts_yaml()
    if len(Hosts) == 0:
        print(f"{YELLOW}You don't have any hosts yet{END}")
    else:
        print(f'{BG_GRAY}  Hostname        MAC               / IP              OS        Version          Disk        Build ?   {END}')
        for h in Hosts:
            bld = GRAY if h['target'] == 'local' else RED
            print(f"  {h['hostname']:15} {BLUE}{h['mac']} / {CYAN}{h['ip_addr']:15}{END} {h['os']:9} {h['version']:16} {h['disk']:11} {bld}{h['target']}{END}")




@app.route("/")
def hello_world():
    Context['page_title'] = 'Home'
    return render_template('home.htm', ctx = Context)


@app.route("/ping")
def ping_pong():
    return "pong\n"


@app.route("/api/complete/<mac>")
def complete_host(mac):
    os.system(f'/usr/local/sbin/bob complete {mac}')
    return "OK"


@app.route("/hosts")
def hosts_idx():
    Context['page_title'] = 'Hosts'
    Context['hosts'] = load_hosts_yaml()
    return render_template('hosts.htm', ctx = Context)


@app.route("/ipam")
def ipam_idx():
    Context['page_title'] = 'IPAM'
    return render_template('ipam.htm', ctx = Context)


@app.route("/nodes")
def nodes_idx():
    Context['page_title'] = 'Nodes'
    return render_template('nodes.htm', ctx = Context)


@app.route("/os")
def os_idx():
    Context['page_title'] = 'OS'
    Context['opsystems'] = Config['os_cache']

    return render_template('os.htm', ctx = Context)


@app.route("/subnets")
def subnets_idx():
    Context['page_title'] = 'Subnets'
    return render_template('subnets.htm', ctx = Context)


