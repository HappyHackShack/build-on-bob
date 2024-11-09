# from dataclasses import dataclass
from jinja2 import Environment, FileSystemLoader
import netaddr
import yaml

from config import *


class HostClass:
    def __init__(self, Data=None):
        if Data:
            self._Name = Data["name"]
            self._IP = Data["ip"]
            self._MAC = Data["mac"]
            self._OS = Data["os"]
            self._Version = Data["version"]
            self._Disk = Data["disk"]
            self._Target = Data["target"]
        else:
            self._Name = None
            self._IP = None
            self._MAC = None
            self._OS = None
            self._Version = None
            self._Disk = "/dev/sda"
            self._Target = "local"

    @property
    def name(self):
        return self._Name

    @property
    def ip(self):
        return self._IP

    @property
    def mac(self):
        return self._MAC

    @property
    def os(self):
        return self._OS

    @property
    def version(self):
        return self._Version

    @property
    def disk(self):
        return self._Disk

    @property
    def target(self):
        return self._Target

    @name.setter
    def name(self, name):
        if not name:
            raise ValueError(f"{RED}Please specify a host to add{END}\n")
        self._Name = name

    @ip.setter
    def ip(self, ip):
        try:
            dummy = netaddr.IPAddress(ip)
        except:
            raise ValueError(f"{RED}That is not a valid IP address{END}\n")
        self._IP = ip

    @mac.setter
    def mac(self, mac):
        try:
            dummy = netaddr.EUI(mac)
        except:
            raise ValueError(f"{RED}That is not a valid MAC address{END}\n")
        self._MAC = mac

    @os.setter
    def os(self, os):
        if os not in Config.get_os_list():
            raise ValueError(f"{RED}That's not a valid OS...{END}\n")
        self._OS = os

    @version.setter
    def version(self, version):
        if not Config.get_os_version(self._OS, version):
            raise ValueError(
                f"{RED}That's not a valid version for {self._OS} ...{END}\n"
            )
        self._Version = version

    @disk.setter
    def disk(self, disk):
        self._Disk = disk

    @target.setter
    def target(self, target):
        self._Target = target

    def as_dict(self):
        return {
            "name": self._Name,
            "ip": self._IP,
            "mac": self._MAC,
            "os": self._OS,
            "version": self._Version,
            "disk": self._Disk,
            "target": self._Target,
        }


class HostsList:
    def __init__(self):
        self.__Data = None
        self.__Hosts = []

    # def __call__(self):
    #     return self.__Hosts

    def __iter__(self):
        self.index = -1
        return self

    def __len__(self):
        return len(self.__Hosts)

    def __next__(self):
        self.index = self.index + 1
        if self.index >= len(self.__Hosts):
            raise StopIteration
        return self.__Hosts[self.index]

    def append(self, host):
        self.__Hosts.append(host)

    def find(self, Hostname=None, MAC=None):
        for host in self.__Hosts:
            if (host.name == Hostname) or (host.mac == MAC):
                return host
        raise ValueError(f"{RED}That host was NOT Found{END}\n")

    def load(self, Hostname=None, MAC=None):
        with open(Hosts_File, "rt") as ipf:
            self.__Data = yaml.safe_load(ipf)
        self.__Hosts = [HostClass(h) for h in self.__Data]

    def remove(self, host):
        self.__Hosts.remove(host)

    def save(self):
        self.__Data = [h.as_dict() for h in self.__Hosts]
        with open(Hosts_File, "wt") as opf:
            yaml.dump(self.__Data, opf)

    def write_dnsmasq(self):
        with open("/etc/dnsmasq.d/hosts.conf", "wt") as dns:
            for host in self.__Hosts:
                dns.write(f"dhcp-host={host.mac},{host.ip},{host.name}\n")


def render_template(Template_Filename, Config, Target_Filename):
    environment = Environment(loader=FileSystemLoader(Template_Dir))
    template = environment.get_template(Template_Filename)
    rendered = template.render(Config)

    with open(Target_Filename, "wt") as cfg:
        cfg.write(rendered)
        cfg.write("\n")


def wipe_host_build_files(Host):
    for directory in [Nginx_Build_Dir, Nginx_Ipxe_Dir]:
        for filename in os.listdir(directory):
            if Host.mac in filename:
                os.unlink(f"{directory}/{filename}")


def write_host_build_files(Host):
    wipe_host_build_files(Host)
    recipe = Recipes["local"] if Host.target == "local" else Recipes[Host.os]
    OS_ver = Config.get_os_version(Host.os, Host.version)
    print(OS_ver)
    for template in recipe["templates"]:
        tpl_name = template["name"]
        output = template["output"].replace("MAC", Host.mac)
        print(f"{GRAY}Writing template {tpl_name} --> {output}{END}")
        h = Host.as_dict()
        render_template(tpl_name, Config | h | OS_ver, f"{Nginx_Base_Dir}/{output}")


# Create the class for everyone
Hosts = HostsList()
