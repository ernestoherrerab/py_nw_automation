#! /usr/bin/env python
"""
Creates the views (routes) for the secondary app
"""
from decouple import config
from flask import render_template, request, session, current_app, redirect, send_file, url_for
from pathlib import Path
from werkzeug.utils import secure_filename
from network_automation.panorama_ops import panorama_ops
import network_automation.panorama_ops.address_checker as address_checker

### VARIABLES ###
FLASK_SECRET_KEY = config("FLASK_SECRET_KEY")
TEMPLATE_DIR = "panorama_ops"
LOG_FILE = Path("logs/panorama_ops.log")

### ISE OPS HOME ###
@panorama_ops.route("/home")
def home():
    """ 
    Home Page
    """
    return render_template(f"{TEMPLATE_DIR}/home.html")

@panorama_ops.route("/")
def home_redirect():
    """ 
    Home Redirect 
    """
    return redirect(url_for("panorama_ops.home"))

@panorama_ops.route("/address_checker", methods=["POST", "GET"])
def address_checker():

    return render_template(f"{TEMPLATE_DIR}/address_checker.html")


### LOG FILE DOWNLOAD ###
@panorama_ops.route("ise_log_file")
def ise_log_file():
    """ 
    Download Log File
    """
    return send_file(f'./../{str(LOG_FILE)}', as_attachment=True)


### VIEWS TO DELETE DATA ###
@panorama_ops.route("/mac_bypass_del_csv_upload")
def mac_bypass_del_csv_upload():
    """ CSV Upload Data Input
    """

    Path("network_automation/panorama_ops/mac_bypass/csv_data/").mkdir(exist_ok=True)
    return render_template(f"{TEMPLATE_DIR}/mac_bypass_del_csv_upload.html")


### ERROR & SUCCESS VIEWS ###

@panorama_ops.route("/ise_mac_bypass_upload.html")
def ise_mac_bypass_upload():
    return render_template(f"{TEMPLATE_DIR}/ise_mac_bypass_upload.html")

@panorama_ops.route("/ise_auth_error")
def ise_auth_error():
    return render_template(f"{TEMPLATE_DIR}/ise_auth_error.html")

@panorama_ops.route("/ise_mac_bypass_upload_error")
def ise_mac_bypass_upload_error():
    return render_template(f"{TEMPLATE_DIR}/ise_mac_bypass_upload_error.html")