from ciscoconfparse import CiscoConfParse
import network_automation.audit_manager.audit_manager.getConfig as get_config

def do_audit(username, password, depth_levels=3):
    """ Parse configurations """
    devs_data = []
    dev_configs = get_config.get_config(username, password, depth_levels)

    for dev_config in dev_configs:
        dev_data = {}
        dev_data[dev_config[0]] = {}
        parse_obj = CiscoConfParse(dev_config[1])

        """ Parse AAA """
        dev_data[dev_config[0]]["aaa"] = {}
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
        dev_data[dev_config[0]]["aaa"]["authentication"] = []
        dev_data[dev_config[0]]["aaa"]["authorization"] = []
        dev_data[dev_config[0]]["aaa"]["accounting"] = []
        dev_data[dev_config[0]]["aaa"]["tacacs_server"] = []
        dev_data[dev_config[0]]["aaa"]["tacacs_server_group"] = []
        dev_data[dev_config[0]]["aaa"]["radius_server"] = []
        dev_data[dev_config[0]]["aaa"]["radius_server_group"] = []
        dev_data[dev_config[0]]["aaa"]["usernames"] = []
        dev_data[dev_config[0]]["aaa"]["enable_pass"] = aaa_enable_line[0].text.replace("enable", "").replace(" ", "", 1)
        dev_data[dev_config[0]]["aaa"]["console"] = []
        dev_data[dev_config[0]]["aaa"]["vtys"] = []
        for aaa_authentication_line in aaa_authentication_lines:
            dev_data[dev_config[0]]["aaa"]["authentication"].append(aaa_authentication_line.text.replace("aaa authentication", "").replace(" ", "", 1))
        for aaa_authorization_line in aaa_authorization_lines:
            dev_data[dev_config[0]]["aaa"]["authorization"].append(aaa_authorization_line.text.replace("aaa authorization", "").replace(" ", "", 1))
        for aaa_accounting_line in aaa_accounting_lines:
            dev_data[dev_config[0]]["aaa"]["accounting"].append(aaa_accounting_line.text.replace("aaa accounting ", "").replace(" ", "", 1))
        for aaa_tacacs_line in aaa_tacacs_lines:
            dev_data[dev_config[0]]["aaa"]["tacacs_server"].append(aaa_tacacs_line.text.replace("tacacs-server ", ""))
        for aaa_radius_line in aaa_radius_lines:
            dev_data[dev_config[0]]["aaa"]["radius_server"].append(aaa_radius_line.text.replace("radius-server ", ""))
        for aaa_usernames_line in aaa_usernames_lines:
            dev_data[dev_config[0]]["aaa"]["usernames"].append(aaa_usernames_line.text.replace("username ", ""))
        for aaa_tacacs_group_line in aaa_tacacs_group_lines:
            for aaa_tacacs_group_server in aaa_tacacs_group_line.children:
                dev_data[dev_config[0]]["aaa"]["tacacs_server_group"].append(aaa_tacacs_group_server.text.replace(" ","",1))
        for aaa_radius_group_line in aaa_radius_group_lines:
            for aaa_radius_group_server in aaa_radius_group_line.children:
                dev_data[dev_config[0]]["aaa"]["radius_server_group"].append(aaa_radius_group_server.text.replace(" ","",1))
        for aaa_console_line in aaa_console_lines:
            for aaa_console_access in aaa_console_line.children:
                dev_data[dev_config[0]]["aaa"]["console"].append(aaa_console_access.text.replace(" ","",1))
        for aaa_vty_line in aaa_vty_lines:
            for aaa_vty_access in aaa_vty_line.children:
                if aaa_vty_access.text.replace(" ","",1) not in dev_data[dev_config[0]]["aaa"]["vtys"]:
                    dev_data[dev_config[0]]["aaa"]["vtys"].append(aaa_vty_access.text.replace(" ","",1))


        devs_data.append(dev_data)

    print(devs_data)


    
