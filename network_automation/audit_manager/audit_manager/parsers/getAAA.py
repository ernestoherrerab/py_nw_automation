#! /usr/bin/env python
"""
Script to parse AAA configs
"""
import re

def audit_aaa(parse_obj):
    """ Parse AAA """

    dev_data = {}
    dev_data["aaa"] = {}
    aaa_authentication_lines = parse_obj.find_objects(r"^aaa authentication")
    aaa_authorization_lines = parse_obj.find_objects(r"^aaa authorization")
    aaa_accounting_lines = parse_obj.find_objects(r"^aaa accounting")
    aaa_tacacs_lines = parse_obj.find_objects(r"^tacacs-server")
    aaa_tacacs_group_lines = parse_obj.find_objects(r"^aaa group server tacacs")
    aaa_radius_lines = parse_obj.find_objects(r"^radius-server")
    aaa_radius_group_lines = parse_obj.find_objects(r"^aaa server radius")
    aaa_usernames_lines = parse_obj.find_objects(r"^username")
    aaa_enable_line = parse_obj.find_objects(r"^enable ")
    aaa_console_lines = parse_obj.find_objects(r"^line con")
    aaa_vty_lines = parse_obj.find_objects(r"^line vty")
    dev_data["aaa"]["authentication"] = []
    dev_data["aaa"]["authorization"] = []
    dev_data["aaa"]["accounting"] = []
    dev_data["aaa"]["tacacs_server"] = []
    dev_data["aaa"]["tacacs_server_group"] = {}
    dev_data["aaa"]["radius_server"] = []
    dev_data["aaa"]["radius_server_group"] = {}
    dev_data["aaa"]["local_users"] = {}
    dev_data["aaa"]["console"] = []
    dev_data["aaa"]["vtys"] = []
    if aaa_enable_line:
        dev_data["aaa"]["enable_pass"] = aaa_enable_line[0].text.replace("enable", "").replace(" ", "", 1)
    
    for aaa_authentication_line in aaa_authentication_lines:
        dev_data["aaa"]["authentication"].append(aaa_authentication_line.text.replace("aaa authentication", "").replace(" ", "", 1))
    for aaa_authorization_line in aaa_authorization_lines:
        dev_data["aaa"]["authorization"].append(aaa_authorization_line.text.replace("aaa authorization", "").replace(" ", "", 1))
    for aaa_accounting_line in aaa_accounting_lines:
        dev_data["aaa"]["accounting"].append(aaa_accounting_line.text.replace("aaa accounting ", "").replace(" ", "", 1))
    for aaa_tacacs_line in aaa_tacacs_lines:
        dev_data["aaa"]["tacacs_server"].append(aaa_tacacs_line.text.replace("tacacs-server ", ""))
    for aaa_radius_line in aaa_radius_lines:
        dev_data["aaa"]["radius_server"].append(aaa_radius_line.text.replace("radius-server ", ""))
    for aaa_usernames_line in aaa_usernames_lines:
        aaa_usernames_line = aaa_usernames_line.text
        local_user = re.findall(r'username\s(\S+)', aaa_usernames_line)
        user_privilege = re.findall(r'username\s\S+\sprivilege\s(\d+)', aaa_usernames_line)
        secret_pwd = re.findall(r'username\s\S+\sprivilege\s\d+\ssecret\s\d+\s(\S+)',aaa_usernames_line) 
        no_priv_pwd = re.findall(r'username\s\S+\s(?!privilege)\S+\s\d+\s(\S+)', aaa_usernames_line)
        local_user = local_user[0]
        if "local_users" not in dev_data["aaa"]:
            dev_data["aaa"]["local_users"] = {}
            dev_data["aaa"]["local_users"][local_user] = {}
            if user_privilege:
                user_privilege = user_privilege[0]
                dev_data["aaa"]["local_users"][local_user]["privilege"] = int(user_privilege)
            if secret_pwd:
                secret_pwd = secret_pwd[0]
                dev_data["aaa"]["local_users"][local_user]["secret"] = secret_pwd
            elif no_priv_pwd:
                no_priv_pwd = no_priv_pwd[0]
                dev_data["aaa"]["local_users"][local_user]["secret"] = no_priv_pwd
        else:
            dev_data["aaa"]["local_users"][local_user] = {}
            if user_privilege:
                user_privilege = user_privilege[0]
                dev_data["aaa"]["local_users"][local_user]["privilege"] = int(user_privilege)
            if secret_pwd:
                secret_pwd = secret_pwd[0]
                dev_data["aaa"]["local_users"][local_user]["secret"] = secret_pwd
            elif no_priv_pwd:
                no_priv_pwd = no_priv_pwd[0]
                dev_data["aaa"]["local_users"][local_user]["secret"] = no_priv_pwd
    for aaa_tacacs_group_line in aaa_tacacs_group_lines:
        tacacs_group = aaa_tacacs_group_line.re_match_typed(r'^aaa group server tacacs\+\s+(\S+)', default='')
        dev_data["aaa"]["tacacs_server_group"][tacacs_group] = []
        for aaa_tacacs_group_server in aaa_tacacs_group_line.children:
            dev_data["aaa"]["tacacs_server_group"][tacacs_group].append(aaa_tacacs_group_server.text.replace(" ","",1))
    for aaa_radius_group_line in aaa_radius_group_lines:
        radius_group = aaa_radius_group_line.re_match_typed(r'^aaa server radius\s+(\S+)', default='')
        dev_data["aaa"]["radius_server_group"][radius_group] = []
        for aaa_radius_group_server in aaa_radius_group_line.children:
            dev_data["aaa"]["radius_server_group"][radius_group].append(aaa_radius_group_server.text.replace(" ","",1))
    for aaa_console_line in aaa_console_lines:
        for aaa_console_access in aaa_console_line.children:
            dev_data["aaa"]["console"].append(aaa_console_access.text.replace(" ","",1))
    for aaa_vty_line in aaa_vty_lines:
        for aaa_vty_access in aaa_vty_line.children:
            if aaa_vty_access.text.replace(" ","",1) not in dev_data["aaa"]["vtys"]:
                dev_data["aaa"]["vtys"].append(aaa_vty_access.text.replace(" ","",1))
    return dev_data