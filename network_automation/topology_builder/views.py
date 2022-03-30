#! /usr/bin/env python
"""
Creates the views (routes) for the secondary app
"""
from decouple import config
from flask import render_template, request, session, current_app, redirect, url_for
from pathlib import Path
from werkzeug.utils import secure_filename
from yaml import dump
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
    Path(GRAPHVIZ_UPLOAD_DIR).mkdir(exist_ok=True)
    return render_template(f"{template_dir}/yml_upload.html")

@topology_builder.route("/manual_upload", methods = ['GET', 'POST'])
def manual_upload():
    return render_template(f"{template_dir}/manual_upload.html")

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
            for text in text_data.items():
                if 'outputtext' in text:
                    success = "Data Captured!"
                    data_input = text[1]
                    data_input = data_input.replace("\n","").split("\r")
                    for data in data_input:
                        data = data.split(",")
                        if data != ['']:
                            print(f"The data from the textarea is {data}")
                            host = {}
                            hostname = data[0]
                            ip_add = data[1]
                            nos = data[2]
                            host[hostname] = {}
                            host[hostname]["groups"] = [nos + "_devices"]
                            host[hostname]["hostname"] = ip_add
            host_yaml = dump(host, default_flow_style=False)
            with open(GRAPHVIZ_UPLOAD_DIR / "hosts.yml", "w") as open_file:
                open_file.write(host_yaml)
            print(f"Manual Input {host_yaml}")
            return render_template(f"{template_dir}/tacacs_login.html", host=host)

@topology_builder.route("/tacacs_auth", methods = ['POST', 'GET'])
def tacacs_auth():
    if request.method == 'POST':
        if "username" in request.form:
            username=request.form['username']
            password=request.form['password']
            dev_failed = do_graph.graph_build(username, password)
            return render_template(f"{template_dir}/graph_upload.html", dev_failed=dev_failed)

### ERROR & SUCCESS VIEWS ###

@topology_builder.route("/graph_upload")
def graph_upload():
    return render_template(f"{template_dir}/graph_upload.html")

@topology_builder.route("/tacacs_auth_error")
def tacacs_auth_error():
    return render_template(f"{template_dir}/tacacs_auth_error.html")

@topology_builder.route("/upload_error")
def upload_error():
    return render_template(f"{template_dir}/upload_error.html")