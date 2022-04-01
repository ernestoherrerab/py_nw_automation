#! /usr/bin/env python
"""
Creates the views (routes) for the secondary app
"""
from decouple import config
from flask import render_template, request, session, current_app, redirect, url_for
from network_automation.mac_finder import mac_finder
import network_automation.mac_finder.mac_finder.find_mac as find_mac

### VARIABLES ###
FLASK_SECRET_KEY = config("FLASK_SECRET_KEY")
template_dir = "mac_finder"

### VIEW TO CREATE DATA ###
@mac_finder.route("/home")
def home():
    return render_template(f"{template_dir}/home.html")

"""ROUTE THAT REQUESTS CREDENTIALS FOR ISE THIS 
   ROUTE HOLDS THE DATA INPUT VALUE AND CARRIES 
   IT TO THE del_ise_auth FUNCTION TO UPLOAD DATA"""
@mac_finder.route("/tacacs_login", methods = ['GET', 'POST'])
def tacacs_login():
    return render_template(f"{template_dir}/tacacs_login.html")

@mac_finder.route("/tacacs_auth", methods = ['POST', 'GET'])
def tacacs_auth():
    if request.method == 'POST':
        if "username" in request.form:
            username=request.form['username']
            password=request.form['password']
            result = find_mac.mac_finder(username, password)
            session["result"] = result
            return render_template(f"{template_dir}/mac_found.html", result=result)

### ERROR & SUCCESS VIEWS ###

@mac_finder.route("/mac_found")
def graph_upload():
    return render_template(f"{template_dir}/mac_found.html")
