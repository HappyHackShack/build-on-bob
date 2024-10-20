import netaddr
from pydantic import field_validator, AfterValidator, ConfigDict
from sqlmodel import Field, SQLModel
from typing import Annotated

from database import get_session


def coerce_to_lower(n: str) -> str:
    return n.lower()


class HostModel(SQLModel):
    model_config = ConfigDict(validate_assignment=True)
    name: Annotated[str, AfterValidator(coerce_to_lower)] = Field(primary_key=True)
    ip: str
    mac: str
    os_name: str | None = Field(default='rescue')
    os_version: str | None = Field(default='v3.20')
    disk: str | None = Field(default='/dev/sda')
    target: str | None = Field(default='local')

    @field_validator('ip')
    @classmethod
    def validate_ip(cls, ip) :
        try:
            netaddr.IPAddress(ip)
        except:
            raise ValueError('invalid IP address')
        return ip

    @field_validator('mac')
    @classmethod
    def validate_mac(cls, mac) :
        try:
            netaddr.EUI(mac)
        except:
            raise ValueError('invalid MAC address')
        return mac


class Host(HostModel, table=True):
    pass


class IPAM(SQLModel, table=True):
    name: str = Field(primary_key=True)
    ip_from: str
    ip_to: str


class Node(SQLModel, table=True):
    name: str = Field(primary_key=True)
    secret: str | None = Field(default=None)


class OpSys(SQLModel, table=True):
    name: str = Field(primary_key=True)
    base_url: str


class OsTemplate(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    os_name: str
    source: str
    output: str


class OsVersion(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    os_name: str
    os_version: str
    url: str
    files: str


class Subnet(SQLModel, table=True):
    network: str = Field(primary_key=True)
    cidr: int
    gateway: str
    nameservers: str | None
    node: str
