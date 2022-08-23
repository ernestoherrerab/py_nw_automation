#! /usr/bin/env python
"""
Script to parse Interfaces configs
"""

import regex as re
from netaddr import valid_ipv4, IPAddress

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
            dev_data["port_channels"][po_id]["enable"] = True
            dev_data["port_channels"][po_id]["speed"] = "auto"
            dev_data["port_channels"][po_id]["duplex"] = "auto"
        elif "Port-channel" not in if_line.text:
            if_id = if_line.text.replace("interface ", "")
            dev_data["interfaces"][if_id] = {} 
            dev_data["interfaces"][if_id]["enable"] = True
            dev_data["interfaces"][if_id]["nonegotiate"] = False
            dev_data["interfaces"][if_id]["speed"] = "auto"
            dev_data["interfaces"][if_id]["duplex"] = "auto"
        for if_data in if_line.children:
            if_data = if_data.text.replace(" ", "", 1)
            ### PARSING PORT CHANNELS ###
            ### PARSE DESCRIPTION, STATUS, VRF, IP ADDRESS, HELPER ADDRESS ###
            if "Port-channel" in if_line.text:
                po_ip_match = re.match(r'ip\saddress\s\S+\s\S+$', if_data)
                po_ip_sec_match = re.match(r'ip\saddress\s\S+\s\S+\ssecondary$', if_data)
                if "description" in if_data:
                    dev_data["port_channels"][po_id]["description"] = if_data.replace("description ", "")
                elif "shutdown" in if_data:
                    dev_data["port_channels"][po_id]["enable"] = False
                elif "speed" in if_data:
                    dev_data["port_channels"][po_id]["speed"] = if_data.replace("speed ", "")
                elif "duplex" in if_data:
                    dev_data["port_channels"][po_id]["duplex"] = if_data.replace("duplex ", "")
                elif "ip vrf" in if_data:
                    dev_data["port_channels"][po_id]["vrf"] = if_data.replace("ip vrf forwarding ", "")
                elif po_ip_match:
                    po_ip_params = re.findall(r'ip\saddress\s(\S+)\s(\S+)$', if_data)
                    po_ip_add = po_ip_params[0][0]
                    po_prefix = IPAddress(po_ip_params[0][1]).netmask_bits()
                    dev_data["port_channels"][po_id]["ip_address"] = f'{po_ip_add}/{po_prefix}'
                elif po_ip_sec_match and "ip_address_secondaries" not in dev_data["port_channels"][po_id]:
                    dev_data["port_channels"][po_id]["ip_address_secondaries"] = []
                    po_sec_ip_params = re.findall(r'ip\saddress\s(\S+)\s(\S+)\ssecondary', if_data)
                    po_sec_ip_add = po_sec_ip_params[0][0]
                    po_sec_prefix = IPAddress(po_sec_ip_params[0][1]).netmask_bits()
                    dev_data["port_channels"][po_id]["ip_address_secondaries"].append(f'{po_sec_ip_add}/{po_sec_prefix}')
                elif po_ip_sec_match and "ip_address_secondaries" in dev_data["port_channels"][po_id]:
                    po_sec_ip_params = re.findall(r'ip\saddress\s(\S+)\s(\S+)\ssecondary',if_data)
                    po_sec_ip_add = po_sec_ip_params[0][0]
                    po_sec_prefix = IPAddress(po_sec_ip_params[0][1]).netmask_bits()
                    dev_data["port_channels"][po_id]["ip_address_secondaries"].append(f'{po_sec_ip_add}/{po_sec_prefix}')
                elif "ip helper-address" in if_data:
                    if "ip_helper" not in dev_data["port_channels"][po_id]:
                        dev_data["port_channels"][po_id]["ip_helper"] = []
                        dev_data["port_channels"][po_id]["ip_helper"].append(if_data.replace("ip helper-address ", ""))
                    else:
                        dev_data["port_channels"][po_id]["ip_helper"].append(if_data.replace("ip helper-address ", ""))
                ### PARSE HSRP ###
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
                ### PARSE SWITCHPORT CONFIGS ###
                elif "switchport nonegotiate" in if_data:
                    dev_data["port_channels"][po_id]["nonegotiate"] = True
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
                    elif "action" in storm_control_sect and "storm_control" not in dev_data["port_channels"][po_id]:
                        storm_action = storm_params.replace(" action ", "")
                        dev_data["port_channels"][po_id]["storm_control"] = {}
                        dev_data["port_channels"][po_id]["storm_control"][storm_control_sect] = []
                        dev_data["port_channels"][po_id]["storm_control"][storm_control_sect].append(storm_action)
                    elif "action" in storm_control_sect and "storm_control" in dev_data["port_channels"][po_id]:
                        storm_action = storm_params.replace(" action ", "")
                        if storm_control_sect not in dev_data["port_channels"][po_id]["storm_control"]:
                            dev_data["port_channels"][po_id]["storm_control"][storm_control_sect] = []
                            dev_data["port_channels"][po_id]["storm_control"][storm_control_sect].append(storm_action)
                        elif storm_control_sect in dev_data["port_channels"][po_id]["storm_control"]:
                            dev_data["port_channels"][po_id]["storm_control"][storm_control_sect].append(storm_action)
                ### SPANNING TREE EVALUATION ###
                elif "spanning-tree" in if_data:
                    if "spanning_tree" not in dev_data["port_channels"][po_id]:
                        stp_params = re.findall(r'(?<=spanning-tree\s)(\S+)(?(?=\s\S+)\s(\S+))', if_data)
                        dev_data["port_channels"][po_id]["spanning_tree"] = {}
                        if stp_params[0][0] == "bpduguard" or stp_params[0][0] == "guard":
                            dev_data["port_channels"][po_id]["spanning_tree"][stp_params[0][0]] = stp_params[0][1]
                        elif stp_params[0][0] == "portfast" and stp_params[0][1] == "":
                            dev_data["port_channels"][po_id]["spanning_tree"][stp_params[0][0]] = "enable"
                        elif stp_params[0][0] == "portfast" and stp_params[0][1] != "":
                            dev_data["port_channels"][po_id]["spanning_tree"][stp_params[0][0]] = stp_params[0][1]
                    elif "spanning_tree" in dev_data["port_channels"][po_id]:
                        stp_params = re.findall(r'(?<=spanning-tree\s)(\S+)(?(?=\s\S+)\s(\S+))', if_data)
                        if stp_params[0][0] == "bpduguard" or stp_params[0][0] == "guard":
                            dev_data["port_channels"][po_id]["spanning_tree"][stp_params[0][0]] = stp_params[0][1]
                        elif stp_params[0][0] == "portfast" and stp_params[0][1] == "":
                            dev_data["port_channels"][po_id]["spanning_tree"][stp_params[0][0]] = "enable"
                        elif stp_params[0][0] == "portfast" and stp_params[0][1] != "":
                            dev_data["port_channels"][po_id]["spanning_tree"][stp_params[0][0]] = stp_params[0][1]
                ### IP ARP INSPECTION EVALUATION ###
                elif "ip arp inspection" in if_data:
                    dev_data["port_channels"][po_id]["ip_arp_inspection"] = if_data.replace("ip arp inspection ", "")
                ### QOS TRUST EVALUATION ###
                elif "mls qos" in if_data and "mls_qos" not in dev_data["port_channels"][po_id]:
                    mls_qos_params = re.findall(r'mls\sqos\s(\S+)\s(\S+)', if_data)
                    dev_data["port_channels"][po_id]["mls_qos"] = {}
                    dev_data["port_channels"][po_id]["mls_qos"][mls_qos_params[0][0]] = mls_qos_params[0][1]
                elif "mls qos" in if_data and "mls_qos" in dev_data["port_channels"][po_id]:
                    mls_qos_params = re.findall(r'mls\sqos\s(\S+)\s(\S+)', if_data)
                    dev_data["port_channels"][po_id]["mls_qos"][mls_qos_params[0][0]] = mls_qos_params[0][1]

            ### PARSING REGULAR INTERFACES ###
            elif "Port-channel" not in if_line.text:
                ### PARSING INTERFACES ###
                if_ip_match = re.match(r'ip\saddress\s\S+\s\S+$', if_data)
                if_ip_sec_match = re.match(r'ip\saddress\s\S+\s\S+\ssecondary$', if_data)
                ### PARSE DESCRIPTION, STATUS, VRF, IP ADDRESS, HELPER ADDRESS ###
                if "description" in if_data:
                    dev_data["interfaces"][if_id]["description"] = if_data.replace("description ", "")
                elif "shutdown" in if_data:
                    dev_data["interfaces"][if_id]["enable"] = False
                elif "speed" in if_data:
                    dev_data["interfaces"][if_id]["speed"] = if_data.replace("speed ", "")
                elif "duplex" in if_data:
                    dev_data["interfaces"][if_id]["duplex"] = if_data.replace("duplex ", "")
                elif "ip vrf" in if_data:
                    dev_data["interfaces"][if_id]["vrf"] = if_data.replace("ip vrf forwarding ", "")
                elif if_ip_match:
                    if_ip_params = re.findall(r'ip\saddress\s(\S+)\s(\S+)$', if_data)
                    if_ip_add = if_ip_params[0][0]
                    if_prefix = IPAddress(if_ip_params[0][1]).netmask_bits()
                    dev_data["interfaces"][if_id]["ip_address"] = f'{if_ip_add}/{if_prefix}'
                elif if_ip_sec_match and "ip_address_secondaries" not in dev_data["interfaces"][if_id]:
                    dev_data["interfaces"][if_id]["ip_address_secondaries"] = []
                    if_sec_ip_params = re.findall(r'ip\saddress\s(\S+)\s(\S+)\ssecondary', if_data)
                    if_sec_ip_add = if_sec_ip_params[0][0]
                    if_sec_prefix = IPAddress(if_sec_ip_params[0][1]).netmask_bits()
                    dev_data["interfaces"][if_id]["ip_address_secondaries"].append(f'{if_sec_ip_add}/{if_sec_prefix}')
                elif if_ip_sec_match and "ip_address_secondaries" in dev_data["interfaces"][if_id]:
                    if_sec_ip_params = re.findall(r'ip\saddress\s(\S+)\s(\S+)\ssecondary',if_data)
                    if_sec_ip_add = if_sec_ip_params[0][0]
                    if_sec_prefix = IPAddress(if_sec_ip_params[0][1]).netmask_bits()
                    dev_data["interfaces"][if_id]["ip_address_secondaries"].append(f'{if_sec_ip_add}/{if_sec_prefix}')
                elif "ip helper-address" in if_data:
                    if "ip_helper" not in dev_data["port_channels"][po_id]:
                        dev_data["interfaces"][if_id]["ip_helper"] = []
                        dev_data["interfaces"][if_id]["ip_helper"].append(if_data.replace("ip helper-address ", ""))
                    else:
                        dev_data["interfaces"][if_id]["ip_helper"].append(if_data.replace("ip helper-address ", ""))
                ### PARSE HSRP ###
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
                ### PARSE SWITCHPORT CONFIGS ###
                elif "switchport nonegotiate" in if_data:
                    dev_data["interfaces"][if_id]["nonegotiate"] = True
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
                    elif "action" in storm_control_sect and "storm_control" not in dev_data["interfaces"][if_id]:
                        storm_action = storm_params.replace(" action ", "")
                        dev_data["interfaces"][if_id]["storm_control"] = {}
                        dev_data["interfaces"][if_id]["storm_control"][storm_control_sect] = []
                        dev_data["interfaces"][if_id]["storm_control"][storm_control_sect].append(storm_action)
                    elif "action" in storm_control_sect and "storm_control" in dev_data["interfaces"][if_id]:
                        storm_action = storm_params.replace(" action ", "")
                        if storm_control_sect not in dev_data["interfaces"][if_id]["storm_control"]:
                            dev_data["interfaces"][if_id]["storm_control"][storm_control_sect] = []
                            dev_data["interfaces"][if_id]["storm_control"][storm_control_sect].append(storm_action)
                        elif storm_control_sect in dev_data["port_channels"][po_id]["storm_control"]:
                            dev_data["interfaces"][if_id]["storm_control"][storm_control_sect].append(storm_action)
                ### SPANNING TREE EVALUATION ###
                elif "spanning-tree" in if_data:
                    if "spanning_tree" not in dev_data["interfaces"][if_id]:
                        stp_params = re.findall(r'(?<=spanning-tree\s)(\S+)(?(?=\s\S+)\s(\S+))', if_data)
                        dev_data["interfaces"][if_id]["spanning_tree"] = {}
                        if stp_params[0][0] == "bpduguard" or stp_params[0][0] == "guard":
                            dev_data["interfaces"][if_id]["spanning_tree"][stp_params[0][0]] = stp_params[0][1]
                        elif stp_params[0][0] == "portfast" and stp_params[0][1] == "":
                            dev_data["interfaces"][if_id]["spanning_tree"][stp_params[0][0]] = "enable"
                        elif stp_params[0][0] == "portfast" and stp_params[0][1] != "":
                            dev_data["interfaces"][if_id]["spanning_tree"][stp_params[0][0]] = stp_params[0][1]
                    elif "spanning_tree" in dev_data["interfaces"][if_id]:
                        stp_params = re.findall(r'(?<=spanning-tree\s)(\S+)(?(?=\s\S+)\s(\S+))', if_data)
                        if stp_params[0][0] == "bpduguard" or stp_params[0][0] == "guard":
                            dev_data["interfaces"][if_id]["spanning_tree"][stp_params[0][0]] = stp_params[0][1]
                        elif stp_params[0][0] == "portfast" and stp_params[0][1] == "":
                            dev_data["interfaces"][if_id]["spanning_tree"][stp_params[0][0]] = "enable"
                        elif stp_params[0][0] == "portfast" and stp_params[0][1] != "":
                            dev_data["interfaces"][if_id]["spanning_tree"][stp_params[0][0]] = stp_params[0][1]
                ### UDLD EVALUATION ###
                elif "udld" in if_data:
                    dev_data["interfaces"][if_id]["udld"] = {}
                    dev_data["interfaces"][if_id]["udld"]["mode"] = if_data.replace("udld port ", "")
                ### IP ARP INSPECTION EVALUATION ###
                elif "ip arp inspection" in if_data:
                    dev_data["interfaces"][if_id]["ip_arp_inspection"] = if_data.replace("ip arp inspection ", "")
                ### QOS TRUST EVALUATION ###
                elif "mls qos" in if_data and "mls_qos" not in dev_data["interfaces"][if_id]:
                    mls_qos_params = re.findall(r'mls\sqos\s(\S+)\s(\S+)', if_data)
                    dev_data["interfaces"][if_id]["mls_qos"] = {}
                    dev_data["interfaces"][if_id]["mls_qos"][mls_qos_params[0][0]] = mls_qos_params[0][1]
                elif "mls qos" in if_data and "mls_qos" in dev_data["interfaces"][if_id]:
                    mls_qos_params = re.findall(r'mls\sqos\s(\S+)\s(\S+)', if_data)
                    dev_data["interfaces"][if_id]["mls_qos"][mls_qos_params[0][0]] = mls_qos_params[0][1]
                ### PORT CHANNEL MEMBERSHIP EVALUATION ###
                if "channel-protocol" in if_data:
                    dev_data["interfaces"][if_id]["channel_protocol"] = if_data.replace("channel-protocol ", "")
                if "channel-group"in if_data:
                    port_ch_parameters = re.findall(r'channel-group\s(\d+)\smode\s(\S+)', if_data)
                    dev_data["interfaces"][if_id]["channel_group"] = {}
                    dev_data["interfaces"][if_id]["channel_group"]["id"] = int(port_ch_parameters[0][0])
                    dev_data["interfaces"][if_id]["channel_group"]["mode"] = port_ch_parameters[0][1]                          

    return dev_data