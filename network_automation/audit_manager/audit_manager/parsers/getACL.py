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
    dev_data["ip_access_lists"] = {}
    ip_acls_lines = parse_obj.find_objects(r'^ip\saccess-list')

    for acl_line in ip_acls_lines:
        acl_line_text = acl_line.text
        standard_acl_match = re.match(r'ip\saccess-list\sstandard')
        extended_acl_match = re.match(r'ip\saccess-list\sextended')
        if standard_acl_match:
            dev_data["standard_access_lists"][acl_line_text.replace("ip access-list standard ", "")] = {}
            for acl_parameters in acl_line.children:
                action = re.findall(r'\s(\w+)')

        elif extended_acl_match:
            dev_data["ip_access_lists"][acl_line_text.replace("ip access-list extended ", "")] = {}


    return dev_data