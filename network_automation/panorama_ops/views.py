#! /usr/bin/env python
"""
Creates the views (routes) for the secondary app
"""
from decouple import config
from flask import render_template, request, session, current_app, redirect, send_file, url_for
from pathlib import Path
from werkzeug.utils import secure_filename
from network_automation.panorama_ops import panorama_ops
import network_automation.panorama_ops.address_checker.address_checker as address_checking_script
import network_automation.panorama_ops.services_checker.services_checker as service_checking_script
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
def address_checker_flask():
    return render_template(f"{TEMPLATE_DIR}/address_checker.html")

@panorama_ops.route("/service_checker", methods=["POST", "GET"])
def service_checker_flask():
    return render_template(f"{TEMPLATE_DIR}/services_checker.html")

@panorama_ops.route("address_check_API_call", methods=["POST"])
def address_check_API_call():
    """ 
    Launch address Checking script
    """
    if request.method == "POST":
        text_data = request.form
        temp=''
        for text in text_data.items():
            if "outputtext" in text:
                data_input = text[1]
                temp=data_input
                script_output =  address_checking_script.panorama_address_check(str(data_input))
    if script_output is None:
        return render_template(f"{TEMPLATE_DIR}/address_checker.html", results="No AddGroup named "+ temp) 
    else:
        return render_template(f"{TEMPLATE_DIR}/address_checker.html", results=script_output)
@panorama_ops.route("service_check_API_call", methods=["POST"])
def service_check_API_call():
    """ 
    Launch service Checking script
    """
    if request.method == "POST":
        text_data = request.form
        temp=''
        for text in text_data.items():
            if "outputtext" in text:
                data_input = text[1]
                temp=data_input
                script_output =  service_checking_script.panorama_services_check(str(data_input))
    if script_output is None:
        return render_template(f"{TEMPLATE_DIR}/services_checker.html", results="No ServiceGroup named "+ temp) 
    else:
        return render_template(f"{TEMPLATE_DIR}/services_checker.html", results=script_output)
