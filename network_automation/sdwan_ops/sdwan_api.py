#! /usr/bin/env python
"""
SDWAN API Functions
"""

import network_automation.sdwan_ops.api_calls as api
from network_automation.sdwan_ops.Authentication import Authentication


def auth(vmanage, username, password):
    """ Authenticate vManage"""
    
    Auth = Authentication()
    jsessionid = Auth.get_jsessionid(vmanage, username, password)
    token = Auth.get_token(vmanage, jsessionid)

    if token is not None:
        header = {'Content-Type': "application/json",'Cookie': jsessionid, 'X-XSRF-TOKEN': token}
        return header
    else:
        header = {'Content-Type': "application/json",'Cookie': jsessionid}
        return header

def get_dev_data(url_var, header):
    data = api.get_operations("dataservice/system/device/vedges", url_var, header)
    return data

def host_template_mapping(input_dict):
    """ Generate Host to Template Mapping """
    output_list = []
    for host_template in input_dict["data"]:
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

def create_device_input(input_list, url_var, header):
    """ Create Device Input """
    
    output_list = []
    for input in input_list:
        dev_input = api.post_operations("dataservice/template/device/config/input", url_var, input, header) 
        dev_input["templateId"] = input["templateId"]
        output_list.append(dev_input) 
    
    return output_list

def duplicate_ip(input_list, url_var, header):
    """ Check if there are duplicate IPs """
    
    output_dict = {}
    output_dict["device"] = []

    for input in input_list:
        transit_dict = {}
        transit_dict["csv-deviceIP"] = input["deviceIP"]
        transit_dict["csv-deviceId"] = input["deviceIds"][0]
        transit_dict["csv-host-name"] = input["host-name"]
        output_dict["device"].append(transit_dict)

    response = api.post_operations("dataservice/template/device/config/duplicateip", url_var, output_dict, header )
    if response["data"] == []:
        return response
    else:
        return None

def get_dev_cli_config(input_list, url_var, header):
    """ Get running configuration """
    
    output_list = []
    for input in input_list:
        output_dict = {}
        output_dict["templateId"] = input["templateId"]
        output_dict["device"] = input["data"][0]
        output_dict["device"]["csv-templateId"] = output_dict["templateId"]
        output_dict["isRFSRequired"] = True
        output_dict["isEdited"] = False
        output_dict["isMasterEdited"] = False
        response = api.post_operations("dataservice/template/device/config/config/", url_var, output_dict, header, False)
        output_tuple = (output_dict, response)
        output_list.append(output_tuple)

    return output_list

def get_dev_config(input_list, url_var, header):
    """ Generate Running Config """
    
    dev_conf_list = []
    for dev_id in input_list: 
        dev_id_str = dev_id["deviceIds"][0].replace("/","%2")
        dev_conf = api.get_operations(f'dataservice/template/device/config/attachedconfig?deviceId={dev_id_str}', url_var, header)
        dev_conf_list.append(dev_conf)
        
    return dev_conf_list

def eval_dev_support(input_list, url_var, header):
    """ Evaluate device model support """

    dev_model_list = []
    for dev_id in input_list: 
        dev_id_str = dev_id["deviceIds"][0].replace("/","%2")
        dev_conf = api.get_operations(f'dataservice/device/models/{dev_id_str}', url_var, header)
        dev_model_list.append(dev_conf)

    return dev_model_list

def attach_feature_dev_template(input_list, url_var, header):
    """ Attach Feature Template to Device """

    ### INITIALIZE FINAL DATA STRUCTURE ###
    feature_template_dict = {}
    feature_template_dict["deviceTemplateList"] = []

    ### REMOVE FAILED CONFIGURATION RETRIEVALS ###
    feature_template_list = [dev_tuple[0] for dev_tuple in input_list if dev_tuple[1] != None]
    
    ### REMOVE DUPLICATE TEMPLATE IDS ###
    template_id_set = {template_id["templateId"] for template_id in feature_template_list}
    
    ### GENERATE FINAL DATA STRUCTURE ###
    for template_id in template_id_set:
        feature_template_dict["deviceTemplateList"].append(
            {"templateId": template_id, 
            "device": [], 
            "isEdited": False, 
            "isMasterEdited": False})
    
    ### TRANSFORM CONFIGURATION TO FINAL DATA STRUCTURE ###
    for feature_template in feature_template_list:
        for index, template_id in enumerate(feature_template_dict["deviceTemplateList"]):
            if template_id["templateId"] ==  feature_template["templateId"]: 
                feature_template_dict["deviceTemplateList"][index]["device"].append(feature_template["device"])
            else:
                pass
    
    ### API CALL ###
    response = api.post_operations("dataservice/template/device/config/attachfeature", url_var, feature_template_dict, header)

    return response

def push_template(input_dict, url_var, header):
    """ Push generated templated"""

    push_id = input_dict["id"]
    response = api.get_operations(f'dataservice/device/action/status/{push_id}', url_var, header)
    print(response)

    return response

