from flask import Flask, redirect, render_template as render_web_template, request

from config import *
from library import *
from wendy import app

Context = {}


@app.route("/")
def hello_world():
    Context["page_title"] = "Home"
    return render_web_template("home.htm", ctx=Context)


@app.route("/ping")
def ping_pong():
    return "pong\n"


@app.route("/api/complete/<mac>")
def complete_host(mac):
    os.system(f"/usr/local/sbin/bob complete {mac}")
    return "OK"


@app.route("/hosts")
def hosts_idx():
    Hosts.load()
    Context["page_title"] = "Hosts"
    Context["hosts"] = Hosts
    return render_web_template("hosts.htm", ctx=Context)


@app.route("/ipam")
def ipam_idx():
    Context["page_title"] = "IPAM"
    return render_web_template("ipam.htm", ctx=Context)


@app.route("/nodes")
def nodes_idx():
    Context["page_title"] = "Nodes"
    return render_web_template("nodes.htm", ctx=Context)


@app.route("/os")
def os_idx():
    Context["page_title"] = "OS"
    Context["opsystems"] = Config["os_cache"]

    return render_web_template("os.htm", ctx=Context)


@app.route("/subnets")
def subnets_idx():
    Context["page_title"] = "Subnets"
    return render_web_template("subnets.htm", ctx=Context)
