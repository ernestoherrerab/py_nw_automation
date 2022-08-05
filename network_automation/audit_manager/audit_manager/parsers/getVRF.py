#! /usr/bin/env python
"""
Script to parse VRF configs
"""
import re

def audit_vrf(parse_obj):
    """ Parse VRFs """

    dev_data = {}
    dev_data["vrfs"] = {}
    vrf_lines = parse_obj.find_objects(r"^ip\svrf\s")
    
    for vrf_line in vrf_lines:
        vrf = vrf_line.text.replace("ip vrf ", "").replace(" ", "", 1) 
        dev_data["vrfs"][vrf] = {}
        for vrf_data in vrf_line.children:
            vrf_data = vrf_data.text
            if "description" in vrf_data:
                dev_data["vrfs"][vrf]["description"] = vrf_data.replace("description ", "")
            elif "rd" in vrf_data:
                dev_data["vrfs"][vrf]["route_distinguisher"] = vrf_data.replace(" rd ", "")
            elif "route-target" in vrf_data and "route_targets" not in dev_data["vrfs"][vrf]:
                vrf_target_params = re.findall(r'route-target\s(\S+)\s(\S+)', vrf_data) 
                dev_data["vrfs"][vrf]["route_targets"] = {}
                dev_data["vrfs"][vrf]["route_targets"][vrf_target_params[0][0]] = []
                dev_data["vrfs"][vrf]["route_targets"][vrf_target_params[0][0]].append(vrf_target_params[0][1])
            elif "route-target" in vrf_data and "route_targets" in dev_data["vrfs"][vrf]:
                vrf_target_params = re.findall(r'route-target\s(\S+)\s(\S+)', vrf_data) 
                print(vrf_target_params)
                if vrf_target_params[0][0] not in dev_data["vrfs"][vrf]["route_targets"]:
                    dev_data["vrfs"][vrf]["route_targets"][vrf_target_params[0][0]] = []
                    dev_data["vrfs"][vrf]["route_targets"][vrf_target_params[0][0]].append(vrf_target_params[0][1])
                elif vrf_target_params[0][0] in dev_data["vrfs"][vrf]["route_targets"]:
                    dev_data["vrfs"][vrf]["route_targets"][vrf_target_params[0][0]].append(vrf_target_params[0][1])
           
    return dev_data