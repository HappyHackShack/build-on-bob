
from jinja2 import Environment, FileSystemLoader
import netaddr
import yaml

from config import *


def load_hosts_yaml(Hostname=None, MAC=None):
    # Only need to define a global to write to it
    global Etc_Bob_Hosts
    
    with open(Hosts_File, 'rt') as ipf:
        Etc_Bob_Hosts = yaml.safe_load(ipf)
    Hosts = Etc_Bob_Hosts
    if Hostname or MAC:
        for host in Hosts:
            if (host['name'] == Hostname) or (host['mac'] == MAC):
                return (Hosts, host)
        return (Hosts, None)
    return (Hosts)


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


def validate_ip_addr(IP):
    try:
        dummy = netaddr.IPAddress(IP)
    except:
        raise ValueError(f"{RED}That is not a valid IP address{END}\n")


def validate_mac_addr(MAC):
    try:
        dummy = netaddr.EUI(MAC)
    except:
        raise ValueError(f"{RED}That is not a valid MAC address{END}\n")


def write_dnsmasq_hosts(Hosts):
    with open('/etc/dnsmasq.d/hosts.conf','wt') as dns:
        for host in Hosts:
            dns.write(f"dhcp-host={host['mac']},{host['ip']},{host['name']}\n")


def wipe_host_build_files(Host):
    for directory in [ Nginx_Build_Dir, Nginx_Ipxe_Dir]:
        for filename in os.listdir(directory):
            if Host['mac'] in filename:
                os.unlink(f"{directory}/{filename}")


def write_host_build_files(Host):
    wipe_host_build_files(Host)
    recipe = Recipes['local'] if Host['target'] == 'local' else Recipes[Host['os']]
    OS_ver = Config.get_os_version(Host['os'], Host['version'])
    for template in recipe['templates']:
        tpl_name = template['name']
        output = template['output'].replace('MAC', Host['mac'])
        print(f'{GRAY}Writing template {tpl_name} --> {output}{END}')
        render_template( tpl_name, Config|Host|OS_ver, f"{Nginx_Base_Dir}/{output}")
