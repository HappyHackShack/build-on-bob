from fastapi import FastAPI

from config import *
from database import *
from library import *

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World !"}

@app.get("/ping")
def ping_pong():
    return {"ping": "pong"}

