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
from vmanage.api.policy_lists import  PolicyLists

### LOGGING SETUP ###
LOG_FILE = Path("logs/sdwan_ops.log")
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler(LOG_FILE)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

def auth(vmanage: str, username: str, password: str) -> Authentication.login:
    """Authenticate vManage

    Args:
    vmanage (str): vManage URL as an env variable
    username (str): From frontend input
    password (str): From frontend input
    
    Returns:
    auth (Session obj): Session object
    """
    auth = Authentication(host=vmanage, port=8443,user=username,password=password).login()

    return auth

def attach_dev_template(authentication: Authentication.login, vmanage: str, payload: dict, config_type: (str) ="template") -> dict:
    """Attach template to device

    Args:
    authentication (Authentication.login): Session object
    vmanage (str): vManage URL as an env variable
    payload (dict): Template and Device attachment data
    config_type (str): "cli" or "template" (by default)
    
    Returns:
    response (dict): Response formatted as a dictionary 
    """
    device_template = DeviceTemplates(authentication, vmanage)
    response =  device_template.attach_to_template(payload, config_type)
    return response


def clone_template(authentication: Authentication.login, vmanage: str, template_dict: dict) -> int:
    """Create new Prisma Templates
    
    Args:
    authentication (Authentication.login): Session object
    vmanage (str): vManage URL as an env variable
    template_dict (dict): Template creation payload
    
    Returns:
    response (int): Response code     
    """ 
    device_template = DeviceTemplates(authentication, vmanage)
    try:
        response =  device_template.add_device_template(template_dict) 
        return response
    except Exception as e:
        print("Something went wrong...check log...")
        return e

def get_all_templates_config(authentication: Authentication.login, vmanage: str, template_name: str =None) -> list:
    """Get templates information for all or specific templates

    Args:
    authentication (Authentication.login): Session object
    vmanage (str): vManage URL as an env variable
    template_name (str): Template new to search if specified
    
    Returns:
    device_templates_list (list): Templates data
    """
    device_template = DeviceTemplates(authentication, vmanage)
    device_templates_list = device_template.get_device_template_list(name_list=template_name)
    return device_templates_list

def get_dev_feature_template(authentication: Authentication.login, vmanage: str, factory_default: bool=False, name_list: list=None) -> list:
    """Get feature templates data to specific template

    Args:
    authentication (Authentication.login): Session object
    vmanage (str): vManage URL as an env variable
    factory_default (bool): Always use "False"
    name_list (list): Can be used if the exact name of the template is known to get filtered data
    
    Returns:
    feature_template_list (list): Feature templates data either filtered or full list
    """
    feature_template = FeatureTemplates(authentication, vmanage)
    feature_template_list = feature_template.get_feature_template_list(factory_default, name_list)
    return feature_template_list

def get_template_config(authentication: Authentication.login, vmanage: str, template_id: str) -> list:
    """Get Reachable vEdge Data
    
    Args:
    authentication (Authentication.login): Session object
    vmanage (str): vManage URL as an env variable
    template_id (str) : Current device template id)
    
    Returns:
    device_templates_list (list): Current device template configuration
    """
    device_templates = DeviceTemplates(authentication, vmanage)
    device_templates_list = device_templates.get_device_template_object(template_id)
    return device_templates_list

def get_template_input(authentication: Authentication.login, vmanage: str, template_id: str, dev_id_list: list =None) -> list:
    """Get the template variable input data

    Args:
    authentication (Authentication.login): Session object
    vmanage (str): vManage URL as an env variable
    template_id (str): Template id to retrieve input data from
    dev_id_list (list): To filter further for specific devices
    
    Returns:
    device_input_list (list): List of template input data   
    """
    device_input = DeviceTemplates(authentication, vmanage)
    device_input_list = device_input.get_template_input(template_id, dev_id_list)
    return device_input_list


def get_vedge_list(authentication: Authentication.login, vmanage: str) -> list:
    """Get Reachable vEdge Data 

    Args:
    authentication (Authentication.login): Session object
    vmanage (str): vManage URL as an env variable
    
    Returns:
    device_config_list (list): vEdge devices data
    """
    vmanage_device = Device(authentication, vmanage)
    device_config_list = vmanage_device.get_device_config_list("vedges")
    return device_config_list


def host_template_mapping(input_dict: dict) -> dict:
    """Generate Host to Template Mapping

    Args:
    input_dict (dict): Specific vEdge data
    
    Returns:
    output_dict (dict): Reformatted vEdge data structure to associate host with template
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

def update_site_list(list_id, sdwan_site_id, vmanage):
    """
    Updates the Azure Site List with the provided SDWAN site ID.

    Args:
        list_id (str): The ID of the list to update.
        sdwan_site_id (str): The ID of the SDWAN site to add to the Azure Site List.
        vmanage (str): The URL of the vManage appliance
        

    Returns:
        str: A message indicating the success of the update.
    """

    print(f'The SDWAN Site ID is: {sdwan_site_id}')
    policy = PolicyLists(auth, vmanage)
    response =  policy.get_policy_list_by_id(list_id)
    response["entries"].append({'siteId': sdwan_site_id})
    print(f'Azure Policy List {response}')
    update = policy.update_policy_list(response)
    print(f'The Azure Site List update with {sdwan_site_id} resulted in {update["status_code"]}')
    
    return update["status_code"]

