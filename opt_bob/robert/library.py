from jinja2 import Environment, FileSystemLoader
import os
from sqlmodel import select
import yaml

from models import *

My_Dir = os.path.dirname(__file__)
Template_Dir = f"{My_Dir}/../templates"

### ---------- Configuration   -----------------------------------------------------------

Config_File = '/etc/bob/config.yaml'

class Configuration():
    Data = {}

    def __init__(self) -> None:
        with open(Config_File, 'rt') as cfg:
            Configuration.Data = yaml.safe_load(cfg)

    def __call__(self) -> dict:
        return Configuration.Data
    
    def __getattribute__(self, name: str) -> str:
        if name in Configuration.Data:
            return Configuration.Data[name]
        else:
            return ''

Config = Configuration()


### ---------- Build Templates -----------------------------------------------------------

def render_template(Template_Filename, Config, Target_Filename):
    environment = Environment(loader=FileSystemLoader(Template_Dir))
    template = environment.get_template(Template_Filename)
    rendered = template.render(Config)

    with open(Target_Filename, 'wt') as cfg:
        cfg.write(rendered)
        cfg.write('\n')


def wipe_host_build_files(host):
    for directory in [ Config.nginx_build_dir, Config.nginx_ipxe_dir ]:
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
    for template in Templates:
        tpl_src = template.source
        output = template.output.replace('MAC', host.mac)
        print(f'Writing template {tpl_src} --> {output}')
        #cfg = host.dict() | OS_Ver.dict()
        render_template( tpl_src, Config()|host.dict()|OS_Ver.dict(), f"{Config.nginx_base_dir}/{output}")
