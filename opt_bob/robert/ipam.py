from fastapi import APIRouter, HTTPException, Query
import ipaddress
from sqlmodel import select
from typing import Annotated

from database import SessionDep
from library import (
    API_DELETE_Responses,
    API_GET_Responses,
    API_POST_Responses,
    Config,
    get_Subnet_for_ip,
)
from models import IPAM, IPaddress, Subnet

i_router = APIRouter(prefix="/ipam", tags=["IPAM"])


def create_ipam_range(ipam: IPAM, session: SessionDep):
    n = ipam.name
    ip_from = ipaddress.IPv4Address(ipam.ip_from)
    ip_to = ipaddress.IPv4Address(ipam.ip_to)
    IP_Range = range(int(ip_from), int(ip_to) + 1)
    # Check for overlap
    for ii in IP_Range:
        ip = ipaddress.IPv4Address(ii)
        if session.get(IPaddress, str(ip)):
            raise HTTPException(
                status_code=409, detail="New range overlaps an existing range"
            )
    # OK=> create IPs
    for ii in IP_Range:
        ip = ipaddress.IPv4Address(ii)
        ipaddr = IPaddress(ipam=n, ip=str(ip))
        session.add(ipaddr)
    session.commit()


def delete_ipam_range(ipam: IPAM, session: SessionDep):
    ip_from = ipaddress.IPv4Address(ipam.ip_from)
    ip_to = ipaddress.IPv4Address(ipam.ip_to)
    IP_Range = range(int(ip_from), int(ip_to) + 1)
    # Check for allocations
    for ii in IP_Range:
        ip = str(ipaddress.IPv4Address(ii))
        ipaddr = session.get(IPaddress, ip)
        if ipaddr.hostname:
            raise HTTPException(
                status_code=406, detail="Some IP allocations still exist"
            )
    # OK=> delete IPs
    for ii in IP_Range:
        ip = str(ipaddress.IPv4Address(ii))
        ipaddr = session.get(IPaddress, ip)
        session.delete(ipaddr)
    session.commit()


@i_router.post("", status_code=201, responses=API_POST_Responses)
def create_ipam(ipam: IPAM, session: SessionDep) -> IPAM:
    # Check if name exists
    if session.get(IPAM, ipam.name):
        raise HTTPException(
            status_code=409, detail="IPAM with that name already exists"
        )
    # Check we are in a Subnet
    Valid_From = get_Subnet_for_ip(ipam.ip_from, session)
    Valid_To = get_Subnet_for_ip(ipam.ip_to, session)
    if not Valid_From:
        raise HTTPException(
            status_code=406, detail="No subnet found that contains that range"
        )
    if Valid_From != Valid_To:
        raise HTTPException(
            status_code=406, detail="No subnet found that contains that range"
        )
    if Valid_From.ipam:
        raise HTTPException(
            status_code=409,
            detail=f"Subnet {Valid_From.net_cidr()} already has an IPAM",
        )

    # All OK => create IP-Range and IPAM
    create_ipam_range(ipam, session)
    Valid_From.ipam = ipam.name
    session.add(Valid_From)
    session.add(ipam)
    session.commit()
    session.refresh(ipam)
    return ipam


@i_router.get("")
def read_ipam_list(
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
) -> list[IPAM]:
    ipams = session.exec(select(IPAM).offset(offset).limit(limit)).all()
    return ipams


@i_router.get("/{ipam_name}", responses=API_GET_Responses)
def read_ipam(ipam_name: str, session: SessionDep) -> IPAM:
    ipam = session.get(IPAM, ipam_name)
    if not ipam:
        raise HTTPException(status_code=404, detail="IPAM not found")
    return ipam


@i_router.get("/{ipam_name}/allocations", responses=API_GET_Responses)
def read_ip_allocations(ipam_name: str, session: SessionDep) -> list[IPaddress]:
    ipam = session.get(IPAM, ipam_name)
    if not ipam:
        raise HTTPException(status_code=404, detail="IPAM not found")
    allocs = session.exec(select(IPaddress).where(IPaddress.ipam == ipam.name)).all()
    return allocs


@i_router.delete("/{ipam_name}", responses=API_DELETE_Responses)
def delete_ipam(ipam_name: str, session: SessionDep):
    ipam = session.get(IPAM, ipam_name)
    if not ipam:
        raise HTTPException(status_code=404, detail="IPAM not found")
    delete_ipam_range(ipam, session)
    for sub in session.exec(select(Subnet).where(Subnet.ipam == ipam.name)).all():
        sub.ipam = ""
        session.add(sub)
    session.delete(ipam)
    session.commit()
    return {"ok": True}


@i_router.post("/{ipam_name}/allocate", responses=API_POST_Responses)
def ipam_allocate_ip(ipam_name: str, data: dict, session: SessionDep) -> IPaddress:
    try:
        fqdn = data["fqdn"]
    except Exception:
        raise HTTPException(status_code=422, detail="FQDN not specified in request")
    free_IPs = session.exec(
        select(IPaddress).where(IPaddress.ipam == ipam_name, IPaddress.hostname is None)
    ).all()
    if len(free_IPs) == 0:
        raise HTTPException(status_code=410, detail="No free IPs left")
    ipaddr = free_IPs[0]
    if "." in fqdn:
        hn = fqdn.split(".")[0]
        dom = ".".join(fqdn.split(".")[1:])
    else:
        hn = fqdn
        dom = Config.dns_domain
    print(f"Allocating {ipaddr.ip} -> {hn} . {dom}")
    ipaddr.hostname = hn
    ipaddr.domain = dom
    session.add(ipaddr)
    session.commit()
    session.refresh(ipaddr)
    return ipaddr


@i_router.delete("/{ip_address}/deallocate", responses=API_DELETE_Responses)
def delete_ip_alloaction(ip_address: str, session: SessionDep):
    ipaddr = session.get(IPaddress, ip_address)
    if not ipaddr:
        raise HTTPException(status_code=404, detail="IP Address not found")
    if not ipaddr.hostname:
        raise HTTPException(status_code=409, detail="IP Address not alloacted")
    ipaddr.hostname = None
    ipaddr.domain = None
    session.add(ipaddr)
    session.commit()
    return {"ok": True}
