#! /usr/bin/env python
"""
Script to parse BGP configs
"""
import re

def audit_bgp(parse_obj):
    """ Parse BGP """
    dev_data = {}
    dev_data["router_bgp"] = {}
    bgp_process = parse_obj.find_objects(r'^router\sbgp')
    
    for bgp_lines in bgp_process:
        dev_data["router_bgp"]["as"] = bgp_lines.text.replace("router bgp ", "")
        dev_data["log_neighbor_changes"] = True
        for bgp_line in bgp_lines.children:
            bgp_line_text = bgp_line.text
            neigh_match = re.match(r'\sneighbor\s\S+\s', bgp_line_text )
            if "router-id" in bgp_line_text:
                dev_data["router_bgp"]["router_id"] = bgp_line.text.replace(" bgp router-id ", "") 
            elif neigh_match and "neighbors" not in dev_data["router_bgp"]: 
                neighbor = re.findall(r'neighbor\s(\S+)', bgp_line_text)
                dev_data["router_bgp"]["neighbors"] = {}
                dev_data["router_bgp"]["neighbors"][neighbor[0]] = {} 
            elif neigh_match and "neighbors" in dev_data["router_bgp"]: 
                neighbor = re.findall(r'neighbor\s(\S+)', bgp_line_text)
                dev_data["router_bgp"]["neighbors"][neighbor[0]] = {} 

    return dev_data