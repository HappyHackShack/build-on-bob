from fastapi import HTTPException, Query
from sqlmodel import select
from typing import Annotated

from database import SessionDep
from main import app
from models import *


@app.post("/ipam")
def create_ipam(ipam: IPAM, session: SessionDep) -> IPAM:
    session.add(ipam)
    session.commit()
    session.refresh(ipam)
    return ipam


@app.get("/ipam")
def read_ipam_list(session: SessionDep, offset: int = 0,
           limit: Annotated[int, Query(le=100)] = 100, ) -> list[IPAM]:
    ipams = session.exec(select(IPAM).offset(offset).limit(limit)).all()
    return ipams


@app.get("/ipam/{ipam_name}")
def read_ipam(ipam_name: str, session: SessionDep) -> IPAM:
    ipam = session.get(IPAM, ipam_name)
    if not ipam:
        raise HTTPException(status_code=404, detail="IPAM not found")
    return ipam


@app.delete("/ipam/{ipam_name}")
def delete_ipam(ipam_name: str, session: SessionDep):
    ipam = session.get(IPAM, ipam_name)
    if not ipam:
        raise HTTPException(status_code=404, detail="IPAM not found")
    session.delete(ipam)
    session.commit()
    return {"ok": True}
