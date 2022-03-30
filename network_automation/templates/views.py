#! /usr/bin/env python
"""
Creates the views (routes) for the secondary app
"""
from decouple import config
from flask import render_template, request, session, current_app, redirect, url_for
from pathlib import Path
from werkzeug.utils import secure_filename
from network_automation.ise_mac_bypass import ise_mac_bypass
import network_automation.ise_mac_bypass.mac_bypass.mac_bypass as bypass

### VARIABLES ###
FLASK_SECRET_KEY = config("FLASK_SECRET_KEY")
ISE_UPLOAD_DIR = Path("network_automation/ise_mac_bypass/mac_bypass/csv_data/")
template_dir = "ise_mac_bypass"

### VIEW TO CREATE DATA ###
@ise_mac_bypass.route("/home")
def home():
    return render_template(f"{template_dir}/home.html")

@ise_mac_bypass.route("/csv_upload")
def csv_upload():
    Path("network_automation/ise_mac_bypass/mac_bypass/csv_data/").mkdir(exist_ok=True)
    return render_template(f"{template_dir}/csv_upload.html")

@ise_mac_bypass.route("/manual_upload", methods = ['GET', 'POST'])
def manual_upload():
    return render_template(f"{template_dir}/manual_upload.html")

"""ROUTE THAT REQUESTS CREDENTIALS FOR ISE THIS 
   ROUTE HOLDS THE DATA INPUT VALUE AND CARRIES 
   IT TO THE del_ise_auth FUNCTION TO UPLOAD DATA"""
@ise_mac_bypass.route("/ise_login", methods = ['GET', 'POST'])
def ise_login():
    if request.method == 'GET':
        return render_template(f"{template_dir}/ise_login.html")
    if request.method == 'POST':
        if "file" in request.files:
            success = "File Successfully Uploaded!"
            f = request.files['file']
            current_app.config['UPLOAD_FOLDER'] = ISE_UPLOAD_DIR
            f.save(current_app.config['UPLOAD_FOLDER'] / secure_filename(f.filename))
            file_name = f.filename
            return render_template(f"{template_dir}/ise_login.html", file_name=file_name, success=success)
        else:
            text_data = request.form
            endpoint_list = []
            for text in text_data.items():
                if 'outputtext' in text:
                    success = "Data Captured!"
                    data_input = text[1]
                    data_input = data_input.replace("\n","").split("\r")
                    for data in data_input:
                        data = data.split(",")
                        if data != ['']:
                            endpoint = {}
                            mac_add = data[0]
                            dev_type = data[1]
                            endpoint["MAC Address"] = mac_add
                            endpoint["Device Type"] = dev_type
                            endpoint_list.append(endpoint)
            session["endpoint_list"] = endpoint_list
            print(f"Manual Input {endpoint_list}")
            return render_template(f"{template_dir}/ise_login.html", endpoint_list=endpoint_list)

@ise_mac_bypass.route("/ise_auth", methods = ['POST', 'GET'])
def ise_auth():
    if request.method == 'POST':
        if "username" in request.form:
            username=request.form['username']
            password=request.form['password']
            if not session.get("endpoint_list") is None:
                manual_data = session.get("endpoint_list")
                print(f"The manual data is: {manual_data}")
                result = bypass.mac_bypass(username, password, manual_data)
            else:
                result = bypass.mac_bypass(username, password)
            if result == 401:
                return redirect(url_for('ise_mac_bypass.ise_auth_error'))
            elif result == {201}:
                return redirect(url_for('ise_mac_bypass.ise_upload'))
            else: 
                return redirect(url_for('ise_mac_bypass.ise_upload_error'))

### VIEWS TO DELETE DATA ###
@ise_mac_bypass.route("/del_file_upload")
def del_file_upload():
    return render_template(f"{template_dir}/del_file_upload.html")

@ise_mac_bypass.route("/del_manual_upload", methods = ['GET', 'POST'])
def del_manual_upload():
    return render_template(f"{template_dir}/del_manual_upload.html")

"""ROUTE THAT REQUESTS CREDENTIALS FOR ISE 
   THIS ROUTE HOLDS THE DATA INPUT VALUE AND
   CARRIES IT TO THE del_ise_auth FUNCTION TO DELETE DATA"""
@ise_mac_bypass.route("/del_ise_login", methods = ['GET', 'POST'])
def del_ise_login():
    if request.method == 'GET':
        return render_template("del_ise_login.html")
    if request.method == 'POST':
        if "file" in request.files:
            success = "File Successfully Uploaded!"
            f = request.files['file']
            current_app.config['UPLOAD_FOLDER'] = ISE_UPLOAD_DIR
            f.save(current_app.config['UPLOAD_FOLDER'] / secure_filename(f.filename))
            file_name = f.filename
            return render_template(f"{template_dir}/del_ise_login.html", file_name=file_name, success=success)
        else:
            text_data = request.form
            mac_list = []
            for text in text_data.items():
                if 'outputtext' in text:
                    data_input = text[1]
                    data_input = data_input.replace("\n","").split("\r")
                    for mac in data_input:
                        if mac != '':
                            mac_list.append(mac)           
            session["mac_list"] = mac_list
            print(f"Manual Input {mac_list}")
            return render_template(f"{template_dir}/del_ise_login.html", mac_list=mac_list)

### GETS DATA INPUT FROM USER AND SUBMITS THE API CALLS TO ISE ###
@ise_mac_bypass.route("/del_ise_auth", methods = ['POST', 'GET'])
def del_ise_auth():
    if request.method == 'POST':
        if "username" in request.form:
            username=request.form['username']
            password=request.form['password']
            if not session.get("mac_list") is None:
                manual_data = session.get("mac_list")
                result = bypass.del_endpoints(username, password, manual_data)
            else:
                result = bypass.del_endpoints(username, password)
            if result == 401:
                return render_template(f"{template_dir}/ise_auth_error.html")
            elif result == {204}:
                return render_template(f"{template_dir}/ise_upload.html")
            else: 
                return render_template(f"{template_dir}/ise_upload_error.html")

### ERROR & SUCCESS VIEWS ###

@ise_mac_bypass.route("/ise_upload")
def ise_upload():
    return render_template(f"{template_dir}/ise_upload.html")

@ise_mac_bypass.route("/ise_auth_error")
def ise_auth_error():
    return render_template(f"{template_dir}/ise_auth_error.html")

@ise_mac_bypass.route("/ise_upload_error")
def ise_upload_error():
    return render_template(f"{template_dir}/ise_upload_error.html")