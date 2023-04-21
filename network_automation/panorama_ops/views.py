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
import network_automation.panorama_ops.address_objects_editor.address_objects_editor as panorama_address
import network_automation.panorama_ops.services_checker.services_checker as service_checking_script
import network_automation.panorama_ops.policy_dissect.policy_dissect as policy_dissecting_script

### VARIABLES ###
FLASK_SECRET_KEY = config("FLASK_SECRET_KEY")
TEMPLATE_DIR = "panorama_ops"
LOG_FILE = Path("logs/panorama_ops.log")
PANORAMA_ADDRESS_OBJECTS_UPLOAD_DIR = Path("network_automation/panorama_ops/address_objects_editor/csv_data/")

### PANORAMA OPS HOME ###
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
def address_checker():
    return render_template(f"{TEMPLATE_DIR}/address_checker.html")

@panorama_ops.route("/service_checker", methods=["POST", "GET"])
def service_checker():
    return render_template(f"{TEMPLATE_DIR}/services_checker.html")

@panorama_ops.route("/policy_dissect", methods=["POST", "GET"])
def policy_dissect():
    return render_template(f"{TEMPLATE_DIR}/policy_dissect.html")

@panorama_ops.route("/panorama_login")
def panorama_login():
    return render_template(f"{TEMPLATE_DIR}/panorama_login.html")

@panorama_ops.route("/panorama_auth", methods=["POST"])
def panorama_auth():
    """ 
    Login Page 
    """
    if request.method == "POST":
        username = request.form["panorama_username"]
        password = request.form["panorama_password"]
        session["panorama_username"] = username
        session["panorama_password"] = password
        return render_template(f"{TEMPLATE_DIR}/address_objects.html")

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
            if source is not None:
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

"""Address Objects Manipulation Functions
"""
### VIEWS TO CREATE DATA ###

@panorama_ops.route("/address_objects_csv_upload")
def address_objects_csv_upload():
    """Route for uploading CSV data for address objects.

    Creates a directory for storing CSV data if it does not already exist, and returns
    the address_objects_csv_upload.html template.

    Returns:
        str: The rendered HTML template for the CSV upload page.
    """

    # CREATE DIRECTORY FOR STORTING CSV DATA IF IT DOES NOT ALREADY EXIST
    Path(PANORAMA_ADDRESS_OBJECTS_UPLOAD_DIR).mkdir(exist_ok=True)

    # RETURN THE TEMPLATE
    return render_template(f"{TEMPLATE_DIR}/address_objects_csv_upload.html")

@panorama_ops.route("/address_objects_manual_upload", methods=["GET", "POST"])
def address_objects_manual_upload():
    """
    Renders the address objects manual upload page.

    Returns:
        rendered HTML template: The HTML template for the address objects manual upload page.
    """

    return render_template(f"{TEMPLATE_DIR}/address_objects_manual_upload.html")

@panorama_ops.route("/add_address_objects", methods=["POST"])
def add_address_objects():
    if request.method == "POST":
        username = session.get("panorama_username")
        password = session.get("panorama_password")
        if "file" in request.files:
            f = request.files["file"]
            current_app.config["UPLOAD_FOLDER"] = PANORAMA_ADDRESS_OBJECTS_UPLOAD_DIR
            f.save(current_app.config["UPLOAD_FOLDER"] / secure_filename(f.filename))
            results = panorama_address.add_address_object(username, password)
            return str(results)
        else:
            text_data = request.form
            address_object_list = []
            for text in text_data.items():
                if "outputtext" in text:
                    data_input = text[1]
                    data_input = data_input.replace("\n", "").split("\r")
                    for data in data_input:
                        data = data.split(",")
                        if data != [""]:
                            address_object = {}
                            object_name = data[0]
                            object_value = data[1]
                            object_type = data[2]
                            object_description = data[3]
                            address_object["obj_name"] = object_name
                            address_object["obj_value"] = object_value
                            address_object["obj_type"] = object_type
                            address_object["obj_desc"] = object_description
                            address_object_list.append(address_object)

            ### ADD MAC ADDRESSES TO BYPASS LIST ###
            print(f'Manual Input {address_object_list}')
            panorama_address.add_address_object(username, password, address_object_list)
            return render_template(f"{TEMPLATE_DIR}/panorama_address_object_upload.html")

    else:
        return "Unexpected Error"

### VIEWS TO DELETE DATA ###

@panorama_ops.route("/address_objects_del_csv_upload")
def address_objects_del_csv_upload():
    """
    Renders the address objects delete CSV upload page.

    Returns:
        rendered HTML template: The HTML template for the address objects delete CSV upload page.
    """

    # CREATE DIRECTORY FOR STORTING CSV DATA IF IT DOES NOT ALREADY EXIST
    Path(PANORAMA_ADDRESS_OBJECTS_UPLOAD_DIR).mkdir(exist_ok=True)

    return render_template(f"{TEMPLATE_DIR}/address_objects_del_csv_upload.html")

@panorama_ops.route("/address_objects_del_manual_upload", methods=["GET", "POST"])
def address_objects_del_manual_upload():
    """
    Renders the address objects deletion manual upload page.

    If the request method is GET, returns the template for the manual upload page.
    If the request method is POST, expects a form submission with the address objects data to delete.
    """
        
    return render_template(f"{TEMPLATE_DIR}/address_objects_del_manual_upload.html")

### LOG FILE DOWNLOAD ###
@panorama_ops.route("panorama_log_file")
def panorama_log_file():
    """ 
    Download Log File
    """
    return send_file(f'./../{str(LOG_FILE)}', as_attachment=True)

### ERROR & SUCCESS VIEWS ###

@panorama_ops.route("/panorama_address_object_upload")
def panorama_address_object_upload():
    return render_template(f"{TEMPLATE_DIR}/panorama_address_object_upload.html")