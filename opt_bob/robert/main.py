from contextlib import asynccontextmanager
from fastapi import HTTPException
from fastapi_offline import FastAPIOffline
from sqlmodel import select
import yaml

from database import create_db_and_tables, SessionDep
from library import Config, render_template
from models import Host, Node, OpSys, OsTemplate, OsVersion, Subnet
from hosts import h_router
from hypervisors import hv_router
from ipam import i_router
from nodes import n_router
from opsystems import os_router
from subnets import sn_router
from virtuals import vm_router

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
    lifespan=myLifespan,
    root_path="/api",
    # static_url = '/static-offline-docs'
)
app.include_router(h_router)
app.include_router(hv_router)
app.include_router(i_router)
app.include_router(n_router)
app.include_router(os_router)
app.include_router(sn_router)
app.include_router(vm_router)


@app.get("/config", tags=["Miscellaneous"])
def get_config():
    return Config()


@app.post("/cache/scripts", tags=["Miscellaneous"])
def cache_scripts_generate(session: SessionDep):
    Opt_Bob = Config.bob_home_directory
    Systems = session.exec(select(OpSys)).all()
    Versions = session.exec(select(OsVersion)).all()
    Temp = {"os_systems": Systems, "os_versions": Versions}

    render_template(
        "populate-cache.sh.j2", Config() | Temp, f"{Opt_Bob}/populate-cache.sh"
    )
    render_template(
        "fetch-from-cache.sh.j2", Config() | Temp, f"{Opt_Bob}/fetch-from-cache.sh"
    )

    return {"ok": True}


@app.post("/initialise/database", tags=["Miscellaneous"])
def init_database(session: SessionDep):
    try:
        with open("init-data.yaml", "rt") as init:
            Data = yaml.safe_load(init)
        print("Init-Data Loaded from ...")
        # Go through each OS
        for opsys in Data["op_systems"]:
            print("On OS:", opsys["name"])
            os = session.get(OpSys, opsys["name"])
            if not os:
                os = OpSys(**opsys)
                session.add(os)
            # Do each OS template
            for template in opsys["templates"]:
                sql = select(OsTemplate).where(
                    OsTemplate.os_name == opsys["name"],
                    OsTemplate.source == template["source"],
                )
                if not session.exec(sql).one_or_none():
                    tpl = OsTemplate(os_name=opsys["name"], **template)
                    session.add(tpl)
            # Now do the OS versions
            for version in opsys["versions"]:
                sql = select(OsVersion).where(
                    OsVersion.os_name == opsys["name"],
                    OsVersion.os_version == version["os_version"],
                )
                if not session.exec(sql).one_or_none():
                    version["files"] = ",".join(version["files"])
                    ver = OsVersion(os_name=opsys["name"], **version)
                    session.add(ver)

        # Localhost NDOE
        print("Create Local.Node")
        if not session.get(Node, "localhost"):
            localnode = Node(name="localhost")
            session.add(localnode)

        session.commit()
        return {"ok": True}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Oops - we hit a problem doing that:\n{e}"
        )
