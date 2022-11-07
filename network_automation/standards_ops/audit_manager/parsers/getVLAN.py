#! /usr/bin/env python
"""
Script to parse VLAN configs
"""

def audit_vlan(parse_obj):
    """ Parse VLANs """

    dev_data = {}
    dev_data["vlans"] = []
    vlan_lines = parse_obj.find_objects(r"^vlan\s\d+")
    
    for vlan_line in vlan_lines:
        for vlan_data in vlan_line.children:
            dev_data["vlans"].append(
                {
                    "id" : int(vlan_line.text.replace("vlan", "").replace(" ", "", 1)), 
                    "name": vlan_data.text.replace("name", "").replace(" ", "")
                }
            )
           
    return dev_data