from fastapi import APIRouter, HTTPException, Query
from sqlmodel import select
from typing import Annotated

from database import SessionDep
from library import API_DELETE_Responses, API_GET_Responses, API_POST_Responses
from models import OpSys, OsVersion

os_router = APIRouter(prefix="/os", tags=["Operating Systems"])


@os_router.post("", status_code=201, responses=API_POST_Responses)
def create_opsys(opsys: OpSys, session: SessionDep) -> OpSys:
    session.add(opsys)
    session.commit()
    session.refresh(opsys)
    return opsys


@os_router.get("")
def read_opsystems(
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
) -> list[OpSys]:
    systems = session.exec(select(OpSys).offset(offset).limit(limit)).all()
    return systems


@os_router.get("/{os_name}", responses=API_GET_Responses)
def read_opsys(os_name: str, session: SessionDep) -> OpSys:
    opsys = session.get(OpSys, os_name)
    if not opsys:
        raise HTTPException(status_code=404, detail="OS not found")
    return opsys


@os_router.delete("/{os_name}", responses=API_DELETE_Responses)
def delete_opsys(os_name: str, session: SessionDep):
    opsys = session.get(OpSys, os_name)
    if not opsys:
        raise HTTPException(status_code=404, detail="OS not found")
    session.delete(opsys)
    session.commit()
    return {"ok": True}


@os_router.get("version")
def read_all_os_versions(session: SessionDep) -> list[OsVersion]:
    sql = select(OsVersion)
    versions = session.exec(sql).all()
    return versions


@os_router.get("/{os_name}/version", responses=API_GET_Responses)
def read_os_versions4os(os_name: str, session: SessionDep) -> list[OsVersion]:
    if not session.get(OpSys, os_name):
        raise HTTPException(status_code=404, detail="OS not found")
    sql = select(OsVersion).where(OsVersion.os_name == os_name)
    versions = session.exec(sql).all()
    return versions


@os_router.get(
    "/{os_name}/version/{os_version}",
    responses=API_GET_Responses,
)
def read_one_os_version(
    os_name: str, os_version: str, session: SessionDep
) -> OsVersion:
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
