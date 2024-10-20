from dataclasses import dataclass
from datalite import datalite
from datalite.fetch import fetch_all, fetch_from
#from datalite.migrations import basic_migrate

BoB_DB = 'bob-data.db'

@datalite(db_path=BoB_DB)
@dataclass
class Config:
    key: str
    value: str


@datalite(db_path=BoB_DB)
@dataclass
class Node:
    hostname: str
    shared_key: str


@datalite(db_path=BoB_DB)
@dataclass
class Host:
    name: str
    ip: str
    mac: str
    os: str
    version: str
    disk: str
    target: str
    