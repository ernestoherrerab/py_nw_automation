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
import network_automation.panorama_ops.policy_dissect.policy_dissect as policy_dissecting_script
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

@panorama_ops.route("/policy_dissect", methods=["POST", "GET"])
def policy_dissect_flask():
    return render_template(f"{TEMPLATE_DIR}/policy_dissect.html")

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
@panorama_ops.route("policy_dissect_API_call", methods=["POST"])
def policy_dissect_API_call():
    def recursion_string(input):
        string_output=''
        for source in input:
            if type(source)!=list:
                string_output = string_output+ source + '\n'
            else:
                string_output = string_output + recursion_string(source) 
        return string_output
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
                script_output =  policy_dissecting_script.policy_dissect(str(data_input))

        outputDict =	{
        "name": script_output['name'],
        "source": [] ,
        "destination": [] ,
        "application": [] ,
        "service": []
        } 
        for source in script_output['source']:
            for IP in address_checking_script.panorama_address_check_IP(source):
                outputDict['source'].append(IP)
        for destination in script_output['destination']:
            for IP in address_checking_script.panorama_address_check_IP(destination):
                outputDict['destination'].append(IP)

        for application in script_output['application']:
                outputDict['application'].append(application)

        for service in script_output['service']:
            
            for SRV in service_checking_script.panorama_service_check_ports(service):
                outputDict['service'].append(SRV)                                
        script_output=outputDict
    if script_output is None:
        return render_template(f"{TEMPLATE_DIR}/policy_dissect.html", results="No ServiceGroup named "+ temp) 
    else:
        result=['','','','']
       
        result[0]=recursion_string(script_output['source'])
        result[1]=recursion_string(script_output['destination'])
        result[2]=recursion_string(script_output['application'])
        result[3]=recursion_string(script_output['service'])

        return render_template(f"{TEMPLATE_DIR}/policy_dissect.html", results=result)
