#! /usr/bin/env python
"""
Script to parse Interfaces configs
"""

import regex as re

def audit_interfaces(parse_obj):
    """ Parse Interfaces """

    dev_data = {}
    dev_data["interfaces"] = {}
    dev_data["port_channels"] = {}
    if_lines = parse_obj.find_objects(r'^interface\s(?!Vlan\d+)')

    for if_line in if_lines:
        if "Port-channel" in if_line.text:
            po_id = if_line.text.replace("interface ", "")
            dev_data["port_channels"][po_id] = {} 
        elif "Port-channel" not in if_line.text:
            if_id = if_line.text.replace("interface ", "")
            dev_data["interfaces"][if_id] = {} 
            dev_data["interfaces"][if_id]["enable"] = True
        for if_data in if_line.children:
            if_data = if_data.text.replace(" ", "", 1)
            ### PARSING PORT CHANNELS ###
            if "Port-channel" in if_line.text:
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
                    dev_data["port_channels"][po_id]["mode"] = "access" 
                elif "switchport access vlan" in if_data:
                    dev_data["port_channels"][po_id]["access_vlan"] = if_data.replace("switchport access vlan ","")
                elif "switchport mode trunk" in if_data:
                        dev_data["port_channels"][po_id]["mode"] = "trunk"
                elif "switchport trunk" in if_data:
                    trunk_params = if_data.replace("switchport trunk ", "")
                    if "encapsulation" in trunk_params:
                        dev_data["port_channels"][po_id]["encapsulation"] = trunk_params.replace("encapsulation ", "" )
                    elif "native" in trunk_params:
                        dev_data["port_channels"][po_id]["native_vlan"] = trunk_params.replace("native vlan ", "" )
                    elif "allowed" in trunk_params:
                        dev_data["port_channels"][po_id]["vlans"] = trunk_params.replace("allowed vlan ", "" )
                ### STORM CONTROL EVALUATION ###
                elif "storm-control" in if_data:
                    storm_params = if_data.replace("storm-control ", " ")
                    storm_control_sect = re.findall(r'storm-control\s(\S+)',if_data)
                    storm_control_sect = storm_control_sect[0]
                    if "action" not in storm_control_sect and "storm_control" not in dev_data["port_channels"][po_id]:
                        dev_data["port_channels"][po_id]["storm_control"] = {}
                        dev_data["port_channels"][po_id]["storm_control"][storm_control_sect] = {}
                        if "pps" in storm_params:
                            storm_thresholds = re.findall(r'(?<=\w\slevel\spps\s)(\S+)(?(?=\s\S+)\s(\S+))', storm_params)
                            dev_data["port_channels"][po_id]["storm_control"][storm_control_sect]["pps"] = {} 
                            dev_data["port_channels"][po_id]["storm_control"][storm_control_sect]["pps"]["rising_threshold"] = storm_thresholds[0][0]
                            if storm_thresholds[0][1]:
                                dev_data["port_channels"][po_id]["storm_control"][storm_control_sect]["pps"]["falling_threshold"] = storm_thresholds[0][1]
                        elif "bps" in storm_params:
                            storm_thresholds = re.findall(r'(?<=\w\slevel\sbps\s)(\S+)(?(?=\s\S+)\s(\S+))', storm_params)
                            dev_data["port_channels"][po_id]["storm_control"][storm_control_sect]["bps"] = {} 
                            dev_data["port_channels"][po_id]["storm_control"][storm_control_sect]["bps"]["rising_threshold"] = storm_thresholds[0][0]
                            if storm_thresholds[0][1]:
                                dev_data["port_channels"][po_id]["storm_control"][storm_control_sect]["bps"]["falling_threshold"] = storm_thresholds[0][1]
                        else:
                            storm_thresholds = re.findall(r'(?<=\w\slevel\s)(\S+)(?(?=\s\S+)\s(\S+))', storm_params)
                            dev_data["port_channels"][po_id]["storm_control"][storm_control_sect]["level"] = {} 
                            dev_data["port_channels"][po_id]["storm_control"][storm_control_sect]["level"]["rising_threshold"] = storm_thresholds[0][0]
                            if storm_thresholds[0][1]:
                                dev_data["port_channels"][po_id]["storm_control"][storm_control_sect]["level"]["falling_threshold"] = storm_thresholds[0][1]
                    elif "action" not in storm_params and "storm_control" in dev_data["port_channels"][po_id]:
                        dev_data["port_channels"][po_id]["storm_control"][storm_control_sect] = {}
                        if "pps" in storm_params:
                            storm_thresholds = re.findall(r'(?<=\w\slevel\spps\s)(\S+)(?(?=\s\S+)\s(\S+))', storm_params)
                            dev_data["port_channels"][po_id]["storm_control"][storm_control_sect]["pps"] = {} 
                            dev_data["port_channels"][po_id]["storm_control"][storm_control_sect]["pps"]["rising_threshold"] = storm_thresholds[0][0]
                            if storm_thresholds[0][1]:
                                dev_data["port_channels"][po_id]["storm_control"][storm_control_sect]["pps"]["falling_threshold"] = storm_thresholds[0][1]
                        elif "bps" in storm_params:
                            storm_thresholds = re.findall(r'(?<=\w\slevel\sbps\s)(\S+)(?(?=\s\S+)\s(\S+))', storm_params)
                            dev_data["port_channels"][po_id]["storm_control"][storm_control_sect]["bps"] = {} 
                            dev_data["port_channels"][po_id]["storm_control"][storm_control_sect]["bps"]["rising_threshold"] = storm_thresholds[0][0]
                            if storm_thresholds[0][1]:
                                dev_data["port_channels"][po_id]["storm_control"][storm_control_sect]["bps"]["falling_threshold"] = storm_thresholds[0][1]
                        else:
                            storm_thresholds = re.findall(r'(?<=\w\slevel\s)(\S+)(?(?=\s\S+)\s(\S+))', storm_params)
                            dev_data["port_channels"][po_id]["storm_control"][storm_control_sect]["level"] = {} 
                            dev_data["port_channels"][po_id]["storm_control"][storm_control_sect]["level"]["rising_threshold"] = storm_thresholds[0][0]
                            if storm_thresholds[0][1]:
                                dev_data["port_channels"][po_id]["storm_control"][storm_control_sect]["level"]["falling_threshold"] = storm_thresholds[0][1]
            ### PARSING REGULAR INTERFACES ###
            elif "Port-channel" not in if_line.text:
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
                    dev_data["interfaces"][if_id]["mode"] = "access"
                elif "switchport access vlan" in if_data:
                        dev_data["interfaces"][if_id]["access_vlan"] = if_data.replace("switchport access vlan ","")
                elif "switchport mode trunk" in if_data:
                    dev_data["interfaces"][if_id]["mode"] = "trunk"
                elif "switchport trunk" in if_data:
                    trunk_params = if_data.replace("switchport trunk ", "")
                    if "encapsulation" in trunk_params:
                        dev_data["interfaces"][if_id]["encapsulation"] = trunk_params.replace("encapsulation ", "" )
                    elif "native" in trunk_params:
                        dev_data["interfaces"][if_id]["native_vlan"] = trunk_params.replace("native vlan ", "" )
                    elif "allowed" in trunk_params:
                        dev_data["interfaces"][if_id]["vlans"] = trunk_params.replace("allowed vlan ", "" )
                ### STORM CONTROL EVALUATION ###
                elif "storm-control" in if_data:
                    storm_params = if_data.replace("storm-control ", " ")
                    storm_control_sect = re.findall(r'storm-control\s(\S+)',if_data)
                    storm_control_sect = storm_control_sect[0]
                    if "action" not in storm_params and "storm_control" not in dev_data["interfaces"][if_id]:
                        dev_data["interfaces"][if_id]["storm_control"] = {}
                        dev_data["interfaces"][if_id]["storm_control"][storm_control_sect] = {}
                        if "pps" in storm_params:
                            storm_thresholds = re.findall(r'(?<=\w\slevel\spps\s)(\S+)(?(?=\s\S+)\s(\S+))', storm_params)
                            dev_data["interfaces"][if_id]["storm_control"][storm_control_sect]["pps"] = {} 
                            dev_data["interfaces"][if_id]["storm_control"][storm_control_sect]["pps"]["rising_threshold"] = storm_thresholds[0][0]
                            if storm_thresholds[0][1]:
                                dev_data["interfaces"][if_id]["storm_control"][storm_control_sect]["pps"]["falling_threshold"] = storm_thresholds[0][1]
                        elif "bps" in storm_params:
                            storm_thresholds = re.findall(r'(?<=\w\slevel\sbps\s)(\S+)(?(?=\s\S+)\s(\S+))', storm_params)
                            dev_data["interfaces"][if_id]["storm_control"][storm_control_sect]["bps"] = {} 
                            dev_data["interfaces"][if_id]["storm_control"][storm_control_sect]["bps"]["rising_threshold"] = storm_thresholds[0][0]
                            if storm_thresholds[0][1]:
                                dev_data["interfaces"][if_id]["storm_control"][storm_control_sect]["bps"]["falling_threshold"] = storm_thresholds[0][1]
                        else:
                            storm_thresholds = re.findall(r'(?<=\w\slevel\s)(\S+)(?(?=\s\S+)\s(\S+))', storm_params)
                            dev_data["interfaces"][if_id]["storm_control"][storm_control_sect]["level"] = {} 
                            dev_data["interfaces"][if_id]["storm_control"][storm_control_sect]["level"]["rising_threshold"] = storm_thresholds[0][0]
                            if storm_thresholds[0][1]:
                                dev_data["interfaces"][if_id]["storm_control"][storm_control_sect]["level"]["falling_threshold"] = storm_thresholds[0][1]
                    elif "action" not in storm_params and "storm_control" in dev_data["interfaces"][if_id]:
                        dev_data["interfaces"][if_id]["storm_control"][storm_control_sect] = {}
                        if "pps" in storm_params:
                            storm_thresholds = re.findall(r'(?<=\w\slevel\spps\s)(\S+)(?(?=\s\S+)\s(\S+))', storm_params)
                            dev_data["interfaces"][if_id]["storm_control"][storm_control_sect]["pps"] = {} 
                            dev_data["interfaces"][if_id]["storm_control"][storm_control_sect]["pps"]["rising_threshold"] = storm_thresholds[0][0]
                            if storm_thresholds[0][1]:
                                dev_data["interfaces"][if_id]["storm_control"][storm_control_sect]["pps"]["falling_threshold"] = storm_thresholds[0][1]
                        elif "bps" in storm_params:
                            storm_thresholds = re.findall(r'(?<=\w\slevel\sbps\s)(\S+)(?(?=\s\S+)\s(\S+))', storm_params)
                            dev_data["interfaces"][if_id]["storm_control"][storm_control_sect]["bps"] = {} 
                            dev_data["interfaces"][if_id]["storm_control"][storm_control_sect]["bps"]["rising_threshold"] = storm_thresholds[0][0]
                            if storm_thresholds[0][1]:
                                dev_data["interfaces"][if_id]["storm_control"][storm_control_sect]["bps"]["falling_threshold"] = storm_thresholds[0][1]
                        else:
                            storm_thresholds = re.findall(r'(?<=\w\slevel\s)(\S+)(?(?=\s\S+)\s(\S+))', storm_params)
                            dev_data["interfaces"][if_id]["storm_control"][storm_control_sect]["level"] = {} 
                            dev_data["interfaces"][if_id]["storm_control"][storm_control_sect]["level"]["rising_threshold"] = storm_thresholds[0][0]
                            if storm_thresholds[0][1]:
                                dev_data["interfaces"][if_id]["storm_control"][storm_control_sect]["level"]["falling_threshold"] = storm_thresholds[0][1]

                    

    return dev_data