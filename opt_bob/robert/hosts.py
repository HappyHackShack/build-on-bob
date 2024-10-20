from fastapi import HTTPException, Query
from jinja2 import Environment, FileSystemLoader
import os
from sqlmodel import select
from typing import Annotated
import yaml

from database import SessionDep
from main import app
from models import *

Config_File = '/etc/bob/config.yaml'
with open(Config_File,'rt') as cfg:
    Config = yaml.safe_load(cfg)

My_Dir = os.path.dirname(__file__)
Nginx_Base_Dir = '/usr/share/nginx/html'
Nginx_Ipxe_Dir = f'{Nginx_Base_Dir}/ipxe'
Nginx_Build_Dir = f'{Nginx_Base_Dir}/build'
Template_Dir = f"{My_Dir}/../templates"


def render_template(Template_Filename, Config, Target_Filename):
    environment = Environment(loader=FileSystemLoader(Template_Dir))
    template = environment.get_template(Template_Filename)
    rendered = template.render(Config)

    with open(Target_Filename, 'wt') as cfg:
        cfg.write(rendered)
        cfg.write('\n')


def wipe_host_build_files(host):
    for directory in [ Nginx_Build_Dir, Nginx_Ipxe_Dir]:
        for filename in os.listdir(directory):
            if host.mac in filename:
                os.unlink(f"{directory}/{filename}")


def write_Dnsmasq(session):
    Hosts = session.exec(select(Host)).all()
    with open('/etc/dnsmasq.d/hosts.conf','wt') as dns:
        for host in Hosts:
            dns.write(f"dhcp-host={host.mac},{host.ip},{host.name}\n")


def write_Build_Files(host, session):
    wipe_host_build_files(host)
    Rname = 'local' if host.target == 'local' else host.os_name
    Templates = session.exec(select(OsTemplate).where(OsTemplate.os_name==Rname)).all()
    OS_Ver = session.exec(select(OsVersion).where(OsVersion.os_name==host.os_name,OsVersion.os_version==host.os_version)).one()
    # OS_ver = Config.get_os_version(host.os_name, host.os_ver)
    # print(OS_ver)
    for template in Templates:
        tpl_src = template.source
        output = template.output.replace('MAC', host.mac)
        print(f'Writing template {tpl_src} --> {output}')
        Config['hostname'] = host.name # | Config | OsVer
        render_template( tpl_src, Config|host.dict()|OS_Ver.dict(), f"{Nginx_Base_Dir}/{output}")


@app.post("/host")
def create_host(host: Host, session: SessionDep) -> Host:
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
    # OK
    session.add(host)
    session.commit()
    session.refresh(host)
    #
    write_Dnsmasq(session)
    write_Build_Files(host,session)
    return host


@app.get("/host")
def read_host_list(session: SessionDep, offset: int = 0,
           limit: Annotated[int, Query(le=100)] = 100, ) -> list[Host]:
    hosts = session.exec(select(Host).offset(offset).limit(limit)).all()
    return hosts


@app.get("/host/{host_name}")
def read_host(host_name: str, session: SessionDep) -> Host:
    host = session.get(Host, host_name)
    if not host:
        raise HTTPException(status_code=404, detail="Host not found")
    return host


@app.patch("/host/{host_name}")
def patch_hero(host_name: str, Patch:Host, session: SessionDep):
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
def build_host(host_name: str, session: SessionDep) -> Host:
    host = session.get(Host, host_name)
    if not host:
        raise HTTPException(status_code=404, detail="Host not found")
    host.target = 'local'
    session.add(host)
    session.commit()
    session.refresh(host)
    write_Build_Files(host, session)
    return host
