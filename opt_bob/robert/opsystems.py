from fastapi import HTTPException, Query
from sqlmodel import select
from typing import Annotated

from database import SessionDep
from library import API_DELETE_Responses, API_GET_Responses, API_POST_Responses
from main import app
from models import OpSys, OsVersion


@app.post(
    "/os", status_code=201, responses=API_POST_Responses, tags=["Operating Systems"]
)
def create_opsys(opsys: OpSys, session: SessionDep) -> OpSys:
    session.add(opsys)
    session.commit()
    session.refresh(opsys)
    return opsys


@app.get("/os", tags=["Operating Systems"])
def read_opsystems(
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
) -> list[OpSys]:
    systems = session.exec(select(OpSys).offset(offset).limit(limit)).all()
    return systems


@app.get("/os/{os_name}", responses=API_GET_Responses, tags=["Operating Systems"])
def read_opsys(os_name: str, session: SessionDep) -> OpSys:
    opsys = session.get(OpSys, os_name)
    if not opsys:
        raise HTTPException(status_code=404, detail="OS not found")
    return opsys


@app.delete("/os/{os_name}", responses=API_DELETE_Responses, tags=["Operating Systems"])
def delete_opsys(os_name: str, session: SessionDep):
    opsys = session.get(OpSys, os_name)
    if not opsys:
        raise HTTPException(status_code=404, detail="OS not found")
    session.delete(opsys)
    session.commit()
    return {"ok": True}


@app.get("/osver", tags=["Operating Systems"])
def read_all_os_versions(session: SessionDep) -> list[OsVersion]:
    sql = select(OsVersion)
    versions = session.exec(sql).all()
    return versions


@app.get("/osver/{os_name}", responses=API_GET_Responses, tags=["Operating Systems"])
def read_os_versions4os(os_name: str, session: SessionDep) -> list[OsVersion]:
    if not session.get(OpSys, os_name):
        raise HTTPException(status_code=404, detail="OS not found")
    sql = select(OsVersion).where(OsVersion.os_name == os_name)
    versions = session.exec(sql).all()
    return versions


@app.get(
    "/osver/{os_name}/{os_version}",
    responses=API_GET_Responses,
    tags=["Operating Systems"],
)
def read_os_version(os_name: str, os_version: str, session: SessionDep) -> OsVersion:
    if not session.get(OpSys, os_name):
        raise HTTPException(status_code=404, detail="OS not found")
    sql = (
        select(OsVersion)
        .where(OsVersion.os_name == os_name)
        .where(OsVersion.os_version == os_version)
    )
    version = session.exec(sql).one_or_none()
    if version:
        return version
    else:
        raise HTTPException(status_code=404, detail="OS_Version not found")
