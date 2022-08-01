#! /usr/bin/env python
"""
Script to parse Base configs
"""

def audit_base(parse_obj):
    
    """ Parse Base """
    dev_data = {}
    dev_data["base"] = {}
    dev_data["base"]["timestamps"] = []
    dev_data["base"]["domain"] = {}
    base_service_lines = parse_obj.find_objects(r"^service")
    base_domainlookup_line = parse_obj.find_objects(r"^ip domain-lookup")
    base_domainname_line = parse_obj.find_objects(r"^ip domain-name")
    base_httpserver_line = parse_obj.find_objects(r"^ip http server")
    base_httpsserver_line = parse_obj.find_objects(r"^ip http secure-server")

    for base_service_line in base_service_lines:
        if "timestamps" in base_service_line.text:
            base_service_line = base_service_line.text.replace("service timestamps", "").replace(" ", "", 1)
            dev_data["base"]["timestamps"].append(base_service_line)
        elif "password-encryption" in base_service_line.text:
             dev_data["base"]["pwd_encryption"] = True

    if base_domainlookup_line:
        dev_data["base"]["domain"]["lookup"] = True
    else:
        dev_data["base"]["domain"]["lookup"] = False 

    if base_domainname_line:
        base_domainname_line = base_domainname_line[0].text.replace("ip domain-name", "").replace(" ", "", 1)
        dev_data["base"]["domain"]["name"] = base_domainname_line

    if base_httpserver_line:
        dev_data["base"]["http_server"] = True
    else:
        dev_data["base"]["http_server"] = False

    if base_httpsserver_line:
        dev_data["base"]["https_server"] = True
    else:
        dev_data["base"]["https_server"] = False

    return dev_data

