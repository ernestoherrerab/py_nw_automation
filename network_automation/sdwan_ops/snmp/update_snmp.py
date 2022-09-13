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
    
def update_snmp(url_var, header):
    snmp_list = []
    feature_templates = api.get_operations("dataservice/template/feature", url_var, header)
    for snmp_template in feature_templates["data"]:
        if snmp_template["templateType"] == "snmp" or snmp_template["templateType"]== "cisco_snmp":
            snmp_list.append(snmp_template)
    
    return snmp_list


