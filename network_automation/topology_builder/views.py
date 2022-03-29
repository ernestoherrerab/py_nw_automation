#! /usr/bin/env python
"""
Creates the views (routes) for the secondary app
"""
from decouple import config
from flask import render_template, request, session, current_app, redirect, url_for
from pathlib import Path
from werkzeug.utils import secure_filename
from network_automation.topology_builder import topology_builder
import network_automation.topology_builder.graphviz.recursive_graph as do_graph

### VARIABLES ###
FLASK_SECRET_KEY = config("FLASK_SECRET_KEY")
GRAPHVIZ_UPLOAD_DIR = Path("network_automation/topology_builder/graphviz/inventory/")
template_dir = "topology_builder"

### VIEW TO CREATE DATA ###
@topology_builder.route("/home")
def home():
    return render_template(f"{template_dir}/home.html")

@topology_builder.route("/yml_upload")
def yml_upload():
    Path("network_automation/topology_builder/graphviz/inventory/").mkdir(exist_ok=True)
    return render_template(f"{template_dir}/yml_upload.html")

@topology_builder.route("/tacacs_login", methods = ['GET', 'POST'])
def tacacs_login():
    if request.method == 'GET':
        return render_template(f"{template_dir}/tacacs_login.html")
    if request.method == 'POST':
        if "file" in request.files:
            success = "File Successfully Uploaded!"
            f = request.files['file']
            current_app.config['UPLOAD_FOLDER'] = GRAPHVIZ_UPLOAD_DIR
            f.save(current_app.config['UPLOAD_FOLDER'] / secure_filename(f.filename))
            file_name = f.filename
            return render_template(f"{template_dir}/tacacs_login.html", file_name=file_name, success=success)
        else:
            text_data = request.form
            host_list = []
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
                            host_list.append(endpoint)
            session["host_list"] = host_list
            print(f"Manual Input {host_list}")
            return render_template(f"{template_dir}/tacacs_login.html", host_list=host_list)

@topology_builder.route("/tacacs_auth", methods = ['POST', 'GET'])
def tacacs_auth():
    if request.method == 'POST':
        if "username" in request.form:
            username=request.form['username']
            password=request.form['password']
            if not session.get("host_list") is None:
                manual_data = session.get("endpoint_list")
                print(f"The manual data is: {manual_data}")
                return redirect(url_for('topology_builder.ise_auth_error'))
            else:
                do_graph.graph_build(username, password)
                return redirect(url_for('topology_builder.graph_upload'))
#            else:
#                result = bypass.mac_bypass(username, password)
#            if result == 401:
#                return redirect(url_for('ise_mac_bypass.ise_auth_error'))
#            elif result == {201}:
#                return redirect(url_for('ise_mac_bypass.ise_upload'))
#            else: 
#                return redirect(url_for('ise_mac_bypass.ise_upload_error'))

### ERROR & SUCCESS VIEWS ###

@topology_builder.route("/graph_upload")
def graph_upload():
    return render_template(f"{template_dir}/graph_upload.html")