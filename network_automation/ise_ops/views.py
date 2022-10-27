#! /usr/bin/env python
"""
Creates the views (routes) for the secondary app
"""
from decouple import config
from flask import render_template, request, session, current_app, redirect, send_file, url_for
from pathlib import Path
from werkzeug.utils import secure_filename
from network_automation.ise_ops import ise_ops
import network_automation.ise_ops.mac_bypass.mac_bypass as bypass

### VARIABLES ###
FLASK_SECRET_KEY = config("FLASK_SECRET_KEY")
ISE_MAC_BYPASS_UPLOAD_DIR = Path("network_automation/ise_ops/mac_bypass/csv_data/")
TEMPLATE_DIR = "ise_ops"
LOG_FILE = Path("logs/ise_ops.log")

### ISE OPS HOME ###
@ise_ops.route("/home")
def home():
    """ 
    Home Page
    """
    return render_template(f"{TEMPLATE_DIR}/home.html")

@ise_ops.route("/")
def home_redirect():
    """ 
    Home Redirect 
    """
    return redirect(url_for("ise_ops.home"))

@ise_ops.route("/ise_auth", methods=["POST", "GET"])
def ise_auth():
    """ 
    Login Page 
    """
    if request.method == "POST":
        username = request.form["ise_username"]
        password = request.form["ise_password"]
        session["ise_username"] = username
        session["ise_password"] = password
        return redirect(url_for("ise_ops.ops"))

@ise_ops.route("/ops")
def ops():
    """ 
    Select ISE Operation to perform
    """
    return render_template(f"{TEMPLATE_DIR}/ops.html")

@ise_ops.route("/mac_bypass")
def mac_bypass():
    """ 
    MAC Bypass Home Data input
    """
    return render_template(f"{TEMPLATE_DIR}/mac_bypass.html")

@ise_ops.route("/mac_bypass_csv_upload")
def mac_bypass_csv_upload():
    """ CSV Upload Data Input
    """
    Path("network_automation/ise_ops/mac_bypass/csv_data/").mkdir(exist_ok=True)
    return render_template(f"{TEMPLATE_DIR}/mac_bypass_csv_upload.html")

@ise_ops.route("/mac_bypass_manual_upload", methods=["GET", "POST"])
def mac_bypass_manual_upload():
    """ Manual Data Input
    """
    return render_template(f"{TEMPLATE_DIR}/mac_bypass_manual_upload.html")

"""ROUTE THAT REQUESTS CREDENTIALS FOR ISE THIS 
   ROUTE HOLDS THE DATA INPUT VALUE AND CARRIES 
   IT TO THE del_ise_auth FUNCTION TO UPLOAD DATA"""

@ise_ops.route("/ise_login", methods=["POST"])
def add_mac_bypass():
    if request.method == "POST":
        username = session.get("ise_username")
        password = session.get("ise_password")
        if "file" in request.files:
            success = "File Successfully Uploaded!"
            f = request.files["file"]
            current_app.config["UPLOAD_FOLDER"] = ISE_MAC_BYPASS_UPLOAD_DIR
            f.save(current_app.config["UPLOAD_FOLDER"] / secure_filename(f.filename))
            file_name = f.filename
            results = bypass.mac_bypass(username, password)
            return str(results)
        else:
            text_data = request.form
            endpoint_list = []
            for text in text_data.items():
                if "outputtext" in text:
                    success = "Data Captured!"
                    data_input = text[1]
                    data_input = data_input.replace("\n", "").split("\r")
                    for data in data_input:
                        data = data.split(",")
                        if data != [""]:
                            endpoint = {}
                            mac_add = data[0]
                            dev_type = data[1]
                            endpoint["mac_address"] = mac_add
                            endpoint["dev_type"] = dev_type
                            endpoint_list.append(endpoint)

            ### ADD MAC ADDRESSES TO BYPASS LIST ###
            print(f'Manual Input {endpoint_list}')
            results = bypass.mac_bypass(username, password, endpoint_list) 
            if results == {201}:
                return render_template(f"{TEMPLATE_DIR}/ise_mac_bypass_upload.html")
            else:
                return render_template(f"{TEMPLATE_DIR}/ise_mac_bypass_upload_error.html")
    else:
        return "Unexpected Error"

### LOG FILE DOWNLOAD ###
@ise_ops.route("ise_log_file")
def ise_log_file():
    """ 
    Download Log File
    """
    return send_file(f'./../{str(LOG_FILE)}', as_attachment=True)


### VIEWS TO DELETE DATA ###
@ise_ops.route("/del_file_upload")
def del_file_upload():
    return render_template(f"{TEMPLATE_DIR}/del_file_upload.html")

@ise_ops.route("/del_manual_upload", methods=["GET", "POST"])
def del_manual_upload():
    return render_template(f"{TEMPLATE_DIR}/del_manual_upload.html")

"""ROUTE THAT REQUESTS CREDENTIALS FOR ISE 
   THIS ROUTE HOLDS THE DATA INPUT VALUE AND
   CARRIES IT TO THE del_ise_auth FUNCTION TO DELETE DATA"""

@ise_ops.route("/del_ise_login", methods=["GET", "POST"])
def del_ise_login():
    if request.method == "GET":
        return render_template("del_ise_login.html")
    if request.method == "POST":
        if "file" in request.files:
            success = "File Successfully Uploaded!"
            f = request.files["file"]
            current_app.config["UPLOAD_FOLDER"] = ISE_MAC_BYPASS_UPLOAD_DIR
            f.save(current_app.config["UPLOAD_FOLDER"] / secure_filename(f.filename))
            file_name = f.filename
            return render_template(
                f"{TEMPLATE_DIR}/del_ise_login.html",
                file_name=file_name,
                success=success,
            )
        else:
            text_data = request.form
            mac_list = []
            for text in text_data.items():
                if "outputtext" in text:
                    data_input = text[1]
                    data_input = data_input.replace("\n", "").split("\r")
                    for mac in data_input:
                        if mac != "":
                            mac_list.append(mac)
            session["mac_list"] = mac_list
            print(f"Manual Input {mac_list}")
            return render_template(
                f"{TEMPLATE_DIR}/del_ise_login.html", mac_list=mac_list
            )

### GETS DATA INPUT FROM USER AND SUBMITS THE API CALLS TO ISE ###
@ise_ops.route("/del_ise_auth", methods=["POST", "GET"])
def del_ise_auth():
    if request.method == "POST":
        if "username" in request.form:
            username = request.form["username"]
            password = request.form["password"]
            if not session.get("mac_list") is None:
                manual_data = session.get("mac_list")
                result = bypass.del_endpoints(username, password, manual_data)
            else:
                result = bypass.del_endpoints(username, password)
            if result == 401:
                return render_template(f"{TEMPLATE_DIR}/ise_auth_error.html")
            elif result == {204}:
                return render_template(f"{TEMPLATE_DIR}/ise_upload.html")
            else:
                return render_template(f"{TEMPLATE_DIR}/ise_upload_error.html")


### ERROR & SUCCESS VIEWS ###

@ise_ops.route("/ise_mac_bypass_upload.html")
def ise_mac_bypass_upload():
    return render_template(f"{TEMPLATE_DIR}/ise_mac_bypass_upload.html")

@ise_ops.route("/ise_auth_error")
def ise_auth_error():
    return render_template(f"{TEMPLATE_DIR}/ise_auth_error.html")

@ise_ops.route("/ise_mac_bypass_upload_error")
def ise_mac_bypass_upload_error():
    return render_template(f"{TEMPLATE_DIR}/ise_mac_bypass_upload_error.html")