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

@panorama_ops.route("API_calls", methods=["POST"])
def API_calls():
    """ 
    Launch Prisma Access Tunnels Provisioning 
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


    # if request.method == "POST":
    #     username = session.get("username")
    #     password = session.get("password")
    #     text_data = request.form
    #     for text in text_data.items():
    #         if "outputtext" in text:
    #             data_input = text[1]
    #             data_input = data_input.replace("\n", "").split("\r")
    #             for data in data_input:
    #                 data = data.split(",")
    #                 if data != [""]:
    #                     site_data = {}
    #                     site_code = data[0]
    #                     region_id = data[1]
    #                     location_id = data[2]
    #                     site_data["site_code"] = site_code
    #                     site_data["region_id"] = region_id
    #                     site_data["location_id"] = location_id
    # else:
    #     return "Unexpected Error"



### LOG FILE DOWNLOAD ###
@panorama_ops.route("ise_log_file")
def ise_log_file():
    """ 
    Download Log File
    """
    return send_file(f'./../{str(LOG_FILE)}', as_attachment=True)



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