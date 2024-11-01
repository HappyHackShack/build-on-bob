from fastapi import APIRouter, HTTPException, Query
from sqlmodel import select
from typing import Annotated

from database import SessionDep
from library import API_DELETE_Responses, API_GET_Responses, API_POST_Responses
from models import Node

n_router = APIRouter(prefix="/node", tags=["Nodes"])


@n_router.post("", status_code=201, responses=API_POST_Responses)
def create_node(node: Node, session: SessionDep) -> Node:
    session.add(node)
    session.commit()
    session.refresh(node)
    return node


@n_router.get("")
def read_node_list(
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
) -> list[Node]:
    nodes = session.exec(select(Node).offset(offset).limit(limit)).all()
    return nodes


@n_router.get("/{node_name}", responses=API_GET_Responses)
def read_node(node_name: str, session: SessionDep) -> Node:
    node = session.get(Node, node_name)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return node


@n_router.delete("/{node_name}", responses=API_DELETE_Responses)
def delete_node(node_name: str, session: SessionDep):
    node = session.get(Node, node_name)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    session.delete(node)
    session.commit()
    return {"ok": True}
