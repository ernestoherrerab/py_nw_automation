#! /usr/bin/env python
"""
Script to update Hostnames on SDWAN
"""
from copy import deepcopy
from time import sleep
import urllib3
import network_automation.sdwan_ops.sdwan_api as sdwan

def update_hostname(url_var, username, password):
    """ Update Hostname operations """

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    ### GENERATE AUTHENTICATION ###
    auth_header = sdwan.auth(url_var, username, password)

    ### GET VEDGE INFO ###
    print("Getting vEdge Data...")
    vedge_data_ops = "dataservice/system/device/vedges"
    vedge_data = sdwan.get_dev_data(url_var, vedge_data_ops, auth_header)       
    
    ### MAP HOST TO TEMPLATES ###
    print("Mapping Host to Templates...")
    vedge_list = sdwan.host_template_mapping(vedge_data)

    ### CREATE DEVICE INPUT ###
    print("Creating Device Input...")
    vedge_input_ops = "dataservice/template/device/config/input"
    vedge_list_copy = deepcopy(vedge_list)
    for vedge in vedge_list_copy:
        vedge.pop("deviceIP", None)
        vedge.pop("host-name", None)
    vedge_input = sdwan.create_device_input(vedge_list_copy, url_var, vedge_input_ops, auth_header) 
    
         
    ### CHECK FOR DUPLICATE IPS ### 
    print(" Check if there are duplicate IPs...")
    duplicate_ip_ops = "dataservice/template/device/config/duplicateip"
    dup_ip = sdwan.duplicate_ip(vedge_list, url_var, duplicate_ip_ops, auth_header)
    if dup_ip == None:
        print("Duplicate IP Identified...")
        return False
    else:
        print("No duplicate IPs found...")
        
    ### GET DEVICE RUNNING CONFIGURATION ###
    print("Getting running configuration...")
    run_conf_ops = "dataservice/template/device/config/config/"
    run_config = sdwan.get_dev_cli_config(vedge_input, url_var, run_conf_ops, auth_header)
    
    
    ### GET ATTACHED CONFIGURATION TO DEVICE ###
    print("Generate Attached Running Config...")
    attached_dev_ops = "dataservice/template/device/config/attachedconfig?deviceId="
    attached_config = sdwan.get_dev_config(vedge_list, url_var, attached_dev_ops, auth_header)

    ### EVALUATE IF DEVICE MODEL IS SUPPORTED IN VMANAGE ###
    print("Evaluate the device model support...")
    dev_eval_ops = "dataservice/device/models/"
    dev_eval = sdwan.eval_dev_support(vedge_list, url_var, dev_eval_ops, auth_header)
    for dev_support in dev_eval:
        if dev_support["templateSupported"] == True :
            print(f'{dev_support["name"]} is supported...')
        else:
            print(f'{dev_support["name"]} is NOT supported...')
            return False

    ### ATTACH FEATURE DEVICE TEMPLATE ###
    print("Attach feature device template...")
    dev_templates_ops = "dataservice/template/device/config/attachfeature"
    dev_templates = sdwan.attach_feature_dev_template(run_config, url_var, dev_templates_ops, auth_header)

    ### PUSH TEMPLATE CHANGES ###
    print("Pushing changes...")
    push_status_ops = "dataservice/device/action/status/"
    push_status = sdwan.push_template(dev_templates, url_var, push_status_ops, auth_header) 
    while push_status["summary"]["status"] != "done":
        print("Pushing changes...")
        push_status = sdwan.push_template(dev_templates, url_var, push_status_ops, auth_header)
        sleep(20)
    else:
        return push_status


