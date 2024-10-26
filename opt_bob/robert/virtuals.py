from fastapi import HTTPException, Query
from sqlmodel import select
from typing import Annotated

from database import SessionDep
from library import *
from main import app
from models import *


@app.post("/vm")
def create_virtual(virtual:  Virtual, session: SessionDep) ->  Virtual:
    if session.get(Virtual, virtual.name):
        raise HTTPException(status_code=422, detail="VM already exists")
    if not session.get(Hypervisor, virtual.hypervisor):
        raise HTTPException(status_code=422, detail="Unknown hypervisor")
    session.add(virtual)
    session.commit()
    session.refresh(virtual)
    write_vm_playbooks(virtual, session)
    return virtual


@app.get("/vm")
def read_virtual_list(session: SessionDep, offset: int = 0,
           limit: Annotated[int, Query(le=100)] = 100, ) -> list[ Virtual]:
    virtuals = session.exec(select(Virtual).offset(offset).limit(limit)).all()
    return virtuals


@app.get("/vm/{vm_name}")
def read_virtual(vm_name: str, session: SessionDep) ->  Virtual:
    virtual = session.get( Virtual, vm_name)
    if not virtual:
        raise HTTPException(status_code=404, detail=" Virtual not found")
    return virtual


@app.delete("/vm/{vm_name}")
def delete_virtual(vm_name: str, session: SessionDep):
    virtual = session.get( Virtual, vm_name)
    if not virtual:
        raise HTTPException(status_code=404, detail=" Virtual not found")
    wipe_vm_playbooks(virtual)
    session.delete(virtual)
    session.commit()
    return {"ok": True}


@app.patch("/vm/{vm_name}/build")
def build_virtual(vm_name: str, session: SessionDep) -> Virtual:
    vm = session.get(Virtual, vm_name)
    if not vm:
        raise HTTPException(status_code=404, detail="VM not found")
    #
    run_ansible(f'build-{vm_name}-vm.yaml')
    return vm


@app.patch("/vm/{vm_name}/remove")
def build_virtual(vm_name: str, session: SessionDep) -> Virtual:
    vm = session.get(Virtual, vm_name)
    if not vm:
        raise HTTPException(status_code=404, detail="VM not found")
    #
    run_ansible(f'remove-{vm_name}-vm.yaml')
    return vm
