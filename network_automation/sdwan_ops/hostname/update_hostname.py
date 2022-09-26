#! /usr/bin/env python
"""
Script to update Hostnames on SDWAN
"""

from time import sleep
import network_automation.sdwan_ops.sdwan_api as sdwan

def update_hostname(url_var, username, password):
    """ Update Hostname operations """

    ### GENERATE AUTHENTICATION ###
    auth_header = sdwan.auth(url_var, username, password)

    ### GET VEDGE INFO ###
    print("Getting vEdge Data...")
    vedge_data = sdwan.get_dev_data(url_var, auth_header)
    
    ### MAP HOST TO TEMPLATES ###
    print("Mapping Host to Templates...")
    vedge_list = sdwan.host_template_mapping(vedge_data)
    
    ### CREATE DEVICE INPUT ###
    print("Creating Device Input...")
    vedge_input = sdwan.create_device_input(vedge_list, url_var, auth_header)     
    
    ### CHECK FOR DUPLICATE IPS ### 
    print(" Check if there are duplicate IPs...")
    dup_ip = sdwan.duplicate_ip(vedge_list, url_var, auth_header)
    if dup_ip == None:
        print("Duplicate IP Identified...")
        return False
    else:
        print("No duplicate IPs found...")

    ### GET DEVICE RUNNING CONFIGURATION ###
    print("Getting running configuration...")
    run_config = sdwan.get_dev_cli_config(vedge_input, url_var, auth_header)

    ### GET ATTACHED CONFIGURATION TO DEVICE ###
    print("Generate Attached Running Config...")
    attached_config = sdwan.get_dev_config(vedge_list, url_var, auth_header)

    ### EVALUATE IF DEVICE MODEL IS SUPPORTED IN VMANAGE ###
    print("Evaluate the device model support...")
    dev_eval = sdwan.eval_dev_support(vedge_list, url_var, auth_header)
    for dev_support in dev_eval:
        if dev_support["templateSupported"] == True :
            print(f'{dev_support["name"]} is supported...')
        else:
            print(f'{dev_support["name"]} is NOT supported...')
            return False

    ### ATTACH FEATURE DEVICE TEMPLATE ###
    print("Attach feature device template...")
    dev_templates = sdwan.attach_feature_dev_template(run_config, url_var, auth_header)

    ### PUSH TEMPLATE CHANGES ###
    print("Pushing changes...")
    push_status = sdwan.push_template(dev_templates, url_var, auth_header) 
    while push_status["summary"]["status"] != "done":
        print("Pushing changes...")
        push_status = sdwan.push_template(dev_templates, url_var, auth_header)
        sleep(15)
    else:
        return push_status


