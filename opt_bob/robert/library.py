import ansible_runner as Ansible
from ansible_runner.utils import cleanup_artifact_dir
from fastapi import HTTPException
import ipaddress
from jinja2 import Environment, FileSystemLoader
import os
from pprint import pprint
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


def render_template(Template_Filename, Config, Target_Filename, mode=0o644):
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
    Stats = result.stats

    # Check the event results
    task_errors = []
    for event in result.events:
        # print("EV", event["uuid"], event["event"])
        if "failed" in event["event"]:
            ev_data = event["event_data"]
            # print("FAIL ", end="")
            # pprint(event)
            task_errors.append(ev_data["res"]["msg"])

    # Finally; clean-up artefacts
    cleanup_artifact_dir(f"{Ansible_Dir}/artifacts", 1)

    # Check for Total Failure
    if not Stats:
        raise HTTPException(status_code=500, detail="FAILED to run the playbook")

    # Check for task failures
    print(Stats)
    if Stats["failures"]:
        raise HTTPException(
            status_code=500,
            detail="There were some tasks failures:\n" + "\n".join(task_errors),
        )
    if not Stats["ok"]:
        raise HTTPException(status_code=500, detail="Hmm, no tasks were run")


def run_event_scripts(object: str, event: str, parameters: list[str]):
    script_dir = f"{Config.bob_home_directory}/events/{object}/{event}"
    print(f"Checking for {object}->{event} in {script_dir}")
    files = os.listdir(script_dir)
    for ff in files:
        f_path = f"{script_dir}/{ff}"
        f_stat = os.stat(f_path)
        if f_stat.st_size == 0:
            print(f"Quietly ignoring {ff}")
            continue
        # Check if ANY executable bit is set
        if f_stat.st_mode & 0o111 == 0:
            print(f"Found {ff}, but it's not executable")
            continue
        else:
            print(f"Executing {ff} ...")
            os.system(f"{f_path} " + " ".join(parameters))


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


def write_host_build_files(host: Host, session: Session):
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
    # TODO - lookup the subnet
    subnet = {"cidr": "24", "gateway": "172.16.0.254", "nameservers": "172.16.0.254"}
    for template in Templates:
        tpl_src = template.source
        output = template.output.replace("MAC", host.mac)
        print(f"Writing template {tpl_src} --> {output}")
        # cfg = host.dict() | OS_Ver.dict()
        render_template(
            tpl_src,
            Config() | subnet | host.dict() | OS_Ver.dict(),
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
    for verb in ["build", "remove"]:
        playbook = f"{Ansible_Dir}/{verb}-{VM.name}-vm.yaml"
        print("RM ", playbook)
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
    osver = session.exec(
        select(OsVersion).where(OsVersion.pve_id == vm.osver_pid)
    ).one()
    extra = {
        "pve_storage": hyper.pve_storage,
        "cidr": "24",
        "sn_gateway": "172.16.0.254",
        "sn_nameservers": ["172.16.0.254"],
        "net_iface": osver.net_iface,
        "cloud_image": osver.files,
        "cloud_user": Config.builder_user,
        "cloud_pass": "RockyP@ss",
        "cloud_ssh_keys": [Config.builder_ssh_key],
    }
    hv_type = hyper.type
    render_template(
        f"{hv_type}-build-vm.j2",
        vm.dict() | extra,
        f"{Ansible_Dir}/build-{vm.name}-vm.yaml",
    )
    render_template(
        f"{hv_type}-destroy-vm.j2",
        hyper.dict() | vm.dict(),
        f"{Ansible_Dir}/destroy-{vm.name}-vm.yaml",
    )
