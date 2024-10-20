from flask import Flask, request

from config import *
from database import *
from library import *
from wendy import app

@app.route("/cli/host/add", methods=['POST'])
def cli_host_add():
    Host = HostClass()
    OS = request.args.get('os') if request.args.get('os') else 'rescue'
    Version = request.args.get('version') if request.args.get('version') else Config.get_os(OS)['versions'][0]['tag']
    try:
        Host.name = request.args.get('name').lower()
        Host.ip = request.args.get('ip')
        Host.mac = request.args.get('mac')
        Host.os = OS
        Host.version = Version
    except ValueError as ve:
        return str(ve)

    # Check IP address not already allocated
    Hosts.load()
    for hh in Hosts:
        if hh.ip == Host.ip:
            return f"{RED}FAILED to add{END}: IP address is already allocated to {WHITE}{hh.name}{END}\n"
    # All OK
    Hosts.append(Host)
    Hosts.save()
    # Now re-write the dnsmasq and host data
    Hosts.write_dnsmasq()
    write_host_build_files(Host)
    return f"{GREEN}New host '{WHITE}{Host.name}{GREEN}' added{END}\n"


@app.route("/cli/host/build", methods=['PATCH'])
def cli_host_build():
    Hostname = request.args.get('name').lower()
    New_OS = request.args.get('os')
    New_version = request.args.get('version')
    #
    if not Hostname:
        return f"{RED}Please specify a host to build{END}\n"
    Hosts.load()
    try:
        host = Hosts.find(Hostname)
        if New_OS:
            host.os = New_OS
            if New_version:
                host.version = New_version
            else:
                host.version = Config.get_os(New_OS)['versions'][0]
    except ValueError as ve:
        return str(ve)
    host.target = 'build'
    #
    Hosts.save()
    write_host_build_files(host)
    return f"{CYAN}Host '{Hostname}' set to BUILD mode{END}\n"


@app.route("/cli/host/complete", methods=['PATCH'])
def cli_host_compete():
    Hostname = request.args.get('name').lower()
    MAC = request.args.get('mac')
    if not Hostname and not MAC:
        return f"{RED}Please specify a host or MAC to complete{END}\n"
    Hosts.load()
    try:
        host = Hosts.find(Hostname, MAC)
    except ValueError as ve:
        return str(ve)
    host.target = 'local'
    Hosts.save()
    write_host_build_files(host)
    return f"{CYAN}Host '{MAC}' set to LOCAL boot mode{END}\n"


@app.route("/cli/host/delete", methods=['DELETE'])
def cli_host_delete():
    Hostname = request.args.get('name').lower()
    if not Hostname:
        return f"{RED}Please specify a host to delete{END}\n"
    Hosts.load()
    try:
        host = Hosts.find(Hostname)
    except ValueError as ve:
        return str(ve)
    Hosts.remove(host)
    wipe_host_build_files(host)
    Hosts.save()
    Hosts.write_dnsmasq()
    return f"{CYAN}Host '{Hostname}' deleted{END}\n"


@app.route("/cli/host/edit", methods=['PATCH'])
def cls_host_edit():
    Hostname = request.args.get('name').lower()
    if not Hostname:
        return f"{RED}Please specify a host to edit{END}\n"
    Hosts.load()
    try:
        host = Hosts.find(Hostname)
    except ValueError as ve:
        return str(ve)
    host0 = HostClass( host.as_dict() )

    try:
        if 'rename' in request.args:
            host.name = request.args.get('rename').lower()
        if 'ip' in request.args:
            host.ip = request.args.get('ip')
        if 'mac' in request.args:
            host.mac = request.args.get('mac').lower().replace('-',':')
        if 'os' in request.args:
            host.os = request.args.get('os')
            host.version = Config.get_os(host.os)['versions'][0]['tag']
        if 'version' in request.args:
            host.version = request.args.get('version')
        if 'disk' in request.args:
            host.disk = request.args.get('disk')
    except ValueError as ve:
        return str(ve)

    if host.as_dict() != host0.as_dict():
        # Make the change
        wipe_host_build_files(host0)
        Hosts.save()
        # Post processing
        if 'rename' in request.args or 'ip' in request.args or 'mac' in request.args:
            Hosts.write_dnsmasq()
        # Always write (local is handled)
        write_host_build_files(host)
        return f"{CYAN}Host '{Hostname}' changed{END}\n"
    else:
        return f"{YELLOW}WARNING: I don't know what to change{END}\n"


@app.route("/cli/host/list")
def cli_host_list():
    Hosts.load()
    if len(Hosts) == 0:
        return f"{YELLOW}You don't have any hosts yet{END}"
    else:
        stdout = [ f'{BG_GRAY}  Hostname        MAC               / IP              OS        Version          Disk        Build ?   {END}' ]
        for h in Hosts:
            bld = GRAY if h.target == 'local' else RED
            stdout.append(f"  {h.name:15} {BLUE}{h.mac} / {CYAN}{h.ip:15}{END} {h.os:9} {h.version:16} {h.disk:11} {bld}{h.target}{END}")
        return '\n'.join(stdout) + '\n'


@app.route("/cli/os/list")
def cli_os_list():
    stdout = ['I know about the following operating systems:']
    for os in Config.get_os_list():
        stdout.append(f"{CYAN}  {os}{END}")
        for version in Config.get_os(os)['versions']:
            stdout.append(f"{MAGENTA}      {version['tag']}{END}")
    return "\n".join(stdout) + '\n'


@app.route("/cli/recipe/list")
def cli_recipe_list():
    stdout = ['I know about the following recipes:']
    for recipe in Recipes:
        stdout.append(f"{CYAN}    {recipe}{END}")
    return "\n".join(stdout) + '\n'
