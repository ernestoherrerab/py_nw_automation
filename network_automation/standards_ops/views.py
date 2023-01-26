#! /usr/bin/env python
"""
Creates the views (routes) for the secondary app
"""
from decouple import config
from flask import render_template, request, redirect, send_file, session, url_for
import logging
from pathlib import Path
from yaml import dump
from network_automation.standards_ops import standards_ops
import network_automation.standards_ops.audit_manager.audit as audit
import network_automation.standards_ops.aaa.build_inventory as do_aaa
import network_automation.standards_ops.ntp.build_inventory as do_ntp

### LOGGING SETUP ###
LOG_FILE = Path("logs/standards_ops.log")
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler(LOG_FILE)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

### VARIABLES ###
FLASK_SECRET_KEY = config("FLASK_SECRET_KEY")
AUDIT_MANAGER_INV_DIR = Path("network_automation/standards_ops/inventory/")
TEMPLATE_DIR = "standards_ops"
LOG_FILE = Path("logs/standards_ops.log")

### VIEW TO CREATE DATA ###
@standards_ops.route("/home")
def home():
    return render_template(f"{TEMPLATE_DIR}/home.html")

@standards_ops.route("/")
def home_redirect():
    return redirect("/home")

@standards_ops.route("/cli_auth", methods=["POST"])
def cli_auth():
    """ 
    Login Page 
    """
    if request.method == "POST":
        session["cli_username"] = request.form["cli_username"]
        session["cli_password"] = request.form["cli_password"]
        return redirect(url_for("standards_ops.ops"))

@standards_ops.route("/ops")
def ops():
    """ 
    Select CLI Operation to perform
    """
    return render_template(f"{TEMPLATE_DIR}/ops.html")

@standards_ops.route("/audit_manager")
def audit_manager():
    """ 
    Audit Manager Home Data input
    """
    return render_template(f"{TEMPLATE_DIR}/audit_manager.html")

@standards_ops.route("/aaa_manager")
def aaa_manager():
    """ 
    AAA Manager Home Data input
    """
    return render_template(f"{TEMPLATE_DIR}/aaa_manager.html")

@standards_ops.route("/ntp_manager")
def ntp_manager():
    """ 
    NTP Manager Home Data input
    """
    return render_template(f"{TEMPLATE_DIR}/ntp_manager.html")

@standards_ops.route("/aaa")
def aaa():
    """ 
    Apply AAA Standards Home Data input
    """
    return render_template(f"{TEMPLATE_DIR}/aaa_manager.html")

@standards_ops.route("/ntp")
def ntp():
    """ 
    Apply NTP Standards Home Data input
    """
    return render_template(f"{TEMPLATE_DIR}/ntp_manager.html")

@standards_ops.route("/do_audit", methods=["POST"])
def do_audit():
    if request.method == "POST":
        text_data = request.form
        username = session.get("cli_username")
        password = session.get("cli_password")
        for text in text_data.items():
            if "outputtext" in text:
                data_input = text[1]
                data_input = data_input.replace("\n", "").split("\r")
                for data in data_input:
                    data = data.split(",")
                    if data != [""]:
                        core_switch = {}
                        hostname = data[0]
                        ip_add = data[1]
                        nos = data[2]
                        site_id = hostname.split("-")
                        site_id = site_id[0]
                        depth_levels = int(data[3])
                        core_switch[hostname] = {}
                        core_switch[hostname]["groups"] = [nos + "_devices"]
                        core_switch[hostname]["hostname"] = ip_add
        
        ### GENERATE DIRECTORY STRUCTURE ###
        Path("file_display/public/documentation").mkdir(exist_ok=True)
        Path(f"file_display/public/documentation/{site_id}").mkdir(exist_ok=True)
        Path(f"file_display/public/documentation/{site_id}/run_config").mkdir(exist_ok=True)
        Path(f"file_display/public/documentation/{site_id}/audits").mkdir(exist_ok=True)
        ### BUILD INITIAL NORNIR INVENTORY FILE ###
        host_yaml = dump(core_switch, default_flow_style=False)
        with open(AUDIT_MANAGER_INV_DIR / "hosts.yml", "w") as open_file:
            open_file.write(host_yaml)
        audit.do_audit(username, password, depth_levels)
        return render_template(f"{TEMPLATE_DIR}/audit_results.html")
        
@standards_ops.route("/apply_aaa", methods=["POST"])
def apply_aaa():
    if request.method == "POST":
        Path(f"network_automation/standards_ops/staging").mkdir(exist_ok=True)
        site_code = request.form["siteId"]
        username = session.get("cli_username")
        password = session.get("cli_password")
        logger.info(f'Applying AAA standards to {site_code}')
        results, failed_hosts = do_aaa.build_inventory(site_code, username, password)
        print(results, failed_hosts)
       
        if results == {True}:
            return render_template(f"{TEMPLATE_DIR}/results_success.html")
        else:
            return render_template(f"{TEMPLATE_DIR}/results_failure.html", failed_hosts=failed_hosts)

@standards_ops.route("/apply_ntp", methods=["POST"])
def apply_ntp():
    if request.method == "POST":
        Path(f"network_automation/standards_ops/staging").mkdir(exist_ok=True)
        ntp_text_data = request.form
        for text in ntp_text_data.items():
            if "outputtext" in text:
                ntp_data_input = text[1]
                ntp_data_input = ntp_data_input.replace("\n", "").split("\r")
                for ntp_data in ntp_data_input:
                    ntp_data = ntp_data.split(",")
                    if ntp_data != [""]:
                        site_code = ntp_data[0]
                        time_zone = ntp_data[1]
                        dls_zone = ntp_data[2]
                        offset = ntp_data[3]
                        ntp_dict = {}
                        ntp_dict["site_code"] = site_code
                        ntp_dict["time_zone"] = time_zone
                        ntp_dict["daylight_zone"] = dls_zone
                        ntp_dict["offset"] = offset
        username = session.get("cli_username")
        password = session.get("cli_password")
        logger.info(f'Applying NTP standards to {site_code}')
        results, failed_hosts = do_ntp.build_inventory(ntp_dict, username, password)
        print(results, failed_hosts)
       
        if results == {True}:
            return render_template(f"{TEMPLATE_DIR}/results_success.html")
        else:
            return render_template(f"{TEMPLATE_DIR}/results_failure.html", failed_hosts=failed_hosts)

@standards_ops.route("standards_log_file")
def standards_log_file():
    """ 
    Download Log File
    """
    return send_file(f'./../{str(LOG_FILE)}', as_attachment=True)

### ERROR & SUCCESS VIEWS ###
@standards_ops.route("/audit_results_success")
def audit_results():
    return render_template(f"{TEMPLATE_DIR}/audit_results_success.html")

@standards_ops.route("/results_success")
def results_success():
    return render_template(f"{TEMPLATE_DIR}/results_success.html")

@standards_ops.route("/results_failure")
def results_failure():
    return render_template(f"{TEMPLATE_DIR}/results_failure.html")