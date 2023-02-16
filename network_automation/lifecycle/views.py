#! /usr/bin/env python
"""
Creates the views (routes) for the secondary app
"""
from decouple import config
from flask import render_template, request, session, redirect
from network_automation.mac_finder import mac_finder
import network_automation.mac_finder.mac_finder.find_mac as find_mac

### VARIABLES ###
FLASK_SECRET_KEY = config("FLASK_SECRET_KEY")
template_dir = "lifecycle"

### VIEW TO CREATE DATA ###
@lifecycle.route("/home")
def home():
    return render_template(f"{template_dir}/home.html")

@lifecycle.route("/")
def home_redirect():
    return redirect("/home")


@lifecycle.route("/get_lifecycle_data", methods=["POST"])
def get_lifecycle_data():
    if request.method == "POST":
        Path(f"network_automation/standards_ops/staging").mkdir(exist_ok=True)
        site_code = request.form["siteId"]
        username = session.get("cli_username")
        password = session.get("cli_password")
        logger.info(f'Adding Infoblox Helper standards to {site_code}')
        results, failed_hosts = add_ib_helper.build_inventory(site_code, username, password)
        print(results, failed_hosts)
       
        if results == {True}:
            return render_template(f"{TEMPLATE_DIR}/results_success.html")
        else:
            return render_template(f"{TEMPLATE_DIR}/results_failure.html", failed_hosts=failed_hosts)

### ERROR & SUCCESS VIEWS ###

@lifecycle.route("/mac_found")
def mac_found():
    return render_template(f"{template_dir}/mac_found.html")
