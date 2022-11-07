#! /usr/bin/env python
"""
Script to parse SVIs configs
"""
import re
from netaddr import IPAddress

def audit_svi(parse_obj):
    """ Parse SVIs """

    dev_data = {}
    dev_data["svis"] = {}
    svi_lines = parse_obj.find_objects(r"^interface\sVlan\d+")

    for svi_line in svi_lines:
        vlan_id = int(svi_line.text.replace("interface Vlan", "").replace(" ", "", 1)) 
        dev_data["svis"][vlan_id] = {}
        dev_data["svis"][vlan_id]["enable"] = True
        for svi_data in svi_line.children:
            svi_data = svi_data.text.replace(" ", "", 1)
            svi_ip_match = re.match(r'ip\saddress\s\S+\s\S+$', svi_data)
            svi_ip_sec_match = re.match(r'ip\saddress\s\S+\s\S+\ssecondary$', svi_data)
            if "description" in svi_data:
                dev_data["svis"][vlan_id]["description"] = svi_data.replace("description ", "")
            elif "shutdown" in svi_data:
                dev_data["svis"][vlan_id]["enable"] = False
            elif "ip vrf" in svi_data:
                dev_data["svis"][vlan_id]["vrf"] = svi_data.replace("ip vrf forwarding ", "")
            elif "no ip address" in svi_data:
                pass
            elif svi_ip_match:
                ip_params = re.findall(r'ip\saddress\s(\S+)\s(\S+)$', svi_data)
                ip_add = ip_params[0][0]
                prefix = IPAddress(ip_params[0][1]).netmask_bits()
                dev_data["svis"][vlan_id]["ip_address"] = f'{ip_add}/{prefix}'
            elif svi_ip_sec_match and "ip_address_secondaries" not in dev_data["svis"][vlan_id]:
                dev_data["svis"][vlan_id]["ip_address_secondaries"] = []
                sec_ip_params = re.findall(r'ip\saddress\s(\S+)\s(\S+)\ssecondary', svi_data)
                sec_ip_add = sec_ip_params[0][0]
                sec_prefix = IPAddress(sec_ip_params[0][1]).netmask_bits()
                dev_data["svis"][vlan_id]["ip_address_secondaries"].append(f'{sec_ip_add}/{sec_prefix}')
            elif svi_ip_sec_match and "ip_address_secondaries" in dev_data["svis"][vlan_id]:
                sec_ip_params = re.findall(r'ip\saddress\s(\S+)\s(\S+)\ssecondary',svi_data)
                sec_ip_add = sec_ip_params[0][0]
                sec_prefix = IPAddress(sec_ip_params[0][1]).netmask_bits()
                dev_data["svis"][vlan_id]["ip_address_secondaries"].append(f'{sec_ip_add}/{sec_prefix}')
            elif "ip helper-address" in svi_data:
                if "ip_helper" not in dev_data["svis"][vlan_id]:
                    dev_data["svis"][vlan_id]["ip_helper"] = []
                    dev_data["svis"][vlan_id]["ip_helper"].append(svi_data.replace("ip helper-address ", ""))
                else:
                    dev_data["svis"][vlan_id]["ip_helper"].append(svi_data.replace("ip helper-address ", ""))
            elif "standby version" in svi_data:
                if "hsrp" not in dev_data["svis"][vlan_id]:
                    dev_data["svis"][vlan_id]["hsrp"] = {}
                    dev_data["svis"][vlan_id]["hsrp"]["version"] = int(svi_data.replace("standby version ", ""))
                else:
                    dev_data["svis"][vlan_id]["hsrp"]["version"] = int(svi_data.replace("standby version ", ""))
            elif "standby" in svi_data:
                hsrp_group = re.findall(r'standby\s(\d+)', svi_data)
                hsrp_group = hsrp_group[0]
                if "hsrp" not in dev_data["svis"][vlan_id]:
                    dev_data["svis"][vlan_id]["hsrp"] = {}
                    dev_data["svis"][vlan_id]["hsrp"]["hsrp_group"] = int(hsrp_group)
                    if f"standby {hsrp_group} ip" in svi_data:
                        dev_data["svis"][vlan_id]["hsrp"]["ip_add"] = svi_data.replace(f"standby {hsrp_group} ip ", "")
                    elif f"standby {hsrp_group} priority" in svi_data:
                        dev_data["svis"][vlan_id]["hsrp"]["priority"] = int(svi_data.replace(f"standby {hsrp_group} priority ", ""))
                    elif f"standby {hsrp_group} preempt" in svi_data:
                        dev_data["svis"][vlan_id]["hsrp"]["preempt"] = True
                    elif f"standby {hsrp_group} authentication" in svi_data:
                        dev_data["svis"][vlan_id]["hsrp"]["authentication"] = svi_data.replace(f"standby {hsrp_group} authentication ", "")
                else:
                    dev_data["svis"][vlan_id]["hsrp"]["hsrp_group"] = hsrp_group
                    if f"standby {hsrp_group} ip" in svi_data:
                        dev_data["svis"][vlan_id]["hsrp"]["ip_add"] = svi_data.replace(f"standby {hsrp_group} ip ", "")
                    elif f"standby {hsrp_group} priority" in svi_data:
                        dev_data["svis"][vlan_id]["hsrp"]["priority"] = int(svi_data.replace(f"standby {hsrp_group} priority ", ""))
                    elif f"standby {hsrp_group} preempt" in svi_data:
                        dev_data["svis"][vlan_id]["hsrp"]["preempt"] = True
                    elif f"standby {hsrp_group} authentication" in svi_data:
                        dev_data["svis"][vlan_id]["hsrp"]["authentication"] = svi_data.replace(f"standby {hsrp_group} authentication ", "")

    return dev_data

