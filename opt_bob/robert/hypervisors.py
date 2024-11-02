from fastapi import APIRouter, HTTPException, Query
from sqlmodel import select
from typing import Annotated

from database import SessionDep
from library import (
    API_DELETE_Responses,
    API_GET_Responses,
    API_POST_Responses,
    write_ansible_hypervisor,
    write_ansible_inventory,
)
from models import Hypervisor

hv_router = APIRouter(prefix="/hypervisor", tags=["Hypervisors"])


@hv_router.post("", status_code=201, responses=API_POST_Responses)
def create_hypervisor(hypervisor: Hypervisor, session: SessionDep) -> Hypervisor:
    # Validations
    if session.get(Hypervisor, hypervisor.name):
        raise HTTPException(status_code=409, detail="Hypervisor already exists")
    #
    session.add(hypervisor)
    session.commit()
    session.refresh(hypervisor)
    write_ansible_inventory(session)
    write_ansible_hypervisor(hypervisor)
    return hypervisor


@hv_router.get("")
def read_hypervisor_list(
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
) -> list[Hypervisor]:
    hypervisors = session.exec(select(Hypervisor).offset(offset).limit(limit)).all()
    return hypervisors


@hv_router.get("/{hypervisor_name}", responses=API_GET_Responses)
def read_hypervisor(hypervisor_name: str, session: SessionDep) -> Hypervisor:
    hypervisor = session.get(Hypervisor, hypervisor_name)
    if not hypervisor:
        raise HTTPException(status_code=404, detail=" Hypervisor not found")
    return hypervisor


@hv_router.delete(
    "/{hypervisor_name}",
    responses=API_DELETE_Responses,
)
def delete_hypervisor(hypervisor_name: str, session: SessionDep):
    hypervisor = session.get(Hypervisor, hypervisor_name)
    if not hypervisor:
        raise HTTPException(status_code=404, detail=" Hypervisor not found")
    session.delete(hypervisor)
    session.commit()
    write_ansible_inventory(session)
    return {"ok": True}
