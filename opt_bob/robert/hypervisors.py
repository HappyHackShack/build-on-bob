from fastapi import HTTPException, Query
from sqlmodel import select
from typing import Annotated

from database import SessionDep
from library import (
    API_DELETE_Responses,
    API_GET_Responses,
    API_POST_Responses,
    write_ansible_inventory,
)
from main import app
from models import Hypervisor


@app.post(
    "/hypervisor", status_code=201, responses=API_POST_Responses, tags=["Hypervisors"]
)
def create_hypervisor(hypervisor: Hypervisor, session: SessionDep) -> Hypervisor:
    session.add(hypervisor)
    session.commit()
    session.refresh(hypervisor)
    write_ansible_inventory(session)
    return hypervisor


@app.get("/hypervisor", tags=["Hypervisors"])
def read_hypervisor_list(
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
) -> list[Hypervisor]:
    hypervisors = session.exec(select(Hypervisor).offset(offset).limit(limit)).all()
    return hypervisors


@app.get(
    "/hypervisor/{hypervisor_name}", responses=API_GET_Responses, tags=["Hypervisors"]
)
def read_hypervisor(hypervisor_name: str, session: SessionDep) -> Hypervisor:
    hypervisor = session.get(Hypervisor, hypervisor_name)
    if not hypervisor:
        raise HTTPException(status_code=404, detail=" Hypervisor not found")
    return hypervisor


@app.delete(
    "/hypervisor/{hypervisor_name}",
    responses=API_DELETE_Responses,
    tags=["Hypervisors"],
)
def delete_hypervisor(hypervisor_name: str, session: SessionDep):
    hypervisor = session.get(Hypervisor, hypervisor_name)
    if not hypervisor:
        raise HTTPException(status_code=404, detail=" Hypervisor not found")
    session.delete(hypervisor)
    session.commit()
    write_ansible_inventory(session)
    return {"ok": True}
