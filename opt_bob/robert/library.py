import ansible_runner as Ansible
from fastapi import HTTPException
import ipaddress
from jinja2 import Environment, FileSystemLoader
import os
from pydantic import BaseModel
import shutil
from sqlmodel import select
import yaml

from models import Host, Hypervisor, OsTemplate, OsVersion, Subnet, Virtual


My_Dir = os.path.dirname(__file__)
Ansible_Dir = "/etc/ansible"
Template_Dir = f"{My_Dir}/../templates"

### ---------- Errors   -----------------------------------------------------------


class API_Error(BaseModel):
    detail: str


API_DELETE_Responses = {
    404: {"model": API_Error, "description": "Not Found"},
    406: {"model": API_Error, "description": "Not Acceptable"},
    409: {"model": API_Error, "description": "Conflicting Data"},
}

API_GET_Responses = {
    404: {"model": API_Error, "description": "Not Found"},
}

API_POST_Responses = {
    201: {"model": API_Error, "description": "Resource Created"},
    406: {"model": API_Error, "description": "Not Acceptable"},
    409: {"model": API_Error, "description": "Conflicting Data"},
    410: {"model": API_Error, "description": "Data Gone"},
}

### ---------- Configuration   -----------------------------------------------------------

Config_File = "/etc/bob/config.yaml"


class Configuration:
    Data = {}

    def __init__(self) -> None:
        with open(Config_File, "rt") as cfg:
            Configuration.Data = yaml.safe_load(cfg)

    def __call__(self) -> dict:
        return Configuration.Data

    def __getattribute__(self, name: str) -> str:
        if name in Configuration.Data:
            return Configuration.Data[name]
        else:
            return ""


Config = Configuration()


### ---------- General --------------------------------------------------------------------


def render_template(Template_Filename, Config, Target_Filename):
    environment = Environment(loader=FileSystemLoader(Template_Dir))
    template = environment.get_template(Template_Filename)
    rendered = template.render(Config)

    with open(Target_Filename, "wt") as cfg:
        cfg.write(rendered)
        cfg.write("\n")


def run_ansible(playbook):
    result = Ansible.interface.run(private_data_dir=Ansible_Dir, playbook=playbook)
    # print(result)
    # for ev in result.events:
    #     stdout = ev['stdout'][2:] if ev['stdout'][:2] == '\r\n' else ev['stdout']
    #     print('EV', ev['uuid'], stdout)

    # Clean up the Artifacts
    for ev in result.events:
        uuid = ev["uuid"]
        evPath = f"{Ansible_Dir}/artifacts/{uuid}"
        if os.path.exists(evPath):
            shutil.rmtree(evPath)
    # Check for Total Failure
    if not result.stats:
        raise HTTPException(status_code=500, detail="FAILED to run the playbook")
    # Check for task failures
    Stats = result.stats
    print(Stats)
    if Stats["failures"]:
        raise HTTPException(status_code=500, detail="There were some tasks failures")
    if not Stats["ok"]:
        raise HTTPException(status_code=500, detail="Hmm, no tasks were run")


### ---------- Networks --------------------------------------------------------------------


def get_Subnet_for_ip(ip, session) -> Subnet:
    for sub in session.exec(select(Subnet)).all():
        if network_contains_ip(sub.net_cidr(), ip):
            return sub
    return None


def network_contains_ip(network_CIDR: str, ip_address: str) -> bool:
    ip_net = ipaddress.IPv4Network(f"{ip_address}/32")
    network = ipaddress.IPv4Network(network_CIDR)
    return network.overlaps(ip_net)


### ---------- Build Templates -----------------------------------------------------------


def wipe_host_build_files(host):
    for directory in [Config.nginx_build_dir, Config.nginx_ipxe_dir]:
        for filename in os.listdir(directory):
            if host.mac in filename:
                if os.path.exists(f"{directory}/{filename}"):
                    os.unlink(f"{directory}/{filename}")


def write_Dnsmasq(session):
    Hosts = session.exec(select(Host)).all()
    with open("/etc/dnsmasq.d/hosts.conf", "wt") as dns:
        for host in Hosts:
            dns.write(f"dhcp-host={host.mac},{host.ip},{host.name}\n")


def write_Build_Files(host, session):
    wipe_host_build_files(host)
    Rname = "local" if host.target == "local" else host.os_name
    Templates = session.exec(
        select(OsTemplate).where(OsTemplate.os_name == Rname)
    ).all()
    OS_Ver = session.exec(
        select(OsVersion).where(
            OsVersion.os_name == host.os_name, OsVersion.os_version == host.os_version
        )
    ).one()
    for template in Templates:
        tpl_src = template.source
        output = template.output.replace("MAC", host.mac)
        print(f"Writing template {tpl_src} --> {output}")
        # cfg = host.dict() | OS_Ver.dict()
        render_template(
            tpl_src,
            Config() | host.dict() | OS_Ver.dict(),
            f"{Config.nginx_base_dir}/{output}",
        )


### ---------- Hypervisor & VMs -----------------------------------------------------------


def wipe_vm_playbooks(VM: Virtual):
    for verb in ["build", "remove]"]:
        playbook = f"{Ansible_Dir}/{verb}-{VM.name}-vm.yaml"
        if os.path.exists(playbook):
            os.unlink(playbook)


def write_ansible_hostvars(hypervisor: Hypervisor):
    render_template("proxmox-host-vars.j2", hypervisor.dict(), f"{Ansible_Dir}/host_vars/{hypervisor.name}.yaml")
    render_template("proxmox-mk-template.j2", hypervisor.dict(), f"{Ansible_Dir}/mk-{hypervisor.name}-r94-tpl.yaml")


def write_ansible_inventory(session):
    Hypers = session.exec(select(Hypervisor)).all()
    Data = {"Hypervisors": Hypers}
    render_template("ans-inventory.j2", Data, f"{Ansible_Dir}/inventory.yaml")


def write_vm_playbooks(VM: Virtual, session):
    Hyper = session.get(Hypervisor, VM.hypervisor)
    Extra = {"cidr": "24", "gateway": "172.16.0.254", "nameservers": ["172.16.0.254"]}
    render_template(
        "libvirt-build-vm.j2",
        VM.dict() | Extra,
        f"{Ansible_Dir}/build-{VM.name}-vm.yaml",
    )
    render_template(
        "libvirt-remove-vm.j2",
        Hyper.dict() | VM.dict(),
        f"{Ansible_Dir}/remove-{VM.name}-vm.yaml",
    )
