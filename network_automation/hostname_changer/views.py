#! /usr/bin/env python
"""
Creates the views (routes) for the secondary app
"""
from decouple import config
from flask import render_template, request, redirect, session, send_file
from pathlib import Path
from yaml import dump
from network_automation.hostname_changer import hostname_changer
import network_automation.hostname_changer.hostname_changer.change_hostname as change_hostname
import network_automation.hostname_changer.hostname_changer.get_hostname_data as get_hostname

### VARIABLES ###
FLASK_SECRET_KEY = config("FLASK_SECRET_KEY")
HOSTNAME_CHANGER_UPLOAD_DIR = Path("network_automation/hostname_changer/hostname_changer/inventory/")
template_dir = "hostname_changer"

### VIEW TO CREATE DATA ###
@hostname_changer.route("/home")
def home():
    return render_template(f"{template_dir}/home.html")

@hostname_changer.route("/")
def home_redirect():
    return redirect("/home")

"""ROUTE THAT REQUESTS CREDENTIALS FOR TACACS. THIS 
   ROUTE HOLDS THE DATA INPUT VALUE AND CARRIES 
   IT TO THE tacacs_auth FUNCTION TO UPLOAD DATA"""

@hostname_changer.route("/tacacs_login", methods=["GET", "POST"])
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
    Path("documentation").mkdir(exist_ok=True)
    Path(f"documentation/{site_id}").mkdir(exist_ok=True)
    Path(f"documentation/{site_id}/hostname_changes").mkdir(exist_ok=True)
    HOSTNAME_CHANGER_DOWNLOAD_DIR = Path(f"documentation/{site_id}/hostname_changes")
    session["HOSTNAME_CHANGER_DOWNLOAD_DIR"] = str(HOSTNAME_CHANGER_DOWNLOAD_DIR)
    
    ### BUILD INITIAL NORNIR INVENTORY FILE ###
    host_yaml = dump(core_switch, default_flow_style=False)
    with open(HOSTNAME_CHANGER_UPLOAD_DIR / "hosts.yml", "w") as open_file:
        open_file.write(host_yaml)
    return render_template(f"{template_dir}/tacacs_login.html", core_switch=core_switch)

@hostname_changer.route("/tacacs_auth", methods=["POST", "GET"])
def tacacs_auth():
    if request.method == "POST":
        if "username" in request.form:
            username = request.form["username"]
            password = request.form["password"]
            depth_levels = session.get("levels")
            depth_levels = int(depth_levels)
            results, reference = change_hostname.change_hostname(username, password, depth_levels)
            session["reference"] = reference
            return render_template(f"{template_dir}/host_changed.html", results=results)

@hostname_changer.route("/download_ref_file")
def download_ref_file():
    HOSTNAME_CHANGER_DOWNLOAD_DIR = session.get("HOSTNAME_CHANGER_DOWNLOAD_DIR")
    ref_file = session.get("reference")
    ref_file = ref_file + ".txt"
    ref_path = "../" / Path(HOSTNAME_CHANGER_DOWNLOAD_DIR) / ref_file
    return send_file(str(ref_path), as_attachment=True)

### ERROR & SUCCESS VIEWS ###

@hostname_changer.route("/host_changed")
def host_changed():
    return render_template(f"{template_dir}/host_changed.html")

@hostname_changer.route("/prime_auth_error")
def prime_auth_error():
    return render_template(f"{template_dir}/prime_auth_error.html")

@hostname_changer.route("/prime_upload_error")
def prime_upload_error():
    return render_template(f"{template_dir}/prime_upload_error.html")
