#! /usr/bin/env python
"""
Creates the views (routes) for the secondary app
"""
from flask import redirect, render_template, request, session, send_file, url_for
from pathlib import Path
from network_automation.sdwan_ops import sdwan_ops
import network_automation.sdwan_ops.prisma_access.provision_tunnel as prisma_tunnels

TEMPLATE_DIR = "sdwan_ops"
LOG_FILE = Path("logs/sdwan_ops.log")

### SDWAN OPS HOME ###

@sdwan_ops.route("/home")
def home():
    """ 
    Homepage for SDWAN Operations 
    """
    return render_template(f"{TEMPLATE_DIR}/home.html")

@sdwan_ops.route("/")
def home_redirect():
    """ 
    Home Redirect 
    """
    return redirect(url_for("sdwan_ops.home"))

@sdwan_ops.route("/vmanage_auth", methods=["POST", "GET"])
def vmanage_auth():
    """ 
    Login Page 
    """
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        session["username"] = username
        session["password"] = password
        return redirect(url_for("sdwan_ops.ops"))

@sdwan_ops.route("/ops")
def ops():
    """ 
    Select SDWAN Operation to perform
    """
    return render_template(f"{TEMPLATE_DIR}/ops.html")

#### PRISMA ACCESS TUNNEL PROVISIONING ###

@sdwan_ops.route("/prisma_site")
def prisma_site():
    """ 
    Site Data User Input
    """
    return render_template(f"{TEMPLATE_DIR}/prisma_site.html")

@sdwan_ops.route("/tunnel_error")
def tunnel_error():
    """ 
    Error Page 
    """
    return render_template(f"{TEMPLATE_DIR}/tunnel_error.html")

@sdwan_ops.route("/tunnel_summary")
def tunnel_summary():
    """ 
    Summary Page 
    """
    return render_template(f"{TEMPLATE_DIR}/tunnel_summary.html")

@sdwan_ops.route("provision_prisma_access", methods=["POST"])
def provision_prisma_access():
    """ 
    Launch Prisma Access Tunnels Provisioning 
    """
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
                        region_id = data[1]
                        location_id = data[2]
                        site_data["site_code"] = site_code
                        site_data["region_id"] = region_id
                        site_data["location_id"] = location_id
    else:
        return "Unexpected Error"

    ### PROVISION TUNNELS (REMOTE NETWORK) ###
    results = prisma_tunnels.provision_tunnel(site_data, username, password) 
    
    ### FORMAT SUMMARY FOR HTML PRESENTATION ###
    if results != False:
        return render_template(f"{TEMPLATE_DIR}/tunnel_summary.html", results=results)
    else:
        return render_template(f"{TEMPLATE_DIR}/tunnel_error.html")

@sdwan_ops.route("prisma_log_file")
def prisma_log_file():
    """ 
    Download Log File
    """
    return send_file(f'./../{str(LOG_FILE)}', as_attachment=True)

