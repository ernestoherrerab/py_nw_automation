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

def get_all_templates_config(authentication, vmanage, template_name=None):
    """ 
    Get templates information for all or specific templates 
    """
    device_template = DeviceTemplates(authentication, vmanage)
    device_templates_list = device_template.get_device_template_list(name_list=template_name)
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
    
    output_dict = {}
    if "templateId" in input_dict and "host-name" in input_dict:
        output_dict["deviceIP"] = input_dict["deviceIP"]
        output_dict["host-name"] = input_dict["host-name"]
        output_dict["templateId"] = input_dict["templateId"]
        output_dict["template"] = input_dict["template"]
        output_dict["deviceIds"] = [input_dict["uuid"]]
        output_dict["isEdited"] = False
        output_dict["isMasterEdited"] = False
            
    return output_dict