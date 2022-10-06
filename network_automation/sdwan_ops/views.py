#! /usr/bin/env python
"""
Creates the views (routes) for the secondary app
"""
from decouple import config
from flask import redirect, render_template, request, session, send_file, url_for
from pathlib import Path
from yaml import dump
from network_automation.sdwan_ops import sdwan_ops
import network_automation.sdwan_ops.hostname.update_hostname as update_hostname
import network_automation.sdwan_ops.prisma_access.provision_tunnel as prisma_tunnels

TEMPLATE_DIR = "sdwan_ops"
LOG_FILE = Path("logs/tunnel_provision.log")
PANAPI_CONFIG_PATH = Path("network_automation/sdwan_ops/prisma_access/config.yml")
VMANAGE_URL_VAR = config("VMANAGE_URL_VAR")
PRISMA_CLIENT_ID = config("PRISMA_CLIENT_ID")
PRISMA_CLIENT_SECRET = config("PRISMA_CLIENT_SECRET")
PRISMA_CLIENT_SCOPE = config("PRISMA_CLIENT_SCOPE")
PRISMA_TOKEN_URL = config("PRISMA_TOKEN_URL")


### SDWAN HOSTNAME CHANGE ###

@sdwan_ops.route("/home")
def home():
    """ Homepage for SDWAN Operations """
    
    return render_template(f"{TEMPLATE_DIR}/home.html")

@sdwan_ops.route("/")
def home_redirect():
    """ Home Redirect """

    return redirect(url_for("sdwan_ops.home"))

@sdwan_ops.route("/vmanage_auth", methods=["POST", "GET"])
def vmanage_auth():
    """ Login Page """

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        session["username"] = username
        session["password"] = password

        return redirect(url_for("sdwan_ops.ops"))

@sdwan_ops.route("/ops")
def ops():
    """ Select SDWAN Operation to perform"""

    return render_template(f"{TEMPLATE_DIR}/ops.html")

@sdwan_ops.route("/hostname")
def hostname():
    """ Launch hostname change process """
    dev_results= []
    username = session.get("username")
    password = session.get("password")
    result = update_hostname.update_hostname(VMANAGE_URL_VAR, username, password)
    
    ### FORMAT SUMMARY FOR HTML PRESENTATION ###
    summary = result["summary"]
    for dev_result in result["data"]:
        dev_data = (dev_result["host-name"], dev_result["status"])
        dev_results.append(dev_data)
    
    ### SUMMARY FOR CONSOLE ###
    print(summary)
    print("*" * 100)
    print(dev_results)

    return render_template(f"{TEMPLATE_DIR}/hostname_summary.html", summary=summary, dev_results=dev_results, )

@sdwan_ops.route("/hostname_summary")
def hostname_summary():
    """ Summary of Hostname changes"""

    return render_template(f"{TEMPLATE_DIR}/hostname_summary.html")

#### PRISMA ACCESS TUNNEL PROVISIONING ###

@sdwan_ops.route("/prisma_site")
def prisma_site():
    """ Site Data User Input """

    return render_template(f"{TEMPLATE_DIR}/prisma_site.html")

@sdwan_ops.route("/tunnel_error")
def tunnel_error():
    """ Error Page """
    return render_template(f"{TEMPLATE_DIR}/tunnel_error.html")

@sdwan_ops.route("/tunnel_success")
def tunnel_success():
    """ Success Page """
    return render_template(f"{TEMPLATE_DIR}/tunnel_success.html")

@sdwan_ops.route("provision_prisma_access", methods=["POST"])
def provision_prisma_access():
    """ Launch Prisma Access Tunnels Provisioning """
    
    if request.method == "POST":
        username = session.get("username")
        password = session.get("password")
        text_data = request.form
        for text in text_data.items():
            if "outputtext" in text:
                data_input = text[1]
                data_input = data_input.replace("\n", "").split("\r")
                for data in data_input:
                    data = data.split(",")
                    if data != [""]:
                        site_data = {}
                        site_code = data[0]
                        location_id = data[1]
                        site_data["site_code"] = site_code
                        site_data["location_id"] = location_id
    else:
        return "Error"
    
    ### PANAPI AUTH INPUT DATA ###

    auth_input = {
        "client_id" : PRISMA_CLIENT_ID,
        "client_secret" : PRISMA_CLIENT_SECRET,
        "scope": PRISMA_CLIENT_SCOPE,
        "token_url": PRISMA_TOKEN_URL
    }
    with open(PANAPI_CONFIG_PATH, "w+") as f:
        dump(auth_input, f)

    ### PROVISION TUNNELS (REMOTE NETWORK) ###
    results = prisma_tunnels.provision_tunnel(PANAPI_CONFIG_PATH, site_data, VMANAGE_URL_VAR, username, password) 
    return results

@sdwan_ops.route("prisma_log_file")
def prisma_log_file():
    """ Download Log File"""
    
    return send_file(f'./../{str(LOG_FILE)}', as_attachment=True)

