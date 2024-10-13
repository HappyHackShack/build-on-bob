from flask import Flask, request

from config import *
from library import *
from wendy import app

@app.route("/cli/host/add", methods=['POST'])
def cli_host_add():
    Hostname = request.args.get('name').lower()
    IP = request.args.get('ip')
    MAC = request.args.get('mac')
    OS = request.args.get('os')
    Version = request.args.get('version')
    if not Hostname:
        return f"{RED}Please specify a host to add{END}\n"
    try:
        validate_ip_addr(IP)
        validate_mac_addr(MAC)
    except ValueError as ve:
        return str(ve)

    Hosts = load_hosts_yaml()
    print('H:', Hosts)
    if not OS:
        OS = 'rescue'
    if OS not in Config.get_os_list():
        return f"{RED}That's not a valid OS...{END}\n"
    if not Version:
        Version = Config.get_os(OS)['versions'][0]['tag']
    if not Config.get_os_version(OS,Version):
        return f"{RED}That's not a valid version for {OS} ...{END}\n"
    # Check IP address not already allocated
    for host in Hosts:
        if IP == host['ip']:
            return f"{RED}FAILED to add{END}: IP address is already allocated to {WHITE}{host['name']}{END}\n"
    # All OK
    new_host = {'mac':MAC.lower(), 'ip':IP, 'name':Hostname, 'os':OS, 'version':Version, 'disk':'/dev/sda', 'target':'local'}
    Hosts.append(new_host)
    save_hosts_yaml()
    # Now re-write the dnsmasq and host data
    write_dnsmasq_hosts(Hosts)
    write_host_build_files(new_host)
    return f"{GREEN}New host '{WHITE}{Hostname}{GREEN}' added{END}\n"


@app.route("/cli/host/build", methods=['PATCH'])
def cli_host_build():
    Hostname = request.args.get('name').lower()
    New_OS = request.args.get('os')
    New_version = request.args.get('version')
    #
    if not Hostname:
        return f"{RED}Please specify a host to build{END}\n"
    Hosts, host = load_hosts_yaml(Hostname)
    if not host:
        return f"{YELLOW}WARNING: I didn't recognize that hostname{END}\n"
    if New_OS:
        if New_OS not in Config.get_os_list():
            return f"{RED}That's not a valid OS...{END}\n"
        if New_version:
            version = Config.get_os_version(New_OS, New_version)
            if not version:
                return f"{RED}That's not a valid version for {New_OS} ...{END}\n"
        else:
            version = Config.get_os(New_OS)['versions'][0]
        host['os'] = New_OS
        host['version'] = version['tag']
    host['target'] = 'build'
    #
    save_hosts_yaml()
    write_host_build_files(host)
    return f"{CYAN}Host '{Hostname}' set to BUILD mode{END}\n"


@app.route("/cli/host/complete", methods=['PATCH'])
def cli_host_compete():
    Hostname = request.args.get('name').lower()
    MAC = request.args.get('mac')
    if not Hostname and not MAC:
        return f"{RED}Please specify a host or MAC to complete{END}\n"
    Hosts, host = load_hosts_yaml(Hostname, MAC)
    if not host:
        return f"{YELLOW}WARNING: I didn't recognize that hostname{END}\n"
    host['target'] = 'local'
    save_hosts_yaml()
    write_host_build_files(host)
    return f"{CYAN}Host '{MAC}' set to LOCAL boot mode{END}\n"


@app.route("/cli/host/delete", methods=['DELETE'])
def cli_host_delete():
    Hostname = request.args.get('name').lower()
    if not Hostname:
        return f"{RED}Please specify a host to delete{END}\n"
    Hosts, host = load_hosts_yaml(Hostname)
    if not host:
        return f"{YELLOW}WARNING: I didn't recognize that hostname{END}\n"
    Hosts.remove(host)
    wipe_host_build_files(host)
    write_dnsmasq_hosts(Hosts)
    save_hosts_yaml()
    return f"{CYAN}Host '{Hostname}' deleted{END}\n"


@app.route("/cli/host/edit", methods=['PATCH'])
def cls_host_edit():
    Hostname = request.args.get('name').lower()
    if not Hostname:
        return f"{RED}Please specify a host to edit{END}\n"
    Hosts, host = load_hosts_yaml(Hostname)
    if not host:
        return f"{YELLOW}WARNING: I didn't recognize that hostname{END}\n"
    host0 = host.copy()

    changed = False
    if 'rename' in request.args:
        Value = request.args.get('rename').lower()
        host['name'] = Value
    if 'ip' in request.args:
        Value = request.args.get('ip')
        try:
            validate_ip_addr(Value)
        except ValueError as ve:
            return str(ve)
        host['ip'] = Value
    if 'mac' in request.args:
        Value = request.args.get('mac').lower().replace('-',':')
        try:
            validate_mac_addr(Value)
        except ValueError as ve:
            return str(ve)
        host['mac'] = Value
    if 'os' in request.args:
        Value = request.args.get('os')
        if Value not in Config.get_os_list():
            return f"{RED}That's not a valid OS...{END}\n"
        host['os'] = Value
        host['version'] = Config.get_os(Value)['versions'][0]['tag']
    if 'version' in request.args:
        Value = request.args.get('version')
        if not Config.get_os_version(host['os'],Value):
            return f"{RED}That's not a valid version for {host['os']} ...{END}\n"
        host['version'] = Value
    if 'disk' in request.args:
        Value = request.args.get('disk')
        host['disk'] = Value

    if host != host0:
        # Make the change
        wipe_host_build_files(host0)
        save_hosts_yaml()
        # Post processing
        if 'rename' in request.args or 'ip' in request.args or 'mac' in request.args:
            write_dnsmasq_hosts(Hosts)
        # Always write (local is handled)
        write_host_build_files(host)
        return f"{CYAN}Host '{Hostname}' changed{END}\n"
    else:
        return f"{YELLOW}WARNING: I don't know what to change{END}\n"


@app.route("/cli/host/list")
def cli_host_list():
    Hosts = load_hosts_yaml()
    if len(Hosts) == 0:
        return f"{YELLOW}You don't have any hosts yet{END}"
    else:
        stdout = [ f'{BG_GRAY}  Hostname        MAC               / IP              OS        Version          Disk        Build ?   {END}' ]
        for h in Hosts:
            bld = GRAY if h['target'] == 'local' else RED
            stdout.append(f"  {h['name']:15} {BLUE}{h['mac']} / {CYAN}{h['ip']:15}{END} {h['os']:9} {h['version']:16} {h['disk']:11} {bld}{h['target']}{END}")
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
