#! /usr/bin/env python
"""
Creates the views (routes) for the secondary app
"""
from decouple import config
from flask import render_template, request, session, current_app, redirect, send_file, url_for
from pathlib import Path
from werkzeug.utils import secure_filename
from network_automation.infoblox_ops import infoblox_ops
import network_automation.infoblox_ops.dhcp.dhcp as dhcp_add

### VARIABLES ###
FLASK_SECRET_KEY = config("FLASK_SECRET_KEY")
ISE_MAC_BYPASS_UPLOAD_DIR = Path("network_automation/infoblox_ops/mac_bypass/csv_data/")
TEMPLATE_DIR = "infoblox_ops"
LOG_FILE = Path("logs/infoblox_ops.log")

### ISE OPS HOME ###
@infoblox_ops.route("/home")
def home():
    """ 
    Home Page
    """
    return render_template(f"{TEMPLATE_DIR}/home.html")

@infoblox_ops.route("/")
def home_redirect():
    """ 
    Home Redirect 
    """
    return redirect(url_for("infoblox_ops.home"))


@infoblox_ops.route("/dhcp_csv_upload")
def dhcp_csv_upload():
    """ 
    DHCP Scopes Home Data input
    """
    Path("network_automation/infoblox_ops/add_dhcp/csv_data/").mkdir(exist_ok=True)
    return render_template(f"{TEMPLATE_DIR}/dhcp_csv_upload.html")


@infoblox_ops.route("/add_mac_bypass", methods=["POST"])
def add_dhcp_scope():
    if request.method == "POST":
        if "file" in request.files:
            success = "File Successfully Uploaded!"
            f = request.files["file"]
            current_app.config["UPLOAD_FOLDER"] = ISE_MAC_BYPASS_UPLOAD_DIR
            f.save(current_app.config["UPLOAD_FOLDER"] / secure_filename(f.filename))
            file_name = f.filename
            results = dhcp_add.add_scope()
            return str(results)
        else:
            return render_template(f"{TEMPLATE_DIR}/add_dhcp_upload_error.html")

    else:
        return "Unexpected Error"

### LOG FILE DOWNLOAD ###
@infoblox_ops.route("infoblox_log_file")
def infoblox_log_file():
    """ 
    Download Log File
    """
    return send_file(f'./../{str(LOG_FILE)}', as_attachment=True)


### ERROR & SUCCESS VIEWS ###

@infoblox_ops.route("/add_dhcp_upload.html")
def ise_mac_bypass_upload():
    return render_template(f"{TEMPLATE_DIR}/ise_mac_bypass_upload.html")

@infoblox_ops.route("/ise_auth_error")
def ise_auth_error():
    return render_template(f"{TEMPLATE_DIR}/ise_auth_error.html")

@infoblox_ops.route("/ise_mac_bypass_upload_error")
def ise_mac_bypass_upload_error():
    return render_template(f"{TEMPLATE_DIR}/ise_mac_bypass_upload_error.html")