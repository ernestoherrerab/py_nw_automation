#! /usr/bin/env python
"""
Creates the views (routes) for the secondary app
"""
from decouple import config
from flask import redirect, render_template, request, session, url_for
from network_automation.sdwan_ops import sdwan_ops
import network_automation.sdwan_ops.snmp.update_snmp as update_snmp

TEMPLATE_DIR = "sdwan_ops"
VMANAGE_URL_VAR = config("VMANAGE_URL_VAR")

### VIEW TO CREATE DATA ###
@sdwan_ops.route("/home")
def home():
    return render_template(f"{TEMPLATE_DIR}/home.html")

@sdwan_ops.route("/")
def home_redirect():
    return redirect(url_for("sdwan_ops.home"))

@sdwan_ops.route("/vmanage_auth", methods=["POST", "GET"])
def vmanage_auth():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        session["username"] = username
        session["password"] = password

        return redirect(url_for("sdwan_ops.ops"))

@sdwan_ops.route("/ops")
def ops():
    return render_template(f"{TEMPLATE_DIR}/ops.html")

@sdwan_ops.route("/snmp")
def snmp():
    username = session.get("username")
    password = session.get("password")
    #username = "admin"
    #password = "C1sco12345"
    auth_header = update_snmp.auth(VMANAGE_URL_VAR, username, password)
    device_list = update_snmp.update_snmp(VMANAGE_URL_VAR, auth_header)
    print(device_list)
    return str(device_list)
