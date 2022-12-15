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
    aaa_tacacs_servers_lines = parse_obj.find_objects(r"^tacacs\sserver\s")
    aaa_tacacs_group_lines = parse_obj.find_objects(r"^aaa group server tacacs")
    aaa_tacacs_source_if_line = parse_obj.find_objects(r'ip tacacs source-interface')
    aaa_radius_lines = parse_obj.find_objects(r"^radius-server")
    aaa_radius_group_lines = parse_obj.find_objects(r"^aaa server radius")
    aaa_console_lines = parse_obj.find_objects(r"^line con")
    aaa_vty_lines = parse_obj.find_objects(r"^line vty")
    dev_data[hostname]["authentication"] = []
    dev_data[hostname]["authorization"] = []
    dev_data[hostname]["accounting"] = []
    dev_data[hostname]["line_console_0"] = []
    dev_data[hostname]["line_vty_0_15"] = []
    if aaa_tacacs_source_if_line:
        dev_data[hostname]["tacacs_source_interface"] = []
        aaa_tacacs_source_if_line = aaa_tacacs_source_if_line[0].text  
        dev_data[hostname]["tacacs_source_interface"].append( aaa_tacacs_source_if_line)
    if aaa_tacacs_servers_lines:
        dev_data[hostname]["tacacs_servers"] = [server.text for server in aaa_tacacs_servers_lines]
    for aaa_authentication_line in aaa_authentication_lines:
        dev_data[hostname]["authentication"].append(aaa_authentication_line.text)
    for aaa_authorization_line in aaa_authorization_lines:
        aaa_authorization_line = aaa_authorization_line.text
        dev_data[hostname]["authorization"].append(aaa_authorization_line)
    for aaa_accounting_line in aaa_accounting_lines:
        aaa_accounting_line = aaa_accounting_line.text
        aaa_accounting_start_stop = re.findall(r'aaa\saccounting\ssystem\sdefault', aaa_accounting_line)
        if aaa_accounting_start_stop: 
            dev_data[hostname]["accounting"].append(aaa_accounting_start_stop[0])
        else:
            dev_data[hostname]["accounting"].append(aaa_accounting_line)
    if aaa_tacacs_lines:
        dev_data[hostname]["tacacs_server"] = []
        for aaa_tacacs_line in aaa_tacacs_lines:
            aaa_tacacs_line = aaa_tacacs_line.text
            dev_data[hostname]["tacacs_server"].append(aaa_tacacs_line)
    if aaa_radius_lines:
        dev_data[hostname]["radius_server"] = []
        for aaa_radius_line in aaa_radius_lines:
            aaa_radius_line = aaa_radius_line.text
            dev_data[hostname]["radius_server"].append(aaa_radius_line)
    if aaa_tacacs_group_lines:
        dev_data[hostname]["tacacs_server_group"] = []
        for aaa_tacacs_group_line in aaa_tacacs_group_lines:
            dev_data[hostname]["tacacs_server_group"].append(aaa_tacacs_group_line.text)
    if aaa_radius_group_lines:
        dev_data[hostname]["radius_server_group"] = []
        for aaa_radius_group_line in aaa_radius_group_lines:
            dev_data[hostname]["radius_server_group"].append(aaa_radius_group_line.text)            
    for aaa_console_line in aaa_console_lines:
        for aaa_console_access in aaa_console_line.children:
            aaa_console_access = aaa_console_access.text
            dev_data[hostname]["line_console_0"].append(aaa_console_access[1:])
    for aaa_vty_line in aaa_vty_lines:
        for aaa_vty_access in aaa_vty_line.children:
            aaa_vty_access = aaa_vty_access.text
            aaa_vty_transport_ssh = re.match(r'\stransport\sinput\sssh', aaa_vty_access )
            if  not aaa_vty_transport_ssh:
                dev_data[hostname]["line_vty_0_15"].append(aaa_vty_access[1:])        

    return dev_data