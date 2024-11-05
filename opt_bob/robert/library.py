import ansible_runner as Ansible
from fastapi import HTTPException
import ipaddress
from jinja2 import Environment, FileSystemLoader
import os
from pydantic import BaseModel
import shutil
from sqlmodel import select, Session
import yaml

from models import Host, Hypervisor, OpSys, OsTemplate, OsVersion, Subnet, Virtual


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


def render_template(Template_Filename, Config, Target_Filename, mode = 0o644):
    environment = Environment(loader=FileSystemLoader(Template_Dir))
    template = environment.get_template(Template_Filename)
    rendered = template.render(Config)

    with open(Target_Filename, "wt") as cfg:
        cfg.write(rendered)
        cfg.write("\n")
    # Then set the mode (perms)
    os.chmod(Target_Filename, mode)


def restart_dnsmasq():
    os.system("systemctl restart dnsmasq")

    
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


def get_Subnet_for_ip(ip, session: Session) -> Subnet:
    for sub in session.exec(select(Subnet)).all():
        if network_contains_ip(sub.net_cidr(), ip):
            return sub
    return None


def network_contains_ip(network_CIDR: str, ip_address: str) -> bool:
    ip_net = ipaddress.IPv4Network(f"{ip_address}/32")
    network = ipaddress.IPv4Network(network_CIDR)
    return network.overlaps(ip_net)


### ---------- Build Templates -----------------------------------------------------------


def wipe_host_build_files(host: Host):
    for directory in [Config.nginx_build_dir, Config.nginx_ipxe_dir]:
        for filename in os.listdir(directory):
            if host.mac in filename:
                if os.path.exists(f"{directory}/{filename}"):
                    os.unlink(f"{directory}/{filename}")


def write_Dnsmasq(session: Session):
    Hosts = session.exec(select(Host)).all()
    with open("/etc/dnsmasq.d/hosts.conf", "wt") as dns:
        for host in Hosts:
            dns.write(f"dhcp-host={host.mac},{host.ip},{host.name}\n")


def write_Build_Files(host: Host, session: Session):
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


### ---------- Op Systems -----------------------------------------------------------------


def get_os_join_versions(session: Session):
    os_versions = session.exec(
        select(OpSys, OsVersion).where(
            OpSys.name == OsVersion.os_name, OsVersion.pve_id != 0
        )
    ).all()
    # The join returns a list of tuples: (OpSys, OsVersion)
    return [a.dict() | b.dict() for a, b in os_versions]


### ---------- Hypervisor & VMs -----------------------------------------------------------


def wipe_vm_playbooks(VM: Virtual):
    for verb in ["build", "remove]"]:
        playbook = f"{Ansible_Dir}/{verb}-{VM.name}-vm.yaml"
        if os.path.exists(playbook):
            os.unlink(playbook)


def write_ansible_hypervisor(hypervisor: Hypervisor, os_versions):
    hv_type = hypervisor.type
    render_template(
        f"{hv_type}-host-vars.j2",
        hypervisor.dict(),
        f"{Ansible_Dir}/host_vars/{hypervisor.name}.yaml",
    )
    render_template(
        f"{hv_type}-prepare.j2",
        {"cfg": Config, "hv": hypervisor, "os_versions": os_versions},
        f"{Ansible_Dir}/prep-{hypervisor.name}-hypervisor.yaml",
    )


def write_ansible_inventory(session):
    hypers = session.exec(select(Hypervisor)).all()
    data = {"hypervisors": hypers}
    render_template("ans-inventory.j2", data, f"{Ansible_Dir}/inventory.yaml")


def write_vm_playbooks(vm: Virtual, session):
    hyper = session.get(Hypervisor, vm.hypervisor)
    # TODO - lookup subnet deets properly
    osver = session.exec(select(OsVersion).where(OsVersion.pve_id==vm.osver_pid)).one()
    extra = {"cidr": "24", "gateway": "172.16.0.254", "nameservers": ["172.16.0.254"], "net_iface": osver.net_iface, "cloud_image": osver.files}
    hv_type = hyper.type
    render_template(
        f"{hv_type}-build-vm.j2",
        vm.dict() | extra,
        f"{Ansible_Dir}/build-{vm.name}-vm.yaml",
    )
    render_template(
        f"{hv_type}-remove-vm.j2",
        hyper.dict() | vm.dict(),
        f"{Ansible_Dir}/remove-{vm.name}-vm.yaml",
    )
