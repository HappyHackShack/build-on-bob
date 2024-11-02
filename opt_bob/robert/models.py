from enum import Enum
import netaddr
from pydantic import field_validator, AfterValidator, ConfigDict
from sqlmodel import Field, SQLModel
from typing import Annotated, Optional


def coerce_to_lower(n: str) -> str:
    return n.lower()


def validate_hv_type(hv_type: str) -> str:
    if hv_type not in ("libvirt", "proxmox"):
        raise ValueError("invalid hypervisor type")
    return hv_type


def validate_ip(ip: str) -> str:
    try:
        netaddr.IPAddress(ip)
    except Exception:
        raise ValueError("invalid IP address")
    return ip


class HypervisorType(str, Enum):
    libvirt = "libvirt"
    proxmox = "proxmox"


class HostModel(SQLModel):
    model_config = ConfigDict(validate_assignment=True)
    #
    name: Annotated[str, AfterValidator(coerce_to_lower)] = Field(primary_key=True)
    ip: Annotated[str, AfterValidator(validate_ip)]
    mac: str
    os_name: Optional[str] = Field(default="rescue")
    os_version: Optional[str] = Field(default="v3.20")
    disk: Optional[str] = Field(default="/dev/sda")
    target: Optional[str] = Field(default="local")

    @field_validator("mac")
    @classmethod
    def validate_mac(cls, mac):
        try:
            netaddr.EUI(mac)
        except Exception:
            raise ValueError("invalid MAC address")
        return mac


class Host(HostModel, table=True):
    pass


class HypervisorModel(SQLModel):
    model_config = ConfigDict(validate_assignment=True)
    #
    name: str = Field(primary_key=True)
    type: Annotated[str, AfterValidator(validate_hv_type)]
    ssh_user: Optional[str] = Field(default="rocky")
    ssh_key_file: Optional[str] = Field(default="~/.ssh/rocky")
    api_user: Optional[str] = Field(default="root@pam")
    api_token: Optional[str] = Field(default="bob")
    api_secret: Optional[str] = Field(default="")
    bridge_name: Optional[str] = Field(default="bridge0")
    cloud_image: Optional[str] = Field(
        default="Rocky-9-GenericCloud-Base-9.4-20240609.1.x86_64.qcow2"
    )
    lv_config_dir: Optional[str] = Field(default="/var/lib/libvirt/cloud")
    lv_image_dir: Optional[str] = Field(default="/var/lib/libvirt/images")


class Hypervisor(HypervisorModel, table=True):
    pass


class IpamModel(SQLModel):
    model_config = ConfigDict(validate_assignment=True)
    #
    name: str = Field(primary_key=True)
    ip_from: Annotated[str, AfterValidator(validate_ip)]
    ip_to: Annotated[str, AfterValidator(validate_ip)]
    backend: str = Field(default="internal")


class IPAM(IpamModel, table=True):
    pass


class IPaddress(SQLModel, table=True):
    ipam: str
    ip: str = Field(primary_key=True)
    hostname: Optional[str] = Field(default=None)
    domain: Optional[str] = Field(default=None)


class Node(SQLModel, table=True):
    name: str = Field(primary_key=True)
    secret: Optional[str] = Field(default=None)


class OpSys(SQLModel, table=True):
    name: str = Field(primary_key=True)
    base_url: str


class OsTemplate(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    os_name: str
    source: str
    output: str


class OsVersion(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    os_name: str
    os_version: str
    url: str
    files: str


class Subnet(SQLModel, table=True):
    network: str = Field(primary_key=True)
    cidr: int
    gateway: str
    nameservers: Optional[str] = Field(default="")
    ipam: Optional[str] = Field(default="")
    node: Optional[str] = Field(default="localhost")

    def net_cidr(self) -> str:
        return f"{self.network}/{self.cidr}"


class VirtualModel(SQLModel):
    model_config = ConfigDict(validate_assignment=True)
    #
    name: Annotated[str, AfterValidator(coerce_to_lower)] = Field(primary_key=True)
    vmid: Optional[int] = Field(default=0)
    hypervisor: str
    ip: Annotated[str, AfterValidator(validate_ip)]
    cpu_cores: Optional[int] = Field(default=4)
    memory_mb: Optional[int] = Field(default=4096)
    disk_gb: Optional[int] = Field(default=25)


class Virtual(VirtualModel, table=True):
    pass
