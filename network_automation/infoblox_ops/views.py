#! /usr/bin/env python
"""
Creates the views (routes) for the secondary app
"""
from decouple import config
from flask import render_template, request, current_app, redirect, send_file, url_for
from pathlib import Path
from werkzeug.utils import secure_filename
from network_automation.infoblox_ops import infoblox_ops
import logging
import network_automation.infoblox_ops.dhcp.dhcp as dhcp_add

### VARIABLES ###
FLASK_SECRET_KEY = config("FLASK_SECRET_KEY")
INFOBLOX_UPLOAD_DIR = Path("network_automation/infoblox_ops/dhcp/csv_data/")
TEMPLATE_DIR = "infoblox_ops"

### LOGGING SETUP ###
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
    INFOBLOX_UPLOAD_DIR.mkdir(exist_ok=True)
    return render_template(f"{TEMPLATE_DIR}/dhcp_csv_upload.html")


@infoblox_ops.route("/add_dhcp_scope", methods=["POST"])
def add_dhcp_scope():
    if request.method == "POST":
        if "file" in request.files:
            print(f'CSV File Successfully Uploaded')
            f = request.files["file"]
            current_app.config["UPLOAD_FOLDER"] = INFOBLOX_UPLOAD_DIR
            f.save(current_app.config["UPLOAD_FOLDER"] / secure_filename(f.filename))
            file_name = INFOBLOX_UPLOAD_DIR / f.filename
            results = dhcp_add.add_scope(file_name)

            if False in results:
                error_string = results[1]
                return render_template(f'{TEMPLATE_DIR}/infoblox_error.html', error_string=error_string)
            else:
                return render_template(f'{TEMPLATE_DIR}/infoblox_success.html')
        else:
            return render_template(f"{TEMPLATE_DIR}/csv_upload_error.html")
    else:
        return render_template(f"{TEMPLATE_DIR}/csv_upload_error.html")



### LOG FILE DOWNLOAD ###
@infoblox_ops.route("infoblox_log_file")
def infoblox_log_file():
    """ 
    Download Log File
    """
    return send_file(f'./../{str(LOG_FILE)}', as_attachment=True)


### ERROR & SUCCESS VIEWS ###
@infoblox_ops.route("/csv_upload_error")
def csv_upload_error():
    return render_template(f"{TEMPLATE_DIR}/csv_upload_error.html")