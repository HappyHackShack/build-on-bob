from fastapi import APIRouter, HTTPException, Query
from sqlmodel import select
from typing import Annotated

from database import SessionDep
from library import (
    API_DELETE_Responses,
    API_GET_Responses,
    API_POST_Responses,
    get_Subnet_for_ip,
    run_ansible,
    wipe_vm_playbooks,
    write_vm_playbooks,
)
from models import Hypervisor, IPaddress, Subnet, Virtual

vm_router = APIRouter(prefix="/mm", tags=["Virtual Machines"])


@vm_router.post("/vm", status_code=201, responses=API_POST_Responses)
def create_virtual(virtual: Virtual, session: SessionDep) -> Virtual:
    if session.get(Virtual, virtual.name):
        raise HTTPException(status_code=409, detail="VM already exists")
    if not session.get(Hypervisor, virtual.hypervisor):
        raise HTTPException(status_code=406, detail="Unknown hypervisor")
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

    # All OK ...
    session.add(virtual)
    session.commit()
    session.refresh(virtual)
    write_vm_playbooks(virtual, session)
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
    wipe_vm_playbooks(virtual)
    session.delete(virtual)
    session.commit()
    return {"ok": True}


@vm_router.patch("/{vm_name}/build", responses=API_GET_Responses)
def build_virtual(vm_name: str, session: SessionDep) -> Virtual:
    vm = session.get(Virtual, vm_name)
    if not vm:
        raise HTTPException(status_code=404, detail="VM not found")
    #
    run_ansible(f"build-{vm_name}-vm.yaml")
    return vm


@vm_router.patch("/{vm_name}/remove", responses=API_GET_Responses)
def remove_virtual(vm_name: str, session: SessionDep) -> Virtual:
    vm = session.get(Virtual, vm_name)
    if not vm:
        raise HTTPException(status_code=404, detail="VM not found")
    #
    run_ansible(f"remove-{vm_name}-vm.yaml")
    return vm
