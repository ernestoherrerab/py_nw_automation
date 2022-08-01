#! /usr/bin/env python
"""
Script to parse Interfaces configs
"""

import re 

def audit_interfaces(parse_obj):
    """ Parse Interfaces """

    dev_data = {}
    dev_data["interfaces"] = {}
    dev_data["port_channels"] = {}
    if_lines = parse_obj.find_objects(r'^interface\s(?!Vlan\d+)')

    for if_line in if_lines:
        for if_data in if_line.children:
            if_data = if_data.text.replace(" ", "", 1)
            if "Port-channel" in if_line.text:
                po_id = if_line.text.replace("interface ", "")
                dev_data["port_channels"][po_id] = {} 
                dev_data["port_channels"][po_id]["enable"] = True
                if "description" in if_data:
                   dev_data["port_channels"][po_id]["description"] = if_data.replace("description ", "")
                elif "shutdown" in if_data:
                    dev_data["port_channels"][po_id]["enable"] = False
                elif "ip vrf" in if_data:
                    dev_data["port_channels"][po_id]["vrf"] = if_data.replace("ip vrf forwarding ", "")
                elif "ip address" in if_data:
                    ip_params = if_data.replace("ip address ", "").split()
                    dev_data["port_channels"][po_id]["ip_address"] = ip_params[0]
                    dev_data["port_channels"][po_id]["subnet_mask"] = ip_params[1]
                elif "ip helper-address" in if_data:
                    if "ip_helper" not in dev_data["port_channels"][po_id]:
                        dev_data["port_channels"][po_id]["ip_helper"] = []
                        dev_data["port_channels"][po_id]["ip_helper"].append(if_data.replace("ip helper-address ", ""))
                    else:
                        dev_data["port_channels"][po_id]["ip_helper"].append(if_data.replace("ip helper-address ", ""))
                elif "standby version" in if_data:
                    if "hsrp" not in dev_data["port_channels"][po_id]:
                        dev_data["port_channels"][po_id]["hsrp"] = {}
                        dev_data["port_channels"][po_id]["hsrp"]["version"] = int(if_data.replace("standby version ", ""))
                    else:
                        dev_data["port_channels"][po_id]["hsrp"]["version"] = int(if_data.replace("standby version ", ""))
                elif "standby" in if_data:
                    hsrp_group = re.findall(r'standby\s(\d+)', if_data)
                    hsrp_group = hsrp_group[0]
                    if "hsrp" not in dev_data["port_channels"][po_id]:
                        dev_data["port_channels"][po_id]["hsrp"] = {}
                        dev_data["port_channels"][po_id]["hsrp"]["hsrp_group"] = int(hsrp_group)
                        if f"standby {hsrp_group} ip" in if_data:
                            dev_data["port_channels"][po_id]["hsrp"]["ip_add"] = if_data.replace(f"standby {hsrp_group} ip ", "")
                        elif f"standby {hsrp_group} priority" in if_data:
                            dev_data["port_channels"][po_id]["hsrp"]["priority"] = int(if_data.replace(f"standby {hsrp_group} priority ", ""))
                        elif f"standby {hsrp_group} preempt" in if_data:
                            dev_data["port_channels"][po_id]["hsrp"]["preempt"] = True
                        elif f"standby {hsrp_group} authentication" in if_data:
                            dev_data["port_channels"][po_id]["hsrp"]["authentication"] = if_data.replace(f"standby {hsrp_group} authentication ", "")
                    else:
                        dev_data["port_channels"][po_id]["hsrp"]["hsrp_group"] = hsrp_group
                        if f"standby {hsrp_group} ip" in if_data:
                            dev_data["port_channels"][po_id]["hsrp"]["ip_add"] = if_data.replace(f"standby {hsrp_group} ip ", "")
                        elif f"standby {hsrp_group} priority" in if_data:
                            dev_data["port_channels"][po_id]["hsrp"]["priority"] = int(if_data.replace(f"standby {hsrp_group} priority ", ""))
                        elif f"standby {hsrp_group} preempt" in if_data:
                            dev_data["port_channels"][po_id]["hsrp"]["preempt"] = True
                        elif f"standby {hsrp_group} authentication" in if_data:
                            dev_data["port_channels"][po_id]["hsrp"]["authentication"] = if_data.replace(f"standby {hsrp_group} authentication ", "")
                elif "switchport mode access" in if_data:
                    if "mode" not in dev_data["port_channels"][po_id]:
                        dev_data["port_channels"][po_id]["mode"] = {}
                        dev_data["port_channels"][po_id]["mode"]["access"] = True 
                    else:
                        dev_data["port_channels"][po_id]["mode"]["access"] = True 
                elif "switchport access vlan" in if_data:
                    if "mode" not in dev_data["port_channels"][po_id]:
                        dev_data["port_channels"][po_id]["mode"] = {}
                        dev_data["port_channels"][po_id]["mode"]["vlan"] = if_data.replace("switchport access vlan ","")
                    else:
                        dev_data["port_channels"][po_id]["mode"]["vlan"] = if_data.replace("switchport access vlan ","")
                elif "switchport mode trunk" in if_data:
                    if "mode" not in dev_data["port_channels"][po_id]:
                        dev_data["port_channels"][po_id]["mode"] = {}
                        dev_data["port_channels"][po_id]["mode"]["trunk"] = True 
                    else:
                        dev_data["port_channels"][po_id]["mode"]["trunk"] = True 

            elif "Port-channel" not in if_line.text:
                if_id = if_line.text.replace("interface ", "")
                dev_data["interfaces"][if_id] = {} 
                dev_data["interfaces"][if_id]["enable"] = True
                if "description" in if_data:
                   dev_data["interfaces"][if_id]["description"] = if_data.replace("description ", "")
                elif "shutdown" in if_data:
                    dev_data["interfaces"][if_id]["enable"] = False
                elif "ip vrf" in if_data:
                    dev_data["interfaces"][if_id]["vrf"] = if_data.replace("ip vrf forwarding ", "")
                elif "ip address" in if_data:
                    ip_params = if_data.replace("ip address ", "").split()
                    dev_data["interfaces"][if_id]["ip_address"] = ip_params[0]
                    dev_data["interfaces"][if_id]["subnet_mask"] = ip_params[1]
                elif "ip helper-address" in if_data:
                    if "ip_helper" not in dev_data["port_channels"][po_id]:
                        dev_data["interfaces"][if_id]["ip_helper"] = []
                        dev_data["interfaces"][if_id]["ip_helper"].append(if_data.replace("ip helper-address ", ""))
                    else:
                        dev_data["interfaces"][if_id]["ip_helper"].append(if_data.replace("ip helper-address ", ""))
                elif "standby version" in if_data:
                    if "hsrp" not in dev_data["interfaces"][if_id]:
                        dev_data["interfaces"][if_id]["hsrp"] = {}
                        dev_data["interfaces"][if_id]["hsrp"]["version"] = int(if_data.replace("standby version ", ""))
                    else:
                        dev_data["interfaces"][if_id]["hsrp"]["version"] = int(if_data.replace("standby version ", ""))
                elif "standby" in if_data:
                    hsrp_group = re.findall(r'standby\s(\d+)', if_data)
                    hsrp_group = hsrp_group[0]
                    if "hsrp" not in dev_data["interfaces"][if_id]:
                        dev_data["interfaces"][if_id]["hsrp"] = {}
                        dev_data["interfaces"][if_id]["hsrp"]["hsrp_group"] = int(hsrp_group)
                        if f"standby {hsrp_group} ip" in if_data:
                            dev_data["interfaces"][if_id]["hsrp"]["ip_add"] = if_data.replace(f"standby {hsrp_group} ip ", "")
                        elif f"standby {hsrp_group} priority" in if_data:
                            dev_data["interfaces"][if_id]["hsrp"]["priority"] = int(if_data.replace(f"standby {hsrp_group} priority ", ""))
                        elif f"standby {hsrp_group} preempt" in if_data:
                            dev_data["interfaces"][if_id]["hsrp"]["preempt"] = True
                        elif f"standby {hsrp_group} authentication" in if_data:
                            dev_data["interfaces"][if_id]["hsrp"]["authentication"] = if_data.replace(f"standby {hsrp_group} authentication ", "")
                    else:
                        dev_data["interfaces"][if_id]["hsrp"]["hsrp_group"] = hsrp_group
                        if f"standby {hsrp_group} ip" in if_data:
                            dev_data["interfaces"][if_id]["hsrp"]["ip_add"] = if_data.replace(f"standby {hsrp_group} ip ", "")
                        elif f"standby {hsrp_group} priority" in if_data:
                            dev_data["interfaces"][if_id]["hsrp"]["priority"] = int(if_data.replace(f"standby {hsrp_group} priority ", ""))
                        elif f"standby {hsrp_group} preempt" in if_data:
                            dev_data["interfaces"][if_id]["hsrp"]["preempt"] = True
                        elif f"standby {hsrp_group} authentication" in if_data:
                            dev_data["interfaces"][if_id]["hsrp"]["authentication"] = if_data.replace(f"standby {hsrp_group} authentication ", "")
                elif "switchport mode access" in if_data:
                    if "mode" not in dev_data["interfaces"][if_id]:
                        dev_data["interfaces"][if_id]["mode"] = {}
                        dev_data["interfaces"][if_id]["mode"]["access"] = True 
                    else:
                        dev_data["interfaces"][if_id]["mode"]["access"] = True 
                elif "switchport access vlan" in if_data:
                    if "mode" not in dev_data["interfaces"][if_id]:
                        dev_data["interfaces"][if_id]["mode"] = {}
                        dev_data["interfaces"][if_id]["mode"]["vlan"] = if_data.replace("switchport access vlan ","")
                    else:
                        dev_data["interfaces"][if_id]["mode"]["vlan"] = if_data.replace("switchport access vlan ","")
                elif "switchport mode trunk" in if_data:
                    if "mode" not in dev_data["interfaces"][if_id]:
                        dev_data["interfaces"][if_id]["mode"] = {}
                        dev_data["interfaces"][if_id]["mode"]["trunk"] = True 
                    else:
                        dev_data["interfaces"][if_id]["mode"]["trunk"] = True 


    return dev_data