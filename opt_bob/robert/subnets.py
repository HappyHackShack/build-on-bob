from fastapi import HTTPException, Query
from sqlmodel import select
from typing import Annotated

from database import SessionDep
from main import app
from models import *


@app.post("/subnet")
def create_subnet(subnet: Subnet, session: SessionDep) -> Subnet:
    session.add(subnet)
    session.commit()
    session.refresh(subnet)
    return subnet


@app.get("/subnet")
def read_subnet_list(session: SessionDep, offset: int = 0,
           limit: Annotated[int, Query(le=100)] = 100, ) -> list[Subnet]:
    subnets = session.exec(select(Subnet).offset(offset).limit(limit)).all()
    return subnets


@app.get("/subnet/{network}")
def read_subnet(network: str, session: SessionDep) -> Subnet:
    subnet = session.get(Subnet, network)
    if not subnet:
        raise HTTPException(status_code=404, detail="Subnet not found")
    return subnet


@app.delete("/subnet/{network}")
def delete_subnet(network: str, session: SessionDep):
    subnet = session.get(Subnet, network)
    if not subnet:
        raise HTTPException(status_code=404, detail="Subnet not found")
    session.delete(subnet)
    session.commit()
    return {"ok": True}
