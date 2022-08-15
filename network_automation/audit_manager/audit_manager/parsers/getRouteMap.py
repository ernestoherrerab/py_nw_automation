#! /usr/bin/env python
"""
Script to parse Route Maps configs
"""
import re

def audit_route_map(parse_obj):
    """ Parse Route Maps """
    dev_data = {}
    dev_data["route_maps"] = {}
    route_map_lines = parse_obj.find_objects(r'^route-map')

    ### EVALUATE ROUTE MAPS ###
    for route_map_line in route_map_lines:
        route_map_line_text = route_map_line.text
        route_map_parameters = re.findall(r'route-map\s(\S+)\s(\w+)\s(\d+)', route_map_line_text)
        route_map_name = route_map_parameters[0][0]
        route_map_type = route_map_parameters[0][1]
        route_map_seq = int(route_map_parameters[0][2])
        if route_map_name not in dev_data["route_maps"]:
            dev_data["route_maps"][route_map_name] = {}
            dev_data["route_maps"][route_map_name]["sequence_numbers"] = {}
            dev_data["route_maps"][route_map_name]["sequence_numbers"][route_map_seq] = {}
            dev_data["route_maps"][route_map_name]["sequence_numbers"][route_map_seq]["type"] = route_map_type
            for route_map_params in route_map_line.children:
                route_map_params_text = route_map_params.text
                route_map_match = re.match(r'\smatch\s', route_map_params_text)
                route_map_set = re.match(r'\sset\s', route_map_params_text)
                if "description" in route_map_params_text:
                    dev_data["route_maps"][route_map_name]["sequence_numbers"][route_map_seq]["description"] = route_map_params_text.replace(" description ", "")
                elif route_map_match and "match" not in dev_data["route_maps"][route_map_name]["sequence_numbers"][route_map_seq]:
                    dev_data["route_maps"][route_map_name]["sequence_numbers"][route_map_seq]["match"] = []
                    dev_data["route_maps"][route_map_name]["sequence_numbers"][route_map_seq]["match"].append(route_map_params_text.replace(" match ", ""))
                elif route_map_match and "match" in dev_data["route_maps"][route_map_name]["sequence_numbers"][route_map_seq]:
                    dev_data["route_maps"][route_map_name]["sequence_numbers"][route_map_seq]["match"].append(route_map_params_text.replace(" match ", ""))
                elif route_map_set and "set" not in dev_data["route_maps"][route_map_name]["sequence_numbers"][route_map_seq]:
                    dev_data["route_maps"][route_map_name]["sequence_numbers"][route_map_seq]["set"] = []
                    dev_data["route_maps"][route_map_name]["sequence_numbers"][route_map_seq]["set"].append(route_map_params_text.replace(" set ", ""))
                elif route_map_set and "set" in dev_data["route_maps"][route_map_name]["sequence_numbers"][route_map_seq]:
                    dev_data["route_maps"][route_map_name]["sequence_numbers"][route_map_seq]["set"].append(route_map_params_text.replace(" set ", ""))     
        elif route_map_name in dev_data["route_maps"]: 
            if "sequence_numbers" not in dev_data["route_maps"][route_map_name]:
                dev_data["route_maps"][route_map_name]["sequence_numbers"] = {}
                dev_data["route_maps"][route_map_name]["sequence_numbers"][route_map_seq] = {}
                dev_data["route_maps"][route_map_name]["sequence_numbers"][route_map_seq]["type"] = route_map_type
                for route_map_params in route_map_line.children:
                    route_map_params_text = route_map_params.text
                    route_map_match = re.match(r'\smatch\s', route_map_params_text)
                    route_map_set = re.match(r'\sset\s', route_map_params_text)
                    if "description" in route_map_params_text:
                        dev_data["route_maps"][route_map_name]["sequence_numbers"][route_map_seq]["description"] = route_map_params_text.replace(" description ", "")
                    elif route_map_match and "match" not in dev_data["route_maps"][route_map_name]["sequence_numbers"][route_map_seq]:
                        dev_data["route_maps"][route_map_name]["sequence_numbers"][route_map_seq]["match"] = []
                        dev_data["route_maps"][route_map_name]["sequence_numbers"][route_map_seq]["match"].append(route_map_params_text.replace(" match ", ""))
                    elif route_map_match and "match" in dev_data["route_maps"][route_map_name]["sequence_numbers"][route_map_seq]:
                        dev_data["route_maps"][route_map_name]["sequence_numbers"][route_map_seq]["match"].append(route_map_params_text.replace(" match ", ""))
                    elif route_map_set and "set" not in dev_data["route_maps"][route_map_name]["sequence_numbers"][route_map_seq]:
                        dev_data["route_maps"][route_map_name]["sequence_numbers"][route_map_seq]["set"] = []
                        dev_data["route_maps"][route_map_name]["sequence_numbers"][route_map_seq]["set"].append(route_map_params_text.replace(" set ", ""))
                    elif route_map_set and "set" in dev_data["route_maps"][route_map_name]["sequence_numbers"][route_map_seq]:
                        dev_data["route_maps"][route_map_name]["sequence_numbers"][route_map_seq]["set"].append(route_map_params_text.replace(" set ", ""))
            elif "sequence_numbers" in dev_data["route_maps"][route_map_name]:
                dev_data["route_maps"][route_map_name]["sequence_numbers"][route_map_seq] = {}
                dev_data["route_maps"][route_map_name]["sequence_numbers"][route_map_seq]["type"] = route_map_type
                for route_map_params in route_map_line.children:
                    route_map_params_text = route_map_params.text
                    route_map_match = re.match(r'\smatch\s', route_map_params_text)
                    route_map_set = re.match(r'\sset\s', route_map_params_text)
                    if "description" in route_map_params_text:
                        dev_data["route_maps"][route_map_name]["sequence_numbers"][route_map_seq]["description"] = route_map_params_text.replace(" description ", "")
                    elif route_map_match and "match" not in dev_data["route_maps"][route_map_name]["sequence_numbers"][route_map_seq]:
                        dev_data["route_maps"][route_map_name]["sequence_numbers"][route_map_seq]["match"] = []
                        dev_data["route_maps"][route_map_name]["sequence_numbers"][route_map_seq]["match"].append(route_map_params_text.replace(" match ", ""))
                    elif route_map_match and "match" in dev_data["route_maps"][route_map_name]["sequence_numbers"][route_map_seq]:
                        dev_data["route_maps"][route_map_name]["sequence_numbers"][route_map_seq]["match"].append(route_map_params_text.replace(" match ", ""))
                    elif route_map_set and "set" not in dev_data["route_maps"][route_map_name]["sequence_numbers"][route_map_seq]:
                        dev_data["route_maps"][route_map_name]["sequence_numbers"][route_map_seq]["set"] = []
                        dev_data["route_maps"][route_map_name]["sequence_numbers"][route_map_seq]["set"].append(route_map_params_text.replace(" set ", ""))
                    elif route_map_set and "set" in dev_data["route_maps"][route_map_name]["sequence_numbers"][route_map_seq]:
                        dev_data["route_maps"][route_map_name]["sequence_numbers"][route_map_seq]["set"].append(route_map_params_text.replace(" set ", ""))    

    return dev_data