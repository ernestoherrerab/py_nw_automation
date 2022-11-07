#! /usr/bin/env python
"""
Initializes the main app and the sub apps
"""
import sys
from decouple import config
from flask import Flask, render_template, redirect
import logging
from pathlib import Path
from network_automation.standards_ops.views import standards_ops
from network_automation.hostname_changer.views import hostname_changer
from network_automation.ise_ops.views import ise_ops
from network_automation.mac_finder.views import mac_finder
from network_automation.nw_infra_links.views import nw_infra_links
from network_automation.sdwan_ops.views import sdwan_ops
from network_automation.site_documentation.views import site_documentation
from network_automation.topology_builder.views import topology_builder

sys.dont_write_bytecode = True

FLASK_KEY = config("FLASK_SECRET_KEY")
REACT_SERVER = config("REACT_SERVER")

### INITIALIZE THE MAIN APP ###
app = Flask(__name__)
app.secret_key = FLASK_KEY

### LOGGING ### 
LOG_FILE = Path("logs/flask.log")
logging.basicConfig(filename=LOG_FILE, level=logging.INFO)

### REGISTER BLUEPRINTS OF SECONDARY APPS ###
app.register_blueprint(standards_ops, url_prefix="/standards-ops")
app.register_blueprint(hostname_changer, url_prefix="/hostname-changer")
app.register_blueprint(ise_ops, url_prefix="/ise-ops")
app.register_blueprint(mac_finder, url_prefix="/mac-finder")
app.register_blueprint(nw_infra_links, url_prefix="/nw-infra-links")
app.register_blueprint(sdwan_ops, url_prefix="/sdwan-ops")
app.register_blueprint(site_documentation, url_prefix="/site_documentation")
app.register_blueprint(topology_builder, url_prefix="/topology-builder")

### VIEWS OR ROUTES ###
@app.route("/home")
def home():
    return render_template("home.html", REACT_SERVER=REACT_SERVER)

@app.route("/")
def home_redirect():
    return redirect("/home")