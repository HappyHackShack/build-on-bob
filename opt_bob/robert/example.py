from fastapi import HTTPException, Query
from sqlmodel import select
from typing import Annotated, Any

#from database import SessionDep
#from main import app
#from models import *


class Billy():
    def __getattribute__(self, name: str) -> Any:
        if name == 'red':
            return 'RED'
        if name == 'green':
            return 'GREEN'
        if name == 'blue':
            return 'BLUE'
        return 'BLANK'


# @app.post("/heroes/")
# def create_hero(hero: Hero, session: SessionDep) -> Hero:
#     session.add(hero)
#     session.commit()
#     session.refresh(hero)
#     return hero


# @app.get("/heroes/")
# def read_heroes(session: SessionDep, offset: int = 0,
#            limit: Annotated[int, Query(le=100)] = 100, ) -> list[Hero]:
#     heroes = session.exec(select(Hero).offset(offset).limit(limit)).all()
#     return heroes


# @app.get("/heroes/{hero_id}")
# def read_hero(hero_id: int, session: SessionDep) -> Hero:
#     hero = session.get(Hero, hero_id)
#     if not hero:
#         raise HTTPException(status_code=404, detail="Hero not found")
#     return hero


# @app.delete("/heroes/{hero_id}")
# def delete_hero(hero_id: int, session: SessionDep):
#     hero = session.get(Hero, hero_id)
#     if not hero:
#         raise HTTPException(status_code=404, detail="Hero not found")
#     session.delete(hero)
#     session.commit()
#     return {"ok": True}


# @app.patch("/heroes/{hero_id}")
# def patch_hero(hero_id: int, Patch:Hero, session: SessionDep):
#     hero = session.get(Hero, hero_id)
#     if not hero:
#         raise HTTPException(status_code=404, detail="Hero not found")
    
#     if Patch.name:
#         hero.name = Patch.name
#     if Patch.age:
#         hero.age = Patch.age
#     if Patch.secret_name:
#         hero.secret_name = Patch.secret_name
#     if Patch.colour:
#         hero.colour = Patch.colour
#     #
#     session.add(hero)
#     session.commit()
#     session.refresh(hero)
#     return hero
