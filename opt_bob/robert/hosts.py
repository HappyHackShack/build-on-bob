from fastapi import HTTPException, Query
from sqlmodel import select
from typing import Annotated
import yaml

from database import SessionDep
from library import *
from main import app
from models import *

@app.post("/host")
def create_host(host: Host, session: SessionDep) -> Host:
    """Create a new Host\n
    Example text"""
    # Validations
    if session.get(Host, host.name):
        raise HTTPException(status_code=422, detail="Host already exists")
    sql = select(Host).where(Host.ip==host.ip)
    if session.exec(sql).one_or_none():
        raise HTTPException(status_code=422, detail="IP already in use")
    sql = select(Host).where(Host.mac==host.mac)
    if session.exec(sql).one_or_none():
        raise HTTPException(status_code=422, detail="MAC already in use")
    # IP in a subnet
    # TODO
    # Which subnet / Node

    # OK
    session.add(host)
    session.commit()
    session.refresh(host)
    #
    write_Dnsmasq(session)
    write_Build_Files(host,session)
    return host


@app.get("/host")
def read_list_of_hosts(session: SessionDep, offset: int = 0,
           limit: Annotated[int, Query(le=100)] = 100, ) -> list[Host]:
    """Get a list of Hosts"""
    hosts = session.exec(select(Host).offset(offset).limit(limit)).all()
    return hosts


@app.get("/host/{host_name}")
def read_a_host(host_name: str, session: SessionDep) -> Host:
    host = session.get(Host, host_name)
    if not host:
        raise HTTPException(status_code=404, detail="Host not found")
    return host


@app.patch("/host/{host_name}")
def update_host(host_name: str, Patch:Host, session: SessionDep):
    host = session.get(Host, host_name)
    if not host:
        raise HTTPException(status_code=404, detail="Host not found")
    
    if Patch.name:
        host.name = Patch.name
    if Patch.ip:
        host.ip = Patch.ip
    if Patch.mac:
        host.mac = Patch.mac
    # TODO
    if Patch.os_name:
        host.os_name = Patch.os_name
    if Patch.os_version:
        host.os_version = Patch.os_version
    if Patch.disk:
        host.disk = Patch.disk
    #
    session.add(host)
    session.commit()
    session.refresh(host)
    return host


@app.delete("/host/{host_name}")
def delete_host(host_name: str, session: SessionDep):
    host = session.get(Host, host_name)
    if not host:
        raise HTTPException(status_code=404, detail="Host not found")
    session.delete(host)
    session.commit()
    return {"ok": True}


@app.patch("/host/{host_name}/build")
def build_host(Params:dict, host_name: str, session: SessionDep) -> Host:
    host = session.get(Host, host_name)
    if not host:
        raise HTTPException(status_code=404, detail="Host not found")
    host.target = 'build'
    # TODO
    if 'os_name' in Params:
        host.os_name = Params['os_name']
        if 'os_version' in Params:
            host.os_version = Params['os_version']
        else:  # Just get the first known
            Version0 = session.exec(select(OsVersion).where(OsVersion.os_name==host.os_name)).first()
            host.os_version = Version0.os_version
    session.add(host)
    session.commit()
    session.refresh(host)
    #
    write_Dnsmasq(session)
    write_Build_Files(host, session)
    return host


@app.get("/host/{host_name}/complete")
def complete_host(host_name: str, session: SessionDep) -> Host:
    host = session.get(Host, host_name)
    if not host:
        raise HTTPException(status_code=404, detail="Host not found")
    host.target = 'local'
    session.add(host)
    session.commit()
    session.refresh(host)
    write_Build_Files(host, session)
    return host
