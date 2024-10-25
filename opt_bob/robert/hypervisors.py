from fastapi import HTTPException, Query
from sqlmodel import select
from typing import Annotated

from database import SessionDep
from library import *
from main import app
from models import *


@app.post("/hypervisor")
def create_hypervisor(hypervisor:  Hypervisor, session: SessionDep) ->  Hypervisor:
    session.add(hypervisor)
    session.commit()
    session.refresh(hypervisor)
    write_ansible_inventory(session)
    return hypervisor


@app.get("/hypervisor")
def read_hypervisor_list(session: SessionDep, offset: int = 0,
           limit: Annotated[int, Query(le=100)] = 100, ) -> list[ Hypervisor]:
    hypervisors = session.exec(select( Hypervisor).offset(offset).limit(limit)).all()
    return hypervisors


@app.get("/hypervisor/{hypervisor_name}")
def read_hypervisor(hypervisor_name: str, session: SessionDep) ->  Hypervisor:
    hypervisor = session.get( Hypervisor, hypervisor_name)
    if not hypervisor:
        raise HTTPException(status_code=404, detail=" Hypervisor not found")
    return hypervisor


@app.delete("/hypervisor/{hypervisor_name}")
def delete_hypervisor(hypervisor_name: str, session: SessionDep):
    hypervisor = session.get( Hypervisor, hypervisor_name)
    if not hypervisor:
        raise HTTPException(status_code=404, detail=" Hypervisor not found")
    session.delete(hypervisor)
    session.commit()
    write_ansible_inventory(session)
    return {"ok": True}