#! /usr/bin/env python
"""
Script to parse AAA configs
"""

from ciscoconfparse import CiscoConfParse

def audit_aaa(parse_obj):
        dev_data = {}
        """ Parse AAA """
        dev_data["aaa"] = {}
        dev_data["aaa"]["aaa"] = {}
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
        dev_data["aaa"]["aaa"]["authentication"] = []
        dev_data["aaa"]["aaa"]["authorization"] = []
        dev_data["aaa"]["aaa"]["accounting"] = []
        dev_data["aaa"]["aaa"]["tacacs_server"] = []
        dev_data["aaa"]["aaa"]["tacacs_server_group"] = {}
        dev_data["aaa"]["aaa"]["radius_server"] = []
        dev_data["aaa"]["aaa"]["radius_server_group"] = {}
        dev_data["aaa"]["aaa"]["usernames"] = []
        dev_data["aaa"]["aaa"]["enable_pass"] = aaa_enable_line[0].text.replace("enable", "").replace(" ", "", 1)
        dev_data["aaa"]["aaa"]["console"] = []
        dev_data["aaa"]["aaa"]["vtys"] = []
        for aaa_authentication_line in aaa_authentication_lines:
            dev_data["aaa"]["aaa"]["authentication"].append(aaa_authentication_line.text.replace("aaa authentication", "").replace(" ", "", 1))
        for aaa_authorization_line in aaa_authorization_lines:
            dev_data["aaa"]["aaa"]["authorization"].append(aaa_authorization_line.text.replace("aaa authorization", "").replace(" ", "", 1))
        for aaa_accounting_line in aaa_accounting_lines:
            dev_data["aaa"]["aaa"]["accounting"].append(aaa_accounting_line.text.replace("aaa accounting ", "").replace(" ", "", 1))
        for aaa_tacacs_line in aaa_tacacs_lines:
            dev_data["aaa"]["aaa"]["tacacs_server"].append(aaa_tacacs_line.text.replace("tacacs-server ", ""))
        for aaa_radius_line in aaa_radius_lines:
            dev_data["aaa"]["aaa"]["radius_server"].append(aaa_radius_line.text.replace("radius-server ", ""))
        for aaa_usernames_line in aaa_usernames_lines:
            dev_data["aaa"]["aaa"]["usernames"].append(aaa_usernames_line.text.replace("username ", ""))
        for aaa_tacacs_group_line in aaa_tacacs_group_lines:
            tacacs_group = aaa_tacacs_group_line.re_match_typed(r'^aaa group server tacacs\+\s+(\S+)', default='')
            dev_data["aaa"]["aaa"]["tacacs_server_group"][tacacs_group] = []
            for aaa_tacacs_group_server in aaa_tacacs_group_line.children:
                dev_data["aaa"]["aaa"]["tacacs_server_group"][tacacs_group].append(aaa_tacacs_group_server.text.replace(" ","",1))
        for aaa_radius_group_line in aaa_radius_group_lines:
            radius_group = aaa_radius_group_line.re_match_typed(r'^aaa server radius\s+(\S+)', default='')
            dev_data["aaa"]["aaa"]["radius_server_group"][radius_group] = []
            for aaa_radius_group_server in aaa_radius_group_line.children:
                dev_data["aaa"]["aaa"]["radius_server_group"][radius_group].append(aaa_radius_group_server.text.replace(" ","",1))
        for aaa_console_line in aaa_console_lines:
            for aaa_console_access in aaa_console_line.children:
                dev_data["aaa"]["aaa"]["console"].append(aaa_console_access.text.replace(" ","",1))
        for aaa_vty_line in aaa_vty_lines:
            for aaa_vty_access in aaa_vty_line.children:
                if aaa_vty_access.text.replace(" ","",1) not in dev_data["aaa"]["aaa"]["vtys"]:
                    dev_data["aaa"]["aaa"] ["vtys"].append(aaa_vty_access.text.replace(" ","",1))
        return dev_data