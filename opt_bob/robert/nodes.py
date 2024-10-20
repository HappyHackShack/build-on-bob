from fastapi import HTTPException, Query
from sqlmodel import select
from typing import Annotated

from database import SessionDep
from main import app
from models import *


@app.post("/node")
def create_node(node: Node, session: SessionDep) -> Node:
    session.add(node)
    session.commit()
    session.refresh(node)
    return node


@app.get("/node")
def read_node_list(session: SessionDep, offset: int = 0,
           limit: Annotated[int, Query(le=100)] = 100, ) -> list[Node]:
    nodes = session.exec(select(Node).offset(offset).limit(limit)).all()
    return nodes


@app.get("/node/{node_name}")
def read_node(node_name: str, session: SessionDep) -> Node:
    node = session.get(Node, node_name)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return node


@app.delete("/node/{node_name}")
def delete_node(node_name: str, session: SessionDep):
    node = session.get(Node, node_name)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    session.delete(node)
    session.commit()
    return {"ok": True}
