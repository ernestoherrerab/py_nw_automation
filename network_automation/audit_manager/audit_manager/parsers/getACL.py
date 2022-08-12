#! /usr/bin/env python
"""
Script to parse Static Routing configs
"""
import regex as re
from netaddr import valid_ipv4, IPAddress

def audit_acl(parse_obj):
    """ Parse ACLs """
    dev_data = {}
    dev_data["standard_access_lists"] = {}
    dev_data["access_lists"] = {}
    ip_acls_lines = parse_obj.find_objects(r'^ip\saccess-list')

    for acl_line in ip_acls_lines:
        acl_line_text = acl_line.text
        standard_acl_match = re.match(r'ip\saccess-list\sstandard', acl_line_text)
        extended_acl_match = re.match(r'ip\saccess-list\sextended', acl_line_text)
        ### EVALUATE STANDARD ACLS ###
        if standard_acl_match:
            dev_data["standard_access_lists"][acl_line_text.replace("ip access-list standard ", "")] = []
            for acl_parameters in acl_line.children:
                acl_parameters = acl_parameters.text
                action = re.findall(r'\s(.+)$', acl_parameters)
                dev_data["standard_access_lists"][acl_line_text.replace("ip access-list standard ", "")].append(action[0])
        ### EVALUATE EXTENDED ACLS ###
        elif extended_acl_match:
            dev_data["access_lists"][acl_line_text.replace("ip access-list extended ", "")] = []
            for acl_parameters in acl_line.children:
                acl_parameters = acl_parameters.text
                action = re.findall(r'\s(.+)$', acl_parameters)
                dev_data["access_lists"][acl_line_text.replace("ip access-list extended ", "")].append(action[0])

    return dev_data