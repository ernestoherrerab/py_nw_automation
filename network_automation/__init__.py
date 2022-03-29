#! /usr/bin/env python
"""
Initializes the main app and the sub apps
"""
import sys
sys.dont_write_bytecode = True
from decouple import config
from flask import Flask, render_template, redirect
from network_automation.ise_mac_bypass.views import ise_mac_bypass
from network_automation.nw_infra_links.views import nw_infra_links

FLASK_KEY = config("FLASK_SECRET_KEY")

### INITIALIZE THE MAIN APP ###
app = Flask(__name__)
app.secret_key = FLASK_KEY

### REGISTER BLUEPRINTS OF SECONDARY APPS ###
app.register_blueprint(ise_mac_bypass, url_prefix="/ise-mac-bypass")
app.register_blueprint(nw_infra_links, url_prefix="/nw-infra-links")

### VIEWS OR ROUTES ###
@app.route("/home")
def home():
    return render_template("home.html")

@app.route("/")
def home_redirect():
    return redirect("/home")
