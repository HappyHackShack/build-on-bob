from fastapi import APIRouter, HTTPException, Query
from sqlmodel import select
from typing import Annotated

from database import SessionDep
from library import API_DELETE_Responses, API_GET_Responses, API_POST_Responses
from models import Subnet


sn_router = APIRouter(prefix="/subnet", tags=["Subnets"])


@sn_router.post("", status_code=201, responses=API_POST_Responses)
def create_subnet(subnet: Subnet, session: SessionDep) -> Subnet:
    if session.get(Subnet, subnet.network):
        raise HTTPException(status_code=409, detail="That Subnet already exists")

    # TODO is this within a supernet

    session.add(subnet)
    session.commit()
    session.refresh(subnet)
    return subnet


@sn_router.get("")
def read_subnet_list(
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
) -> list[Subnet]:
    subnets = session.exec(select(Subnet).offset(offset).limit(limit)).all()
    return subnets


@sn_router.get("/{network}", responses=API_GET_Responses)
def read_subnet(network: str, session: SessionDep) -> Subnet:
    subnet = session.get(Subnet, network)
    if not subnet:
        raise HTTPException(status_code=404, detail="Subnet not found")
    return subnet


@sn_router.delete("/{network}", responses=API_DELETE_Responses)
def delete_subnet(network: str, session: SessionDep):
    subnet = session.get(Subnet, network)
    if not subnet:
        raise HTTPException(status_code=404, detail="Subnet not found")
    if subnet.ipam:
        raise HTTPException(status_code=409, detail="Subnet has an active IPAM")
    session.delete(subnet)
    session.commit()
    return {"ok": True}
