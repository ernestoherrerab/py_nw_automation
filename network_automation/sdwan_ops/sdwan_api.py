#! /usr/bin/env python
"""
SDWAN API Functions
"""
import logging
from pathlib import Path
from vmanage.api.authentication import Authentication
from vmanage.api.device import Device
from vmanage.api.device_templates import DeviceTemplates
from vmanage.api.feature_templates import FeatureTemplates

import network_automation.sdwan_ops.api_calls as api
from network_automation.sdwan_ops.ViptelaAuthentication import ViptelaAuthentication


### LOGGING SETUP ###
LOG_FILE = Path("logs/tunnel_provision.log")
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler(LOG_FILE)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

def auth(vmanage, username, password):
    """ 
    Authenticate vManage
    """
    auth = Authentication(host=vmanage, port=8443,user=username,password=password).login()

    return auth

def attach_dev_template(authentication, vmanage, payload, config_type="template"):
    """
    Attach template to device
    """
    device_template = DeviceTemplates(authentication, vmanage)
    response =  device_template.attach_to_template(payload, config_type)
    return response


def clone_template(authentication, vmanage, template_dict):
    device_template = DeviceTemplates(authentication, vmanage)
    try:
        response =  device_template.add_device_template(template_dict) 
        return response
    except Exception as e:
        print("Something went wrong")
        return e

def get_all_templates_config(authentication, vmanage, templates_names=None):
    """ 
    Get templates information for all or specific templates 
    """
    device_template = DeviceTemplates(authentication, vmanage)
    device_templates_list = device_template.get_device_template_list(name_list=templates_names)
    return device_templates_list

def get_dev_feature_template(authentication, vmanage, factory_default=False, name_list=None):
    """ 
    Get feature templates data to specific template
    """
    feature_template = FeatureTemplates(authentication, vmanage)
    feature_template_list = feature_template.get_feature_template_list(factory_default, name_list)
    return feature_template_list

def get_template_config(authentication, vmanage, template_id):
    """ 
    Get Reachable vEdge Data 
    """
    device_templates = DeviceTemplates(authentication, vmanage)
    device_templates_list = device_templates.get_device_template_object(template_id)
    return device_templates_list

def get_template_input(authentication, vmanage, template_id, dev_id_list=None):
    """ 
    Get the template input data 
    """
    device_input = DeviceTemplates(authentication, vmanage)
    device_input_list = device_input.get_template_input(template_id, dev_id_list)
    return device_input_list


def get_vedge_list(authentication, vmanage):
    """ 
    Get Reachable vEdge Data 
    """
    vmanage_device = Device(authentication, vmanage)
    device_config_list = vmanage_device.get_device_config_list("vedges")
    return device_config_list


def host_template_mapping(input_dict):
    """ 
    Generate Host to Template Mapping 
    """
    ### GENERATE FORMATTED PAYLOAD FOR DEVICE INPUT API CALL ###
    output_list = []
    for host_template in input_dict:
        output_dict = {}
        if "templateId" in host_template and "host-name" in host_template:
            output_dict["deviceIP"] = host_template["deviceIP"]
            output_dict["host-name"] = host_template["host-name"]
            output_dict["templateId"] = host_template["templateId"]
            output_dict["deviceIds"] = [host_template["uuid"]]
            output_dict["isEdited"] = False
            output_dict["isMasterEdited"] = False
            output_list.append(output_dict)
    return output_list

#def get_template_config(authentication, vmanage):
#    """ Get Reachable vEdge Data """
#
#    device_templates = DeviceTemplates(authentication, vmanage)
#    device_templates_list = device_templates.get_device_templates()
#    return device_templates_list

#def auth(vmanage, username, password):
#    """ Authenticate vManage"""
#    
#    jsessionid = ViptelaAuthentication.get_jsessionid(vmanage, username, password)
#    token = ViptelaAuthentication.get_token(vmanage, jsessionid)
#
#    if token is not None:
#        header = {'Content-Type': "application/json",'Cookie': jsessionid, 'X-XSRF-TOKEN': token}
#        return header
#    else:
#        header = {'Content-Type': "application/json",'Cookie': jsessionid}
#        return header
#
#def get_dev_data(url_var, operation, header):
#    """ Get Reachable vEdge Data """
#
#    data = api.get_operations(operation, url_var, header)
#    
#    ### FILTER DEVICES - ONLY REACHABLE ###
#    #filtered_data = [online_dev for online_dev in data["data"] if "system-ip" in online_dev and online_dev["system-ip"] == "10.61.112.133"]
#    filtered_data = [online_dev for online_dev in data["data"] if "reachability" in online_dev and online_dev["reachability"] == "reachable"]
#    data["data"] = filtered_data 
#    
#    return data
#
#def host_template_mapping(input_dict):
#    """ Generate Host to Template Mapping """
#
#    ### GENERATE FORMATTED PAYLOAD FOR DEVICE INPUT API CALL ###
#    output_list = []
#    for host_template in input_dict["data"]:
#        output_dict = {}
#        if "templateId" in host_template and "host-name" in host_template:
#            output_dict["deviceIP"] = host_template["deviceIP"]
#            output_dict["host-name"] = host_template["host-name"]
#            output_dict["templateId"] = host_template["templateId"]
#            output_dict["deviceIds"] = [host_template["uuid"]]
#            output_dict["isEdited"] = False
#            output_dict["isMasterEdited"] = False
#            output_list.append(output_dict)
#    return output_list
#
#def create_device_input(input_list, url_var, operation, header):
#    """ Create Device Input """
#    
#    output_list = []
#    for input in input_list:
#        dev_input = api.post_operations(operation, url_var, input, header) 
#        dev_input["templateId"] = input["templateId"]
#        output_list.append(dev_input)
#    
#    return output_list
#
#def duplicate_ip(input_list, url_var, operation, header):
#    """ Check if there are duplicate IPs """
#    
#    output_dict = {}
#    output_dict["device"] = []
#
#    ### FORMAT PAYLOAD DATA TO GENERATE CLI CONFIG ###
#    for input in input_list:
#        transit_dict = {}
#        transit_dict["csv-deviceIP"] = input["deviceIP"]
#        transit_dict["csv-deviceId"] = input["deviceIds"][0]
#        transit_dict["csv-host-name"] = input["host-name"]
#        output_dict["device"].append(transit_dict)
#    response = api.post_operations(operation, url_var, output_dict, header )
#    if response["data"] == []:
#        return response
#    else:
#        return None
#
#def get_dev_cli_config(input_list, url_var, operation, header):
#    """ Get running configuration """
#
#    ### FORMAT PAYLOAD DATA TO GENERATE TEMPLATE RUNNING CONFIG ###
#    output_list = []
#    for input in input_list:
#        output_dict = {}
#        output_dict["templateId"] = input["templateId"]
#        output_dict["device"] = input["data"][0]
#        output_dict["device"]["csv-templateId"] = output_dict["templateId"]
#        output_dict["isRFSRequired"] = True
#        output_dict["isEdited"] = False
#        output_dict["isMasterEdited"] = False
#        response = api.post_operations(operation, url_var, output_dict, header, False)
#        output_tuple = (output_dict, response)
#        output_list.append(output_tuple)
#
#    return output_list
#
#def get_dev_config(input_list, url_var, operation, header):
#    """ Generate Running Config """
#    
#    dev_conf_list = []
#    for dev_id in input_list: 
#        dev_id_str = dev_id["deviceIds"][0].replace("/","%2")
#        dev_conf = api.get_operations(operation + dev_id_str, url_var, header)
#        dev_conf_list.append(dev_conf)
#        
#    return dev_conf_list
#
#def eval_dev_support(input_list, url_var, operation, header):
#    """ Evaluate device model support """
#
#    dev_model_list = []
#    for dev_id in input_list: 
#        dev_id_str = dev_id["deviceIds"][0].replace("/","%2")
#        dev_conf = api.get_operations(operation + dev_id_str, url_var, header)
#        dev_model_list.append(dev_conf)
#
#    return dev_model_list
#
#def attach_feature_dev_template(input_list, url_var, operation, header):
#    """ Attach Feature Template to Device """
#
#    ### INITIALIZE FINAL DATA STRUCTURE ###
#    feature_template_dict = {}
#    feature_template_dict["deviceTemplateList"] = []
#
#    ### REMOVE FAILED CONFIGURATION RETRIEVALS ###
#    feature_template_list = [dev_tuple[0] for dev_tuple in input_list if dev_tuple[1] != None]
#    
#    ### REMOVE DUPLICATE TEMPLATE IDS ###
#    template_id_set = {template_id["templateId"] for template_id in feature_template_list}
#    
#    ### GENERATE FINAL DATA STRUCTURE ###
#    for template_id in template_id_set:
#        feature_template_dict["deviceTemplateList"].append(
#            {"templateId": template_id, 
#            "device": [], 
#            "isEdited": False, 
#            "isMasterEdited": False})
#    
#    ### TRANSFORM CONFIGURATION TO FINAL DATA STRUCTURE ###
#    for feature_template in feature_template_list:
#        for index, template_id in enumerate(feature_template_dict["deviceTemplateList"]):
#            if template_id["templateId"] ==  feature_template["templateId"]: 
#                feature_template_dict["deviceTemplateList"][index]["device"].append(feature_template["device"])
#            else:
#                pass
#    
#    ### API CALL ###
#    response = api.post_operations(operation, url_var, feature_template_dict, header)
#
#    return response
#
#def push_template(input_dict, url_var, operation, header):
#    """ Push generated templated"""
#
#    ### RETURNS STATUS OF OPERATION ###
#    push_id = input_dict["id"]
#    response = api.get_operations(operation + push_id, url_var, header)
#    
#    return response