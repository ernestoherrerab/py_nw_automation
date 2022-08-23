#! /usr/bin/env python
"""
Creates the views (routes) for the secondary app
"""
from decouple import config
from flask import render_template, request, redirect, session
from pathlib import Path
from yaml import dump
from network_automation.audit_manager import audit_manager
import network_automation.audit_manager.audit_manager.audit as audit


### VARIABLES ###
FLASK_SECRET_KEY = config("FLASK_SECRET_KEY")
AUDIT_MANAGER_INV_DIR = Path("network_automation/audit_manager/audit_manager/inventory/")
TEMPLATE_DIR = "audit_manager"

### VIEW TO CREATE DATA ###
@audit_manager.route("/home")
def home():
    return render_template(f"{TEMPLATE_DIR}/home.html")

@audit_manager.route("/")
def home_redirect():
    return redirect("/home")


"""ROUTE THAT REQUESTS CREDENTIALS FOR TACACS. THIS 
   ROUTE HOLDS THE DATA INPUT VALUE AND CARRIES 
   IT TO THE tacacs_auth FUNCTION TO UPLOAD DATA"""

@audit_manager.route("/tacacs_login", methods=["GET", "POST"])
def tacacs_login():
    if request.method == "POST":
        text_data = request.form
        for text in text_data.items():
            if "outputtext" in text:
                data_input = text[1]
                data_input = data_input.replace("\n", "").split("\r")
                for data in data_input:
                    data = data.split(",")
                    if data != [""]:
                        core_switch = {}
                        hostname = data[0]
                        ip_add = data[1]
                        nos = data[2]
                        site_id = hostname.split("-")
                        site_id = site_id[0]
                        session["levels"] = data[3]
                        core_switch[hostname] = {}
                        core_switch[hostname]["groups"] = [nos + "_devices"]
                        core_switch[hostname]["hostname"] = ip_add

    ### GENERATE DIRECTORY STRUCTURE ###
    Path("file_display/public/documentation").mkdir(exist_ok=True)
    Path(f"file_display/public/documentation/{site_id}").mkdir(exist_ok=True)
    Path(f"file_display/public/documentation/{site_id}/run_config").mkdir(exist_ok=True)
    Path(f"file_display/public/documentation/{site_id}/audits").mkdir(exist_ok=True)
    
    ### BUILD INITIAL NORNIR INVENTORY FILE ###
    host_yaml = dump(core_switch, default_flow_style=False)
    with open(AUDIT_MANAGER_INV_DIR / "hosts.yml", "w") as open_file:
        open_file.write(host_yaml)
    return render_template(f"{TEMPLATE_DIR}/tacacs_login.html", core_switch=core_switch)

@audit_manager.route("/tacacs_auth", methods=["POST", "GET"])
def tacacs_auth():
    if request.method == "POST":
        if "username" in request.form:
            username = request.form["username"]
            password = request.form["password"]
            depth_levels = session.get("levels")
            depth_levels = int(depth_levels)
            audit.do_audit(username, password, depth_levels)
            return render_template(f"{TEMPLATE_DIR}/audit_results.html")


### ERROR & SUCCESS VIEWS ###

@audit_manager.route("/audit_results")
def audit_results():
    return render_template(f"{TEMPLATE_DIR}/audit_results.html")