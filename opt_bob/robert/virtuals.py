from fastapi import APIRouter, HTTPException, Query
import random
from sqlmodel import select
from typing import Annotated

from database import SessionDep
from library import (
    API_DELETE_Responses,
    API_GET_Responses,
    API_POST_Responses,
    Config,
    get_Subnet_for_ip,
    run_ansible,
    run_event_scripts,
    wipe_vm_playbooks,
    write_vm_playbooks,
)
from models import Hypervisor, IPaddress, OsVersion, Subnet, Virtual

vm_router = APIRouter(prefix="/vm", tags=["Virtual Machines"])


@vm_router.post("", status_code=201, responses=API_POST_Responses)
def create_virtual(virtual: Virtual, session: SessionDep) -> Virtual:
    if session.get(Virtual, virtual.name):
        raise HTTPException(status_code=409, detail="VM already exists")
    hypervisor = session.get(Hypervisor, virtual.hypervisor)
    if not hypervisor:
        raise HTTPException(status_code=406, detail="Unknown hypervisor")

    # Sort the DNS Domain
    if "." in virtual.name:
        virtual.dns_domain = ".".join(virtual.name.split(".")[1:])
        virtual.name = virtual.name.split(".")[0]
    else:
        # Just use the default
        virtual.dns_domain = Config.dns_domain

    # Check OS-Ver PID (and convert)
    osver = session.exec(
        select(OsVersion).where(OsVersion.pve_id == virtual.osver_pid)
    ).one_or_none()
    if not osver:
        raise HTTPException(status_code=406, detail="Unknown OS_Version ID")

    # Now check the IP validity
    subnet = session.get(Subnet, virtual.ip)
    if subnet:
        # Check that this subnet has an IPAM
        if not subnet.ipam:
            raise HTTPException(
                status_code=406, detail="That subnet doesn't have an IPAM"
            )
        # Requested network address => attempt IPAM
        from ipam import ipam_allocate_ip

        suggested = ipam_allocate_ip(subnet.ipam, {"fqdn": virtual.name}, session)
        virtual.ip = suggested.ip
    else:
        Valid_Subnet = get_Subnet_for_ip(virtual.ip, session)
        if not Valid_Subnet:
            raise HTTPException(status_code=406, detail="No subnet found for that IP")
        # In a subnet, but is it under IPAM
        if session.get(IPaddress, virtual.ip):
            raise HTTPException(
                status_code=409, detail="That IP is within an IPAM controlled range"
            )

    # Check / Generate an ID for ProxMox VMs
    if hypervisor.type != "proxmox":
        # force zero, when it's not needed
        virtual.vmid = 0
    else:
        # if ID requested, then check it
        if virtual.vmid != 0:
            sql = select(Virtual).where(Virtual.vmid == virtual.vmid)
            if session.exec(sql).one_or_none():
                raise HTTPException(
                    status_code=409, detail="A VM with that ID already exists"
                )
        else:
            while True:
                vmid = random.randint(100000, 500000)
                sql = select(Virtual).where(Virtual.vmid == vmid)
                if not session.exec(sql).one_or_none():
                    virtual.vmid = vmid
                    break

    # All OK ...
    run_event_scripts(
        "virtual", "pre-add", [virtual.hypervisor, virtual.fqdn(), virtual.ip]
    )
    session.add(virtual)
    session.commit()
    session.refresh(virtual)
    write_vm_playbooks(virtual, session)
    run_event_scripts(
        "virtual", "post-add", [virtual.hypervisor, virtual.fqdn(), virtual.ip]
    )
    return virtual


@vm_router.get("")
def read_virtual_list(
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
) -> list[Virtual]:
    virtuals = session.exec(select(Virtual).offset(offset).limit(limit)).all()
    return virtuals


@vm_router.get("/{vm_name}", responses=API_GET_Responses)
def read_virtual(vm_name: str, session: SessionDep) -> Virtual:
    virtual = session.get(Virtual, vm_name)
    if not virtual:
        raise HTTPException(status_code=404, detail=" Virtual not found")
    return virtual


@vm_router.delete("/{vm_name}", responses=API_DELETE_Responses)
def delete_virtual(vm_name: str, session: SessionDep):
    virtual = session.get(Virtual, vm_name)
    if not virtual:
        raise HTTPException(status_code=404, detail=" Virtual not found")
    #
    run_event_scripts(
        "virtual", "pre-remove", [virtual.hypervisor, virtual.fqdn(), virtual.ip]
    )
    wipe_vm_playbooks(virtual)
    session.delete(virtual)
    session.commit()
    run_event_scripts(
        "virtual", "post-remove", [virtual.hypervisor, virtual.fqdn(), virtual.ip]
    )
    return {"ok": True}


@vm_router.patch("/{vm_name}/build", responses=API_GET_Responses)
def build_virtual(vm_name: str, session: SessionDep) -> Virtual:
    virtual = session.get(Virtual, vm_name)
    if not virtual:
        raise HTTPException(status_code=404, detail="VM not found")
    #
    run_event_scripts(
        "virtual", "pre-build", [virtual.hypervisor, virtual.fqdn(), virtual.ip]
    )
    run_ansible(f"build-{vm_name}-vm.yaml")
    run_event_scripts(
        "virtual", "post-build", [virtual.hypervisor, virtual.fqdn(), virtual.ip]
    )
    return virtual


@vm_router.patch("/{vm_name}/destroy", responses=API_GET_Responses)
def remove_virtual(vm_name: str, session: SessionDep) -> Virtual:
    virtual = session.get(Virtual, vm_name)
    if not virtual:
        raise HTTPException(status_code=404, detail="VM not found")
    #
    run_event_scripts(
        "virtual", "pre-destroy", [virtual.hypervisor, virtual.fqdn(), virtual.ip]
    )
    run_ansible(f"destroy-{vm_name}-vm.yaml")
    run_event_scripts(
        "virtual", "post-destroy", [virtual.hypervisor, virtual.fqdn(), virtual.ip]
    )
    return virtual
