#! /usr/bin/env python
"""
Creates the views (routes) for the secondary app
"""
from decouple import config
from flask import render_template, request, send_file, redirect
import logging
from pathlib import Path
from network_automation.lifecycle import lifecycle
import network_automation.lifecycle.lifecycle_data as get_lifecycle



### VARIABLES ###
FLASK_SECRET_KEY = config("FLASK_SECRET_KEY")
template_dir = "lifecycle"

### LOGGING SETUP ###
LOG_FILE = Path("logs/lifecycle.log")
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler(LOG_FILE)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

### VIEW TO CREATE DATA ###
@lifecycle.route("/home")
def home():
    return render_template(f"{template_dir}/home.html")

@lifecycle.route("/")
def home_redirect():
    return redirect("/home")


@lifecycle.route("/get_lifecycle_data", methods=["POST"])
def get_lifecycle_data():
    if request.method == "POST":
        logger.info(f'Generating report')
        print(f'Generating report')
        get_lifecycle.build_lifecycle_report(True)

        return send_file(f'./lifecycle/archive/eol_summary.xlsx', as_attachment=True)

@lifecycle.route("/get_lifecycle_diff", methods=["POST"])
def get_lifecycle_diff():
    if request.method == "POST":
        logger.info(f'Generating differential report')
        print(f'Generating differential report')
        get_lifecycle.build_lifecycle_diff()

    return send_file(f'./lifecycle/archive/differential.xlsx', as_attachment=True)
        

### ERROR & SUCCESS VIEWS ###

@lifecycle.route("lifecycle_log_file")
def standards_log_file():
    """ 
    Download Log File
    """
    return send_file(f'./../{str(LOG_FILE)}', as_attachment=True)
