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
template_dir = "mac_finder"

### VIEW TO CREATE DATA ###
@mac_finder.route("/home")
def home():
    return render_template(f"{template_dir}/home.html")

@mac_finder.route("/")
def home_redirect():
    return redirect("/home")

"""ROUTE THAT REQUESTS CREDENTIALS FOR ISE THIS 
   ROUTE HOLDS THE DATA INPUT VALUE AND CARRIES 
   IT TO THE del_ise_auth FUNCTION TO UPLOAD DATA"""

@mac_finder.route("/tacacs_login", methods=["GET", "POST"])
def tacacs_login():
    if request.method == "POST":
        text_data = request.form
        for text in text_data.items():
            if "outputtext" in text:
                data_input = text[1]
                data_input = data_input.replace("\n", "").split("\r")
                print(data_input)
                for data in data_input:
                    data = data.split(",")
                    if data != [""]:
                        core_switch = {}
                        hostname = data[0]
                        host_ip = data[1]
                        find_ip = data[2]
                        core_switch["hostname"] = hostname
                        core_switch["host_ip"] = host_ip
                        core_switch["find_ip"] = find_ip
    session["core_switch"] = core_switch
    return render_template(f"{template_dir}/tacacs_login.html", core_switch=core_switch)

@mac_finder.route("/tacacs_auth", methods=["POST", "GET"])
def tacacs_auth():
    if request.method == "POST":
        if "username" in request.form:
            username = request.form["username"]
            password = request.form["password"]
            if not session.get("core_switch") is None:
                core_data = session.get("core_switch")
                hostname = core_data["hostname"]
                host_ip = core_data["host_ip"]
                find_ip = core_data["find_ip"]
                result = find_mac.find_mac(
                    hostname, host_ip, find_ip, username, password
                )
                return render_template(f"{template_dir}/mac_found.html", result=result)

### ERROR & SUCCESS VIEWS ###

@mac_finder.route("/mac_found")
def mac_found():
    return render_template(f"{template_dir}/mac_found.html")
