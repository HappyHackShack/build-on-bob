from contextlib import asynccontextmanager

from typing import Annotated
from fastapi_offline import FastAPIOffline
import yaml

from library import *
from models import *
from database import *

# Some HTTP Response Codes
# 200 = OK
# 201 = Created
# 202 = Accepted
# 204 = No Content
# 400 = Bad Request; e.g. malformed data in the request
# 406 = Not Acceptable; well-formed request but doesn't meet other criteria
# 409 = Conflict; well-formed, but violates current data
# 410 = Gone
# 422 = Unprocessable Content (Data validation)
# 423 = Locked 


@asynccontextmanager
async def myLifespan(app: FastAPIOffline):
    create_db_and_tables()
    yield
    # nothing to do on exit

# Start the API App (with a lifespan)
app = FastAPIOffline(
    lifespan = myLifespan,
    root_path = '/api',
    #static_url = '/static-offline-docs'
)

from hosts import *
from hypervisors import *
from ipam import *
from nodes import *
from opsystems import *
from subnets import *
from virtuals import *


@app.get("/config", tags=['Miscellaneous'])
def get_config():
    return Config()


@app.post("/cache/scripts", tags=['Miscellaneous'])
def cache_scripts_generate(session: SessionDep):
    Opt_Bob = Config.bob_home_directory
    Local_Cache = Config.bob_local_cache
    Systems = session.exec(select(OpSys)).all()
    Versions = session.exec(select(OsVersion)).all()
    Temp = { 'os_systems': Systems, 'os_versions': Versions }

    render_template('populate-cache.sh.j2', Config()|Temp, f'{Opt_Bob}/populate-cache.sh')
    render_template('fetch-from-cache.sh.j2', Config()|Temp, f'{Opt_Bob}/fetch-from-cache.sh')

    return {"ok": True}


@app.post("/initialise/database", tags=['Miscellaneous'])
def init_database(session: SessionDep):
    try:
        with open('init-data.yaml','rt') as init:
            Data = yaml.safe_load(init)
        print('Init-Data Loaded from ...')
        # Go through each OS
        for opsys in Data['op_systems']:
            print('On OS:', opsys['name'])
            os = session.get(OpSys, opsys['name'])
            if not os:
                os = OpSys(**opsys)
                session.add(os)
            # Do each OS template
            for template in opsys['templates']:
                sql = select(OsTemplate).where(OsTemplate.os_name==opsys['name'], OsTemplate.source==template['source'])
                if not session.exec(sql).one_or_none():
                    tpl = OsTemplate(os_name=opsys['name'], **template)
                    session.add(tpl)
            # Now do the OS versions
            for version in opsys['versions']:
                sql = select(OsVersion).where(OsVersion.os_name==opsys['name'], OsVersion.os_version==version['os_version'])
                if not session.exec(sql).one_or_none():
                    version['files'] = ','.join(version['files'])
                    ver = OsVersion(os_name=opsys['name'], **version)
                    session.add(ver)

        # Localhost NDOE
        print('Create Local.Node')
        if not session.get(Node, 'localhost'):
            localnode = Node(name='localhost')
            session.add(localnode)

        # Local SUBNET
        print('Create Local.SubNet')
        sn0 = {"network":'172.16.0.0',"cidr":24,"gateway":'172.16.0.254',"nameservers":'172.16.0.254',"node":'localhost'}
        if not session.get(Subnet, sn0['network']):
            sn = Subnet(**sn0)
            session.add(sn)

        # Test HOST
        print('Create Test Host')
        lucy = { 'name':'lucy', 'ip':'172.16.0.12', 'mac':'e4:b9:7a:0b:bf:97' }
        if not session.get(Host, 'lucy'):
            h0 = Host(**lucy)
            session.add(h0)

        session.commit()
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Oops - we hit a problem doing that:\n{e}")
