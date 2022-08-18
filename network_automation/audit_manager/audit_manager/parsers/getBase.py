#! /usr/bin/env python
"""
Script to parse Base configs
"""
from netaddr import valid_ipv4

def audit_base(parse_obj):
    
    """ Parse Base """
    dev_data = {}
    dev_data["base"] = {}
    dev_data["base"]["timestamps"] = []
    dev_data["base"]["domain"] = {}
    dev_data["base"]["logging"] = {}
    base_service_lines = parse_obj.find_objects(r"^service")
    base_domainlookup_line = parse_obj.find_objects(r"^ip domain-lookup")
    base_domainname_line = parse_obj.find_objects(r"^ip domain-name")
    base_httpserver_line = parse_obj.find_objects(r"^ip http server")
    base_httpsserver_line = parse_obj.find_objects(r"^ip http secure-server")
    base_logging_line = parse_obj.find_objects(r"^logging")
    base_logging_console_line = parse_obj.find_objects(r"logging console")

    ### EVALUATE TIMESTAMPS  & PASSWORD ENCRYPTION ###
    for base_service_line in base_service_lines:
        if "timestamps" in base_service_line.text:
            base_service_line = base_service_line.text.replace("service timestamps", "").replace(" ", "", 1)
            dev_data["base"]["timestamps"].append(base_service_line)
        elif "password-encryption" in base_service_line.text:
             dev_data["base"]["pwd_encryption"] = True
    
    ### EVALUATE DOMAIN DATA ###
    if base_domainlookup_line:
        dev_data["base"]["domain"]["lookup"] = True
    else:
        dev_data["base"]["domain"]["lookup"] = False 

    if base_domainname_line:
        base_domainname_line = base_domainname_line[0].text.replace("ip domain-name", "").replace(" ", "", 1)
        dev_data["base"]["domain"]["name"] = base_domainname_line
    
    ### EVALUATE HTTP/S SERVER ###
    if base_httpserver_line:
        dev_data["base"]["http_server"] = True
    else:
        dev_data["base"]["http_server"] = False

    if base_httpsserver_line:
        dev_data["base"]["https_server"] = True
    else:
        dev_data["base"]["https_server"] = False
    
    ### EVALUATE LOGGING ###
    for base_logging in base_logging_line:
        base_logging_text = base_logging.text
        if "trap" in base_logging_text:
            dev_data["base"]["logging"]["trap"] = base_logging_text.replace("logging trap " , "")
        elif "source-interface" in base_logging_text:
            dev_data["base"]["logging"]["source_interface"] = base_logging_text.replace("logging source-interface " , "")
        elif valid_ipv4(base_logging_text.replace("logging ", "")) and "hosts" not in dev_data["base"]["logging"]:
            dev_data["base"]["logging"]["hosts"] = {}
            dev_data["base"]["logging"]["hosts"][base_logging_text.replace("logging ", "")] = {}
        elif valid_ipv4(base_logging_text.replace("logging ", "")) and "hosts" in dev_data["base"]["logging"]:
            dev_data["base"]["logging"]["hosts"][base_logging_text.replace("logging ", "")] = {}

    for logging_console in base_logging_console_line:
        logging_console_text = logging_console.text
        if logging_console_text == "no logging console":
            dev_data["base"]["logging"]["console"] = False
  
    return dev_data

