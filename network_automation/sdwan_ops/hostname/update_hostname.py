#! /usr/bin/env python
"""
Script to update SNMP Templates on SDWAN
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

def get_dev_config(input_list, url_var, header):
    """ Generate Running Config """
    
    dev_conf_list = []
    for dev_id in input_list: 
        dev_conf = api.get_operations(f'dataservice/template/device/config/attachedconfig?deviceId={dev_id["deviceIds"][0]}', url_var, header)
        print(dev_id["deviceIds"][0])
        dev_conf_list.append(dev_conf)
        
    print(dev_conf_list)
    return dev_conf_list
    

def update_hostname(url_var, header):
    """ Update Hostname operations """

    ### GET VEDGE INFO ###
    print("Getting vEdge Data...")
    vedge_data = api.get_operations("dataservice/system/device/vedges", url_var, header)
    
    ### MAP HOST TO TEMPLATES ###
    print("Mapping Host to Templates...")
    vedge_list = host_template_mapping(vedge_data)
    
    ### CREATE DEVICE INPUT ###
    print("Creating Device Input...")
    vedge_input = create_device_input(vedge_list, url_var, header)     
    
    ### CHECK FOR DUPLICATE IPS ### 
    print(" Check if there are duplicate IPs...")
    dup_ip = duplicate_ip(vedge_list, url_var, header)
    if dup_ip == None:
        print("Duplicate IP Identified...")
        return None

    ### GET ATTACHED CONFIGURATION TO DEVICE ###
    print("Generate Running Config...")
    attached_config = get_dev_config(vedge_list, url_var, header)


    return attached_config


