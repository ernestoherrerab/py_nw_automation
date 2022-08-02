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
    dev_data["aaa"]["tacacs_server"] = {}
    dev_data["aaa"]["tacacs_server_group"] = {}
    dev_data["aaa"]["radius_server"] = {}
    dev_data["aaa"]["radius_server_group"] = {}
    dev_data["aaa"]["local_users"] = {}
    dev_data["aaa"]["console"] = []
    dev_data["aaa"]["vtys"] = {}
    if aaa_enable_line:
        dev_data["aaa"]["enable_pass"] = aaa_enable_line[0].text.replace("enable", "").replace(" ", "", 1)
    for aaa_authentication_line in aaa_authentication_lines:
        dev_data["aaa"]["authentication"].append(aaa_authentication_line.text.replace("aaa authentication", "").replace(" ", "", 1))
    for aaa_authorization_line in aaa_authorization_lines:
        dev_data["aaa"]["authorization"].append(aaa_authorization_line.text.replace("aaa authorization", "").replace(" ", "", 1))
    for aaa_accounting_line in aaa_accounting_lines:
        dev_data["aaa"]["accounting"].append(aaa_accounting_line.text.replace("aaa accounting ", "").replace(" ", "", 1))
    for aaa_tacacs_line in aaa_tacacs_lines:
        aaa_tacacs_line = aaa_tacacs_line.text
        tacacs_params = re.findall(r'tacacs-server\shost (\S+)\s\S+\s\d+\s(\S+)', aaa_tacacs_line)
        if tacacs_params:
            tacacs_host = tacacs_params[0][0]
            tacacs_key = tacacs_params[0][1]
            if tacacs_host not in dev_data["aaa"]["tacacs_server"]:
                dev_data["aaa"]["tacacs_server"][tacacs_host] = {}
                dev_data["aaa"]["tacacs_server"][tacacs_host]["key"] = tacacs_key
            else:
                dev_data["aaa"]["tacacs_server"][tacacs_host]["key"] = tacacs_key
    for aaa_radius_line in aaa_radius_lines:
        aaa_radius_line = aaa_radius_line.text
        radius_attribute = re.findall(r'radius-server\sattribute\s(\d+)\s(\S+)', aaa_radius_line)
        radius_host = re.findall(r'radius-server\shost\s(\S+)\sauth-port\s(\d+)\sacct-port\s(\d+)\s(\S+)\susername\s(\S+)\s(\S+)\s(\d+)\s(\S+)\s(\d+)\s(\S+)', aaa_radius_line)
        if radius_attribute:
            attribute_id = int(radius_attribute[0][0])
            attribute_param = radius_attribute[0][1]
            if "radius_server" not in dev_data["aaa"]:
                dev_data["aaa"]["radius_server"] = {}
                dev_data["aaa"]["radius_server"]["attributes"] = {}
                dev_data["aaa"]["radius_server"]["attributes"][attribute_id] = []
                dev_data["aaa"]["radius_server"]["attributes"][attribute_id].append(attribute_param)
            elif "radius_server" in dev_data["aaa"] and "attributes" not in dev_data["aaa"]["radius_server"]:
                dev_data["aaa"]["radius_server"]["attributes"] = {}
                dev_data["aaa"]["radius_server"]["attributes"][attribute_id] = []
                dev_data["aaa"]["radius_server"]["attributes"][attribute_id].append(attribute_param)
            elif "radius_server" in dev_data["aaa"] and "attributes" in dev_data["aaa"]["radius_server"] and attribute_id not in dev_data["aaa"]["radius_server"]["attributes"]:
                dev_data["aaa"]["radius_server"]["attributes"][attribute_id] = []
                dev_data["aaa"]["radius_server"]["attributes"][attribute_id].append(attribute_param)
            elif "radius_server" in dev_data["aaa"] and radius_attribute and "attributes" in dev_data["aaa"]["radius_server"] and attribute_id in dev_data["aaa"]["radius_server"]["attributes"]:
                dev_data["aaa"]["radius_server"]["attributes"][attribute_id].append(attribute_param)
        if radius_host:
            radius_host_id = radius_host[0][0] 
            radius_auth_port = int(radius_host[0][1] )
            radius_acct_port = int(radius_host[0][2])
            test_condition = radius_host[0][3]
            radius_test_user = radius_host[0][4]
            radius_idle_time_cond = radius_host[0][5]
            radius_idle_time = int(radius_host[0][6])
            radius_test_pwd = radius_host[0][9]
            if "radius_server" not in dev_data["aaa"]:
                dev_data["aaa"]["radius_server"] = {}
                dev_data["aaa"]["radius_server"]["host"] = {}
                dev_data["aaa"]["radius_server"]["host"][radius_host_id] = {}
                if radius_auth_port:
                    dev_data["aaa"]["radius_server"]["host"][radius_host_id]["auth_port"] = radius_auth_port
                if radius_acct_port:
                    dev_data["aaa"]["radius_server"]["host"][radius_host_id]["acct_port"] = radius_acct_port
                if test_condition:
                    dev_data["aaa"]["radius_server"]["host"][radius_host_id]["test"] = True
                    dev_data["aaa"]["radius_server"]["host"][radius_host_id]["test_user"] = radius_test_user
                if radius_idle_time_cond:
                    dev_data["aaa"]["radius_server"]["host"][radius_host_id]["idle_time"] = radius_idle_time
                if radius_test_pwd: 
                    dev_data["aaa"]["radius_server"]["host"][radius_host_id]["key"] = radius_test_pwd
            elif "radius_server" in dev_data["aaa"] and "host" not in dev_data["aaa"]["radius_server"]:
                dev_data["aaa"]["radius_server"]["host"] = {}
                dev_data["aaa"]["radius_server"]["host"][radius_host_id] = {}
                if radius_auth_port:
                    dev_data["aaa"]["radius_server"]["host"][radius_host_id]["auth_port"] = radius_auth_port
                if radius_acct_port:
                    dev_data["aaa"]["radius_server"]["host"][radius_host_id]["acct_port"] = radius_acct_port
                if test_condition:
                    dev_data["aaa"]["radius_server"]["host"][radius_host_id]["test"] = True
                    dev_data["aaa"]["radius_server"]["host"][radius_host_id]["test_user"] = radius_test_user
                if radius_idle_time_cond:
                    dev_data["aaa"]["radius_server"]["host"][radius_host_id]["idle_time"] = radius_idle_time
                if radius_test_pwd: 
                    dev_data["aaa"]["radius_server"]["host"][radius_host_id]["key"] = radius_test_pwd
            elif "radius_server" in dev_data["aaa"] and "host" in dev_data["aaa"]["radius_server"]:
                dev_data["aaa"]["radius_server"]["host"][radius_host_id] = {}
                if radius_auth_port:
                    dev_data["aaa"]["radius_server"]["host"][radius_host_id]["auth_port"] = radius_auth_port
                if radius_acct_port:
                    dev_data["aaa"]["radius_server"]["host"][radius_host_id]["acct_port"] = radius_acct_port
                if test_condition:
                    dev_data["aaa"]["radius_server"]["host"][radius_host_id]["test"] = True
                    dev_data["aaa"]["radius_server"]["host"][radius_host_id]["test_user"] = radius_test_user
                if radius_idle_time_cond:
                    dev_data["aaa"]["radius_server"]["host"][radius_host_id]["idle_time"] = radius_idle_time
                if radius_test_pwd: 
                    dev_data["aaa"]["radius_server"]["host"][radius_host_id]["key"] = radius_test_pwd
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
            dev_data["aaa"]["tacacs_server_group"][tacacs_group].append(aaa_tacacs_group_server.text.replace(" server ",""))
    for aaa_radius_group_line in aaa_radius_group_lines:
        radius_group = aaa_radius_group_line.re_match_typed(r'^aaa server radius\s+(\S+)', default='')
        dev_data["aaa"]["radius_server_group"][radius_group] = {}
        for aaa_radius_group_server in aaa_radius_group_line.children:
            aaa_radius_group_server = aaa_radius_group_server.text
            radius_clients = re.findall(r'client\s(\S+)\s\S+\s\d+\s(\S+)', aaa_radius_group_server)
            radius_client = radius_clients[0][0]
            radius_key = radius_clients[0][1]
            if radius_client not in dev_data["aaa"]["radius_server_group"][radius_group]:
                dev_data["aaa"]["radius_server_group"][radius_group][radius_client] = {}
                dev_data["aaa"]["radius_server_group"][radius_group][radius_client]["key"] = radius_key
            else:
                dev_data["aaa"]["radius_server_group"][radius_group][radius_client]["key"] = radius_key              
    for aaa_console_line in aaa_console_lines:
        for aaa_console_access in aaa_console_line.children:
            dev_data["aaa"]["console"].append(aaa_console_access.text.replace(" ","",1))
    for aaa_vty_line in aaa_vty_lines:
        for aaa_vty_access in aaa_vty_line.children:
            aaa_vty_access = aaa_vty_access.text
            vty_pwd = re.findall(r'(password)\s\d+\s(\S+)', aaa_vty_access)
            vty_authorization = re.findall(r'authorization\scommands\s(\d+)\s(\S+)', aaa_vty_access)
            vty_transport = re.findall(r'transport\s(\S+)\s(.+)', aaa_vty_access)
            if vty_pwd:
                vty_pwd = vty_pwd[0][1]
                dev_data["aaa"]["vtys"]["password"] = vty_pwd
            if vty_authorization and "authorization" not in dev_data["aaa"]["vtys"]:
                dev_data["aaa"]["vtys"]["authorization"] = {}
                dev_data["aaa"]["vtys"]["authorization"]["commands"] = {}
                dev_data["aaa"]["vtys"]["authorization"]["commands"][int(vty_authorization[0][0])] = vty_authorization[0][1]
            elif vty_authorization and "authorization" in dev_data["aaa"]["vtys"]:
                dev_data["aaa"]["vtys"]["authorization"]["commands"][int(vty_authorization[0][0])] = vty_authorization[0][1]
            if vty_transport and "transport" not in dev_data["aaa"]["vtys"]:
                vty_dir = vty_transport[0][0]
                vty_protocols = vty_transport[0][1]
                dev_data["aaa"]["vtys"]["transport"] = {}
                dev_data["aaa"]["vtys"]["transport"][vty_dir] = []
                vty_protocols = vty_protocols.split(" ")
                for vty_protocol in vty_protocols:
                    if vty_protocol not in dev_data["aaa"]["vtys"]["transport"][vty_dir]:
                        dev_data["aaa"]["vtys"]["transport"][vty_dir].append(vty_protocol)
            elif vty_transport and "transport" in dev_data["aaa"]["vtys"]:
                vty_dir = vty_transport[0][0]
                vty_protocols = vty_transport[0][1]
                vty_protocols = vty_protocols.split(" ")
                for vty_protocol in vty_protocols:
                    if vty_protocol not in dev_data["aaa"]["vtys"]["transport"][vty_dir]:
                        dev_data["aaa"]["vtys"]["transport"][vty_dir].append(vty_protocol)

    return dev_data