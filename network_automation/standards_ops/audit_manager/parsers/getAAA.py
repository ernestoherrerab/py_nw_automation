#! /usr/bin/env python
"""
Script to parse AAA configs
"""
import re

def audit_aaa(parse_obj, hostname):
    """ Parse AAA """

    dev_data = {}
    dev_data[hostname] = {}
    aaa_authentication_lines = parse_obj.find_objects(r"^aaa authentication")
    aaa_authorization_lines = parse_obj.find_objects(r"^aaa authorization")
    aaa_accounting_lines = parse_obj.find_objects(r"^aaa accounting")
    aaa_tacacs_lines = parse_obj.find_objects(r"^tacacs-server")
    aaa_tacacs_group_lines = parse_obj.find_objects(r"^aaa group server tacacs")
    aaa_tacacs_source_if_line = parse_obj.find_objects(r'ip tacacs source-interface')
    aaa_radius_lines = parse_obj.find_objects(r"^radius-server")
    aaa_radius_group_lines = parse_obj.find_objects(r"^aaa server radius")
    aaa_usernames_lines = parse_obj.find_objects(r"^username")
    aaa_enable_line = parse_obj.find_objects(r"^enable ")
    aaa_console_lines = parse_obj.find_objects(r"^line con")
    aaa_vty_lines = parse_obj.find_objects(r"^line vty")
    dev_data[hostname]["authentication"] = []
    dev_data[hostname]["authorization"] = []
    dev_data[hostname]["accounting"] = []
    dev_data[hostname]["tacacs_server"] = []
    dev_data[hostname]["tacacs_server_group"] = []
    dev_data[hostname]["radius_server"] = []
    dev_data[hostname]["radius_server_group"] = []
    dev_data[hostname]["local_users"] = []
    dev_data[hostname]["console"] = []
    dev_data[hostname]["vtys"] = []
    if aaa_enable_line:
        dev_data[hostname]["enable_pass"] = aaa_enable_line[0].text
    if aaa_tacacs_source_if_line:
        dev_data[hostname]["tacacs_source_interface"] = aaa_tacacs_source_if_line[0].text
    for aaa_authentication_line in aaa_authentication_lines:
        dev_data[hostname]["authentication"].append(aaa_authentication_line.text)
    for aaa_authorization_line in aaa_authorization_lines:
        aaa_authorization_line = aaa_authorization_line.text
        dev_data[hostname]["authorization"].append(aaa_authorization_line)
    for aaa_accounting_line in aaa_accounting_lines:
        dev_data[hostname]["accounting"].append(aaa_accounting_line.text)
    for aaa_tacacs_line in aaa_tacacs_lines:
        aaa_tacacs_line = aaa_tacacs_line.text
        dev_data[hostname]["tacacs_server"].append(aaa_tacacs_line)
    for aaa_radius_line in aaa_radius_lines:
        aaa_radius_line = aaa_radius_line.text
        dev_data[hostname]["radius_server"].append(aaa_radius_line)
    for aaa_usernames_line in aaa_usernames_lines:
        dev_data[hostname]["local_users"].append(aaa_usernames_line.text)
    for aaa_tacacs_group_line in aaa_tacacs_group_lines:
        dev_data[hostname]["tacacs_server_group"].append(aaa_tacacs_group_line.text)
    for aaa_radius_group_line in aaa_radius_group_lines:
        dev_data[hostname]["radius_server_group"].append(aaa_radius_group_line.text)            
    for aaa_console_line in aaa_console_lines:
        for aaa_console_access in aaa_console_line.children:
            aaa_console_access = aaa_console_access.text
            dev_data[hostname]["console"].append(aaa_console_access[1:])
    for aaa_vty_line in aaa_vty_lines:
        for aaa_vty_access in aaa_vty_line.children:
            aaa_vty_access = aaa_vty_access.text
            aaa_vty_transport_ssh = re.match(r'\stransport\sinput\sssh', aaa_vty_access )
            if  not aaa_vty_transport_ssh:
                dev_data[hostname]["vtys"].append(aaa_vty_access[1:])        

    return dev_data