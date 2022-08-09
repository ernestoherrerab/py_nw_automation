#! /usr/bin/env python
"""
Script to parse BGP configs
"""
import regex as re

def audit_bgp(parse_obj):
    """ Parse BGP """
    dev_data = {}
    dev_data["router_bgp"] = {}
    bgp_process = parse_obj.find_objects(r'^router\sbgp')
    
    for bgp_lines in bgp_process:
        dev_data["router_bgp"]["as"] = bgp_lines.text.replace("router bgp ", "")
        dev_data["router_bgp"]["log_neighbor_changes"] = True
        dev_data["shutdown"] = False
        for bgp_line in bgp_lines.children:
            bgp_line_text = bgp_line.text
            neigh_match = re.match(r'\sneighbor\s\S+\s', bgp_line_text )
            route_map_filter_match = re.match(r'\sneighbor\s\S+\sroute-map', bgp_line_text)
            network_match = re.match(r'\snetwork\s', bgp_line_text)
            ipv4_af_match = re.match(r'\saddress-family\sipv4$', bgp_line_text)
            ipv4_vrf_af_name = re.findall(r'\saddress-family\sipv4\svrf\s(\S+)', bgp_line_text)
            ### COMMON GENERAL BGP SETTINGS EVALUATION ###
            if "router-id" in bgp_line_text:
                dev_data["router_bgp"]["router_id"] = bgp_line.text.replace(" bgp router-id ", "") 
            elif network_match and "networks" not in dev_data["router_bgp"]:
                network_parameters = re.findall(r'(?<=network\s)(\S+)\smask\s(\S+)(?(?=\s\S+)\sroute-map\s(\S+))', bgp_line_text)
                dev_data["router_bgp"]["networks"] = {}
                dev_data["router_bgp"]["networks"][network_parameters[0][0]] = {}
                dev_data["router_bgp"]["networks"][network_parameters[0][0]]["mask"] =  network_parameters[0][1]
                if network_parameters[0][2]:
                    dev_data["router_bgp"]["networks"][network_parameters[0][0]]["route_map"] = network_parameters[0][2]
            elif network_match and "networks" in dev_data["router_bgp"]:
                network_parameters = re.findall(r'(?<=network\s)(\S+)\smask\s(\S+)(?(?=\s\S+)\sroute-map\s(\S+))', bgp_line_text)
                dev_data["router_bgp"]["networks"][network_parameters[0][0]] = {}
                dev_data["router_bgp"]["networks"][network_parameters[0][0]]["mask"] =  network_parameters[0][1]
                if network_parameters[0][2]:
                    dev_data["router_bgp"]["networks"][network_parameters[0][0]]["route_map"] = network_parameters[0][2]
            elif "aggregate-address" in bgp_line_text and "aggregate_addresses" not in dev_data["router_bgp"]: 
                aggregate_address = re.findall(r'aggregate-address\s(\S+)\s(\S+)\s(\S+)', bgp_line_text)
                dev_data["router_bgp"]["aggregate_addresses"] = {}
                dev_data["router_bgp"]["aggregate_addresses"][aggregate_address[0][0]] = {}
                dev_data["router_bgp"]["aggregate_addresses"][aggregate_address[0][0]]["mask"] = aggregate_address[0][1]
                if aggregate_address[0][2] == "summary-only":
                    dev_data["router_bgp"]["address_family_ipv4"]["aggregate_addresses"][aggregate_address[0][2]] = True
            elif "aggregate-address" in bgp_line_text and "aggregate_addresses" in dev_data["router_bgp"]: 
                aggregate_address = re.findall(r'aggregate-address\s(\S+)\s(\S+)\s(\S+)', bgp_line_text)
                dev_data["router_bgp"]["aggregate_addresses"][aggregate_address[0][0]] = {}
                dev_data["router_bgp"]["aggregate_addresses"][aggregate_address[0][0]]["mask"] = aggregate_address[0][1]
                if aggregate_address[0][2] == "summary-only":
                    dev_data["router_bgp"]["aggregate_addresses"][aggregate_address[0][2]] = True
            elif "redistribute" in bgp_line_text and "redistribution" not in dev_data["router_bgp"]:
                redistribute_type = re.findall(r'redistribute\s(\w+)', bgp_line_text)
                redistribute_type = redistribute_type[0]
                redistribute_route_map = re.findall(r'redistribute\s\w+\sroute-map\s(\S+)', bgp_line_text)
                dev_data["router_bgp"]["redistribution"] = {}
                dev_data["router_bgp"]["redistribution"][redistribute_type] = {}
                if redistribute_route_map:
                    redistribute_route_map = redistribute_route_map[0]
                    dev_data["router_bgp"]["redistribution"][redistribute_type]["route_map"] = redistribute_route_map
            elif "redistribute" in bgp_line_text and "redistribution" in dev_data["router_bgp"]:
                redistribute_type = re.findall(r'redistribute\s(\w+)', bgp_line_text)
                redistribute_type = redistribute_type[0]
                redistribute_route_map = re.findall(r'redistribute\s\w+\sroute-map\s(\S+)', bgp_line_text)
                dev_data["router_bgp"]["redistribution"][redistribute_type] = {}
                if redistribute_route_map:
                    redistribute_route_map = redistribute_route_map[0]
                    dev_data["router_bgp"]["redistribution"][redistribute_type]["route_map"] = redistribute_route_map
            elif neigh_match and "neighbors" not in dev_data["router_bgp"]: 
                neighbor = re.findall(r'neighbor\s(\S+)', bgp_line_text)
                dev_data["router_bgp"]["neighbors"] = {}
                dev_data["router_bgp"]["neighbors"][neighbor[0]] = {} 
                if "remote-as" in bgp_line_text:
                    dev_data["router_bgp"]["neighbors"][neighbor[0]]["remote_as"] = int(re.sub(r'\sneighbor\s\S+\sremote-as\s', "", bgp_line_text))
                elif "description" in bgp_line_text:
                    dev_data["router_bgp"]["neighbors"][neighbor[0]]["description"] = re.sub(r'\sneighbor\s\S+\sdescription\s', "", bgp_line_text)
                elif "password" in bgp_line_text:
                    dev_data["router_bgp"]["neighbors"][neighbor[0]]["password"] = re.sub(r'\sneighbor\s\S+\spassword\s\d+\s', "", bgp_line_text)
                elif "soft-reconfiguration inbound" in bgp_line_text:
                    dev_data["router_bgp"]["neighbors"][neighbor[0]]["soft-reconfiguration inbound"] = True
                elif "route-reflector-client" in bgp_line_text:
                    dev_data["router_bgp"]["neighbors"][neighbor[0]]["route-reflector-client"] = True
                elif route_map_filter_match:
                    route_map_filter = re.findall(r'neighbor\s\S+\s\S+\s(\S+)\s(\w+)', bgp_line_text)
                    dev_data["router_bgp"]["neighbors"][neighbor[0]][f'route_map_{route_map_filter[0][1]}'] = route_map_filter[0][0]
            elif neigh_match and "neighbors" in dev_data["router_bgp"]: 
                neighbor = re.findall(r'neighbor\s(\S+)', bgp_line_text)
                if "remote-as" in bgp_line_text and neighbor[0] not in dev_data["router_bgp"]["neighbors"]:
                    dev_data["router_bgp"]["neighbors"][neighbor[0]] = {} 
                    dev_data["router_bgp"]["neighbors"][neighbor[0]]["remote_as"] = int(re.sub(r'\sneighbor\s\S+\sremote-as\s', "", bgp_line_text))
                elif "remote-as" in bgp_line_text and neighbor[0] in dev_data["router_bgp"]["neighbors"]:
                    dev_data["router_bgp"]["neighbors"][neighbor[0]]["remote_as"] = int(re.sub(r'\sneighbor\s\S+\sremote-as\s', "", bgp_line_text))
                elif "description" in bgp_line_text and neighbor[0] not in dev_data["router_bgp"]["neighbors"]:
                    dev_data["router_bgp"]["neighbors"][neighbor[0]] = {} 
                    dev_data["router_bgp"]["neighbors"][neighbor[0]]["description"] = re.sub(r'\sneighbor\s\S+\sdescription\s', "", bgp_line_text)
                elif "description" in bgp_line_text and neighbor[0] in dev_data["router_bgp"]["neighbors"]:
                    dev_data["router_bgp"]["neighbors"][neighbor[0]]["description"] = re.sub(r'\sneighbor\s\S+\sdescription\s', "", bgp_line_text)
                elif "password" in bgp_line_text and neighbor[0] not in dev_data["router_bgp"]["neighbors"]:
                    dev_data["router_bgp"]["neighbors"][neighbor[0]] = {} 
                    dev_data["router_bgp"]["neighbors"][neighbor[0]]["password"] = re.sub(r'\sneighbor\s\S+\spassword\s\d+\s', "", bgp_line_text)
                elif "password" in bgp_line_text and neighbor[0] in dev_data["router_bgp"]["neighbors"]:
                    dev_data["router_bgp"]["neighbors"][neighbor[0]]["password"] = re.sub(r'\sneighbor\s\S+\spassword\s\d+\s', "", bgp_line_text)
                elif "soft-reconfiguration inbound" in bgp_line_text and neighbor[0] not in dev_data["router_bgp"]["neighbors"]:
                    dev_data["router_bgp"]["neighbors"][neighbor[0]] = {} 
                    dev_data["router_bgp"]["neighbors"][neighbor[0]]["soft-reconfiguration inbound"] = True
                elif "soft-reconfiguration inbound" in bgp_line_text and neighbor[0] in dev_data["router_bgp"]["neighbors"]:
                    dev_data["router_bgp"]["neighbors"][neighbor[0]]["soft-reconfiguration inbound"] = True
                elif "route-reflector-client" in bgp_line_text and neighbor[0] not in dev_data["router_bgp"]["neighbors"]:
                    dev_data["router_bgp"]["neighbors"][neighbor[0]] = {}
                    dev_data["router_bgp"]["neighbors"][neighbor[0]]["route-reflector-client"] = True
                elif "route-reflector-client" in bgp_line_text and neighbor[0] in dev_data["router_bgp"]["neighbors"]:
                    dev_data["router_bgp"]["neighbors"][neighbor[0]]["route-reflector-client"] = True
                elif route_map_filter_match and neighbor[0] not in dev_data["router_bgp"]["neighbors"]:
                    route_map_filter = re.findall(r'neighbor\s\S+\s\S+\s(\S+)\s(\w+)', bgp_line_text)
                    dev_data["router_bgp"]["neighbors"][neighbor[0]] = {}
                    dev_data["router_bgp"]["neighbors"][neighbor[0]][f'route_map_{route_map_filter[0][1]}'] = route_map_filter[0][0]
                elif route_map_filter_match and neighbor[0] in dev_data["router_bgp"]["neighbors"]:
                    route_map_filter = re.findall(r'neighbor\s\S+\s\S+\s(\S+)\s(\w+)', bgp_line_text)
                    dev_data["router_bgp"]["neighbors"][neighbor[0]][f'route_map_{route_map_filter[0][1]}'] = route_map_filter[0][0]
            ### ADDRESS FAMILIES EVALUATION ###
            ### GLOBAL IPV4 FAMILY ###
            elif ipv4_af_match and "address_family_ipv4" not in dev_data["router_bgp"]:
                dev_data["router_bgp"]["address_family_ipv4"] = {}
                dev_data["router_bgp"]["address_family_ipv4"]["no_auto_summary"] = True
                dev_data["router_bgp"]["address_family_ipv4"]["no_synchronization"] = True
                for bgp_ipv4_params in bgp_line.children:
                    bgp_ipv4_params_text = bgp_ipv4_params.text
                    ipv4_neigh_match = re.match(r'\s\sneighbor\s\S+\s', bgp_ipv4_params_text)
                    ipv4_route_map_filter_match = re.match(r'\s\sneighbor\s\S+\sroute-map', bgp_ipv4_params_text)
                    ipv4_network_match = re.match(r'\s\snetwork\s', bgp_ipv4_params_text)
                    if ipv4_network_match and "networks" not in dev_data["router_bgp"]["address_family_ipv4"]:
                        ipv4_network_parameters = re.findall(r'(?<=network\s)(\S+)\smask\s(\S+)(?(?=\s\S+)\sroute-map\s(\S+))', bgp_ipv4_params_text)
                        dev_data["router_bgp"]["address_family_ipv4"]["networks"] = {}
                        dev_data["router_bgp"]["address_family_ipv4"]["networks"][ipv4_network_parameters[0][0]] = {}
                        dev_data["router_bgp"]["address_family_ipv4"]["networks"][ipv4_network_parameters[0][0]]["mask"] =  ipv4_network_parameters[0][1]
                        if ipv4_network_parameters[0][2]:
                            dev_data["router_bgp"]["address_family_ipv4"]["networks"][ipv4_network_parameters[0][0]]["route_map"] = ipv4_network_parameters[0][2]
                    elif ipv4_network_match and "networks" in dev_data["router_bgp"]["address_family_ipv4"]:
                        ipv4_network_parameters = re.findall(r'(?<=network\s)(\S+)\smask\s(\S+)(?(?=\s\S+)\sroute-map\s(\S+))', bgp_ipv4_params_text)
                        dev_data["router_bgp"]["address_family_ipv4"]["networks"][ipv4_network_parameters[0][0]] = {}
                        dev_data["router_bgp"]["address_family_ipv4"]["networks"][ipv4_network_parameters[0][0]]["mask"] =  ipv4_network_parameters[0][1]
                        if ipv4_network_parameters[0][2]:
                            dev_data["router_bgp"]["address_family_ipv4"]["networks"][ipv4_network_parameters[0][0]]["route_map"] = ipv4_network_parameters[0][2]
                    elif "redistribute" in bgp_ipv4_params_text and "redistribution" not in dev_data["router_bgp"]["address_family_ipv4"]:
                        ipv4_redistribute_type = re.findall(r'redistribute\s(\w+)', bgp_ipv4_params_text )
                        ipv4_redistribute_type = ipv4_redistribute_type[0]
                        ipv4_redistribute_route_map = re.findall(r'redistribute\s\w+\sroute-map\s(\S+)', bgp_ipv4_params_text)
                        dev_data["router_bgp"]["address_family_ipv4"]["redistribution"] = {}
                        dev_data["router_bgp"]["address_family_ipv4"]["redistribution"][ipv4_redistribute_type] = {}
                        if ipv4_redistribute_route_map:
                            ipv4_redistribute_route_map = ipv4_redistribute_route_map[0]
                            dev_data["router_bgp"]["address_family_ipv4"]["redistribution"][ipv4_redistribute_type]["route_map"] = ipv4_redistribute_route_map
                    elif "redistribute" in bgp_ipv4_params_text and "redistribution" in dev_data["router_bgp"]["address_family_ipv4"]:
                        ipv4_redistribute_type = re.findall(r'redistribute\s(\w+)', bgp_ipv4_params_text )
                        ipv4_redistribute_type = ipv4_redistribute_type[0]
                        ipv4_redistribute_route_map = re.findall(r'redistribute\s\w+\sroute-map\s(\S+)', bgp_ipv4_params_text)
                        dev_data["router_bgp"]["address_family_ipv4"]["redistribution"][ipv4_redistribute_type] = {}
                        if ipv4_redistribute_route_map:
                            ipv4_redistribute_route_map = ipv4_redistribute_route_map[0]
                            dev_data["router_bgp"]["address_family_ipv4"]["redistribution"][ipv4_redistribute_type]["route_map"] = ipv4_redistribute_route_map
                    elif "aggregate-address" in bgp_ipv4_params_text and "aggregate_addresses" not in dev_data["router_bgp"]["address_family_ipv4"]: 
                        ipv4_aggregate_address = re.findall(r'aggregate-address\s(\S+)\s(\S+)\s(\S+)', bgp_ipv4_params_text)
                        dev_data["router_bgp"]["address_family_ipv4"]["aggregate_addresses"] = {}
                        dev_data["router_bgp"]["address_family_ipv4"]["aggregate_addresses"][ipv4_aggregate_address[0][0]] = {}
                        dev_data["router_bgp"]["address_family_ipv4"]["aggregate_addresses"][ipv4_aggregate_address[0][0]]["mask"] = ipv4_aggregate_address[0][1]
                        if ipv4_aggregate_address[0][2] == "summary-only":
                            dev_data["router_bgp"]["address_family_ipv4"]["aggregate_addresses"][ipv4_aggregate_address[0][2]] = True
                    elif "aggregate-address" in bgp_ipv4_params_text and "aggregate_addresses" in dev_data["router_bgp"]["address_family_ipv4"]: 
                        ipv4_aggregate_address = re.findall(r'aggregate-address\s(\S+)\s(\S+)\s(\S+)', bgp_ipv4_params_text)
                        dev_data["router_bgp"]["address_family_ipv4"]["aggregate_addresses"][ipv4_aggregate_address[0][0]] = {}
                        dev_data["router_bgp"]["address_family_ipv4"]["aggregate_addresses"][ipv4_aggregate_address[0][0]]["mask"] = ipv4_aggregate_address[0][1]
                        if ipv4_aggregate_address[0][2] == "summary-only":
                            dev_data["router_bgp"]["address_family_ipv4"]["aggregate_addresses"][ipv4_aggregate_address[0][2]] = True
                    elif ipv4_neigh_match and "neighbors" not in dev_data["router_bgp"]["address_family_ipv4"]: 
                        ipv4_neighbor = re.findall(r'neighbor\s(\S+)', bgp_ipv4_params_text)
                        dev_data["router_bgp"]["address_family_ipv4"]["neighbors"] = {}
                        dev_data["router_bgp"]["address_family_ipv4"]["neighbors"][ipv4_neighbor[0]] = {} 
                        if "description" in bgp_ipv4_params_text:
                            dev_data["router_bgp"]["address_family_ipv4"]["neighbors"][ipv4_neighbor[0]]["description"] = re.sub(r'\s\sneighbor\s\S+\sdescription\s', "", bgp_ipv4_params_text)
                        elif "password" in bgp_ipv4_params_text:
                            dev_data["router_bgp"]["address_family_ipv4"]["neighbors"][ipv4_neighbor[0]]["password"] = re.sub(r'\s\sneighbor\s\S+\spassword\s\d+\s', "", bgp_ipv4_params_text)
                        elif "activate" in bgp_ipv4_params_text:
                            dev_data["router_bgp"]["address_family_ipv4"]["neighbors"][ipv4_neighbor[0]]["activate"] = True
                        elif "route-reflector-client" in bgp_ipv4_params_text:
                            dev_data["router_bgp"]["address_family_ipv4"]["neighbors"][ipv4_neighbor[0]]["route-reflector-client"] = True
                        elif "soft-reconfiguration inbound" in bgp_ipv4_params_text:
                            dev_data["router_bgp"]["address_family_ipv4"]["neighbors"][ipv4_neighbor[0]]["soft-reconfiguration inbound"] = True
                        elif ipv4_route_map_filter_match:
                            ipv4_route_map_filter = re.findall(r'neighbor\s\S+\s\S+\s(\S+)\s(\w+)', bgp_ipv4_params_text)
                            dev_data["router_bgp"]["address_family_ipv4"]["neighbors"][ipv4_neighbor[0]][f'route_map_{ipv4_route_map_filter[0][1]}'] = ipv4_route_map_filter[0][0]
                    elif ipv4_neigh_match and "neighbors" in dev_data["router_bgp"]["address_family_ipv4"]: 
                        ipv4_neighbor = re.findall(r'neighbor\s(\S+)', bgp_ipv4_params_text)
                        if "description" in bgp_ipv4_params_text and ipv4_neighbor not in dev_data["router_bgp"]["address_family_ipv4"]["neighbors"]:
                            dev_data["router_bgp"]["address_family_ipv4"]["neighbors"][ipv4_neighbor] = {} 
                            dev_data["router_bgp"]["address_family_ipv4"]["neighbors"][ipv4_neighbor]["description"] = re.sub(r'\s\sneighbor\s\S+\sdescription\s', "", bgp_ipv4_params_text)
                        elif "description" in bgp_ipv4_params_text and ipv4_neighbor in dev_data["router_bgp"]["address_family_ipv4"]["neighbors"]:
                            dev_data["router_bgp"]["address_family_ipv4"]["neighbors"][ipv4_neighbor[0]]["description"] = re.sub(r'\s\sneighbor\s\S+\sdescription\s', "", bgp_ipv4_params_text)
                        elif "password" in bgp_ipv4_params_text and ipv4_neighbor[0] not in dev_data["router_bgp"]["address_family_ipv4"]["neighbors"]:
                            dev_data["router_bgp"]["address_family_ipv4"]["neighbors"][ipv4_neighbor[0]] = {} 
                            dev_data["router_bgp"]["address_family_ipv4"]["neighbors"][ipv4_neighbor[0]]["password"] = re.sub(r'\s\sneighbor\s\S+\spassword\s\d+\s', "", bgp_ipv4_params_text)
                        elif "password" in bgp_ipv4_params_text and ipv4_neighbor[0] in dev_data["router_bgp"]["address_family_ipv4"]["neighbors"]:
                            dev_data["router_bgp"]["address_family_ipv4"]["neighbors"][ipv4_neighbor[0]]["password"] = re.sub(r'\s\sneighbor\s\S+\spassword\s\d+\s', "", bgp_ipv4_params_text)
                        elif "activate" in bgp_ipv4_params_text and ipv4_neighbor[0] not in dev_data["router_bgp"]["address_family_ipv4"]["neighbors"]:
                            dev_data["router_bgp"]["address_family_ipv4"]["neighbors"][ipv4_neighbor[0]] = {} 
                            dev_data["router_bgp"]["address_family_ipv4"]["neighbors"][ipv4_neighbor[0]]["activate"] = True
                        elif "activate" in bgp_ipv4_params_text and ipv4_neighbor[0] in dev_data["router_bgp"]["address_family_ipv4"]["neighbors"]:
                            dev_data["router_bgp"]["address_family_ipv4"]["neighbors"][ipv4_neighbor[0]]["activate"] = True
                        elif "route-reflector-client" in bgp_ipv4_params_text and ipv4_neighbor[0] not in dev_data["router_bgp"]["address_family_ipv4"]["neighbors"]:
                            dev_data["router_bgp"]["address_family_ipv4"]["neighbors"][ipv4_neighbor[0]] = {} 
                            dev_data["router_bgp"]["address_family_ipv4"]["neighbors"][ipv4_neighbor[0]]["route-reflector-client"] = True
                        elif "route-reflector-client" in bgp_ipv4_params_text and ipv4_neighbor[0] in dev_data["router_bgp"]["address_family_ipv4"]["neighbors"]:
                            dev_data["router_bgp"]["address_family_ipv4"]["neighbors"][ipv4_neighbor[0]]["route-reflector-client"] = True
                        elif "soft-reconfiguration inbound" in bgp_ipv4_params_text and ipv4_neighbor[0] not in dev_data["router_bgp"]["address_family_ipv4"]["neighbors"]:
                            dev_data["router_bgp"]["address_family_ipv4"]["neighbors"][ipv4_neighbor[0]] = {} 
                            dev_data["router_bgp"]["address_family_ipv4"]["neighbors"][ipv4_neighbor[0]]["soft-reconfiguration inbound"] = True
                        elif "soft-reconfiguration inbound" in bgp_ipv4_params_text and ipv4_neighbor[0] in dev_data["router_bgp"]["address_family_ipv4"]["neighbors"]:
                            dev_data["router_bgp"]["address_family_ipv4"]["neighbors"][ipv4_neighbor[0]]["soft-reconfiguration inbound"] = True
                        elif ipv4_route_map_filter_match and ipv4_neighbor[0] not in dev_data["router_bgp"]["address_family_ipv4"]["neighbors"]:
                            ipv4_route_map_filter = re.findall(r'neighbor\s\S+\s\S+\s(\S+)\s(\w+)', bgp_ipv4_params_text)
                            dev_data["router_bgp"]["address_family_ipv4"]["neighbors"][ipv4_neighbor[0]] = {} 
                            dev_data["router_bgp"]["address_family_ipv4"]["neighbors"][ipv4_neighbor[0]][f'route_map_{ipv4_route_map_filter[0][1]}'] = ipv4_route_map_filter[0][0]
                        elif ipv4_route_map_filter_match and ipv4_neighbor[0] in dev_data["router_bgp"]["address_family_ipv4"]["neighbors"]:
                            ipv4_route_map_filter = re.findall(r'neighbor\s\S+\s\S+\s(\S+)\s(\w+)', bgp_ipv4_params_text)
                            dev_data["router_bgp"]["address_family_ipv4"]["neighbors"][ipv4_neighbor[0]][f'route_map_{ipv4_route_map_filter[0][1]}'] = ipv4_route_map_filter[0][0] 
            elif ipv4_af_match and "address_family_ipv4" in dev_data["router_bgp"]:
                for bgp_ipv4_params in bgp_line.children:
                    bgp_ipv4_params_text = bgp_ipv4_params.text
                    ipv4_neigh_match = re.match(r'\s\sneighbor\s\S+\s', bgp_ipv4_params_text)
                    ipv4_route_map_filter_match = re.match(r'\s\sneighbor\s\S+\sroute-map', bgp_ipv4_params_text)
                    ipv4_network_match = re.match(r'\s\snetwork\s', bgp_ipv4_params_text)
                    if ipv4_network_match and "networks" not in dev_data["router_bgp"]["address_family_ipv4"]:
                        ipv4_network_parameters = re.findall(r'(?<=network\s)(\S+)\smask\s(\S+)(?(?=\s\S+)\sroute-map\s(\S+))', bgp_ipv4_params_text)
                        dev_data["router_bgp"]["address_family_ipv4"]["networks"] = {}
                        dev_data["router_bgp"]["address_family_ipv4"]["networks"][ipv4_network_parameters[0][0]] = {}
                        dev_data["router_bgp"]["address_family_ipv4"]["networks"][ipv4_network_parameters[0][0]]["mask"] =  ipv4_network_parameters[0][1]
                        if ipv4_network_parameters[0][2]:
                            dev_data["router_bgp"]["address_family_ipv4"]["networks"][ipv4_network_parameters[0][0]]["route_map"] = ipv4_network_parameters[0][2]
                    elif ipv4_network_match and "networks" in dev_data["router_bgp"]["address_family_ipv4"]:
                        ipv4_network_parameters = re.findall(r'(?<=network\s)(\S+)\smask\s(\S+)(?(?=\s\S+)\sroute-map\s(\S+))', bgp_ipv4_params_text)
                        dev_data["router_bgp"]["address_family_ipv4"]["networks"][ipv4_network_parameters[0][0]] = {}
                        dev_data["router_bgp"]["address_family_ipv4"]["networks"][ipv4_network_parameters[0][0]]["mask"] =  ipv4_network_parameters[0][1]
                        if ipv4_network_parameters[0][2]:
                            dev_data["router_bgp"]["address_family_ipv4"]["networks"][ipv4_network_parameters[0][0]]["route_map"] = ipv4_network_parameters[0][2]
                    elif "redistribute" in bgp_ipv4_params_text and "redistribution" not in dev_data["router_bgp"]["address_family_ipv4"]:
                        ipv4_redistribute_type = re.findall(r'redistribute\s(\w+)', bgp_ipv4_params_text )
                        ipv4_redistribute_type = ipv4_redistribute_type[0]
                        ipv4_redistribute_route_map = re.findall(r'redistribute\s\w+\sroute-map\s(\S+)', bgp_ipv4_params_text)
                        dev_data["router_bgp"]["address_family_ipv4"]["redistribution"] = {}
                        dev_data["router_bgp"]["address_family_ipv4"]["redistribution"][ipv4_redistribute_type] = {}
                        if ipv4_redistribute_route_map:
                            ipv4_redistribute_route_map = ipv4_redistribute_route_map[0]
                            dev_data["router_bgp"]["address_family_ipv4"]["redistribution"][ipv4_redistribute_type]["route_map"] = ipv4_redistribute_route_map
                    elif "redistribute" in bgp_ipv4_params_text and "redistribution" in dev_data["router_bgp"]["address_family_ipv4"]:
                        ipv4_redistribute_type = re.findall(r'redistribute\s(\w+)', bgp_ipv4_params_text )
                        ipv4_redistribute_type = ipv4_redistribute_type[0]
                        ipv4_redistribute_route_map = re.findall(r'redistribute\s\w+\sroute-map\s(\S+)', bgp_ipv4_params_text)
                        dev_data["router_bgp"]["address_family_ipv4"]["redistribution"][ipv4_redistribute_type] = {}
                        if ipv4_redistribute_route_map:
                            ipv4_redistribute_route_map = ipv4_redistribute_route_map[0]
                            dev_data["router_bgp"]["address_family_ipv4"]["redistribution"][ipv4_redistribute_type]["route_map"] = ipv4_redistribute_route_map
                    elif "aggregate-address" in bgp_ipv4_params_text and "aggregate_addresses" not in dev_data["router_bgp"]["address_family_ipv4"]: 
                        ipv4_aggregate_address = re.findall(r'aggregate-address\s(\S+)\s(\S+)\s(\S+)', bgp_ipv4_params_text)
                        dev_data["router_bgp"]["address_family_ipv4"]["aggregate_addresses"] = {}
                        dev_data["router_bgp"]["address_family_ipv4"]["aggregate_addresses"][ipv4_aggregate_address[0][0]] = {}
                        dev_data["router_bgp"]["address_family_ipv4"]["aggregate_addresses"][ipv4_aggregate_address[0][0]]["mask"] = ipv4_aggregate_address[0][1]
                        if ipv4_aggregate_address[0][2] == "summary-only":
                            dev_data["router_bgp"]["address_family_ipv4"]["aggregate_addresses"][ipv4_aggregate_address[0][2]] = True
                    elif "aggregate-address" in bgp_ipv4_params_text and "aggregate_addresses" in dev_data["router_bgp"]["address_family_ipv4"]: 
                        ipv4_aggregate_address = re.findall(r'aggregate-address\s(\S+)\s(\S+)\s(\S+)', bgp_ipv4_params_text)
                        dev_data["router_bgp"]["address_family_ipv4"]["aggregate_addresses"][ipv4_aggregate_address[0][0]] = {}
                        dev_data["router_bgp"]["address_family_ipv4"]["aggregate_addresses"][ipv4_aggregate_address[0][0]]["mask"] = ipv4_aggregate_address[0][1]
                        if ipv4_aggregate_address[0][2] == "summary-only":
                            dev_data["router_bgp"]["address_family_ipv4"]["aggregate_addresses"][ipv4_aggregate_address[0][2]] = True
                    elif ipv4_neigh_match and "neighbors" not in dev_data["router_bgp"]["address_family_ipv4"]: 
                        ipv4_neighbor = re.findall(r'neighbor\s(\S+)', bgp_ipv4_params_text)
                        dev_data["router_bgp"]["address_family_ipv4"]["neighbors"] = {}
                        dev_data["router_bgp"]["address_family_ipv4"]["neighbors"][ipv4_neighbor[0]] = {} 
                        if "description" in bgp_ipv4_params_text:
                            dev_data["router_bgp"]["address_family_ipv4"]["neighbors"][ipv4_neighbor[0]]["description"] = re.sub(r'\s\sneighbor\s\S+\sdescription\s', "", bgp_ipv4_params_text)
                        elif "password" in bgp_ipv4_params_text:
                            dev_data["router_bgp"]["address_family_ipv4"]["neighbors"][ipv4_neighbor[0]]["password"] = re.sub(r'\s\sneighbor\s\S+\spassword\s\d+\s', "", bgp_ipv4_params_text)
                        elif "activate" in bgp_ipv4_params_text:
                            dev_data["router_bgp"]["address_family_ipv4"]["neighbors"][ipv4_neighbor[0]]["activate"] = True
                        elif "route-reflector-client" in bgp_ipv4_params_text:
                            dev_data["router_bgp"]["address_family_ipv4"]["neighbors"][ipv4_neighbor[0]]["route-reflector-client"] = True
                        elif "soft-reconfiguration inbound" in bgp_ipv4_params_text:
                            dev_data["router_bgp"]["address_family_ipv4"]["neighbors"][ipv4_neighbor[0]]["soft-reconfiguration inbound"] = True
                        elif ipv4_route_map_filter_match:
                            ipv4_route_map_filter = re.findall(r'neighbor\s\S+\s\S+\s(\S+)\s(\w+)', bgp_ipv4_params_text)
                            dev_data["router_bgp"]["address_family_ipv4"]["neighbors"][ipv4_neighbor[0]][f'route_map_{ipv4_route_map_filter[0][1]}'] = ipv4_route_map_filter[0][0]
                    elif ipv4_neigh_match and "neighbors" in dev_data["router_bgp"]["address_family_ipv4"]: 
                        ipv4_neighbor = re.findall(r'neighbor\s(\S+)', bgp_ipv4_params_text)
                        if "description" in bgp_ipv4_params_text and ipv4_neighbor not in dev_data["router_bgp"]["address_family_ipv4"]["neighbors"]:
                            dev_data["router_bgp"]["address_family_ipv4"]["neighbors"][ipv4_neighbor] = {} 
                            dev_data["router_bgp"]["address_family_ipv4"]["neighbors"][ipv4_neighbor]["description"] = re.sub(r'\s\sneighbor\s\S+\sdescription\s', "", bgp_ipv4_params_text)
                        elif "description" in bgp_ipv4_params_text and ipv4_neighbor in dev_data["router_bgp"]["address_family_ipv4"]["neighbors"]:
                            dev_data["router_bgp"]["address_family_ipv4"]["neighbors"][ipv4_neighbor[0]]["description"] = re.sub(r'\s\sneighbor\s\S+\sdescription\s', "", bgp_ipv4_params_text)
                        elif "password" in bgp_ipv4_params_text and ipv4_neighbor[0] not in dev_data["router_bgp"]["address_family_ipv4"]["neighbors"]:
                            dev_data["router_bgp"]["address_family_ipv4"]["neighbors"][ipv4_neighbor[0]] = {} 
                            dev_data["router_bgp"]["address_family_ipv4"]["neighbors"][ipv4_neighbor[0]]["password"] = re.sub(r'\s\sneighbor\s\S+\spassword\s\d+\s', "", bgp_ipv4_params_text)
                        elif "password" in bgp_ipv4_params_text and ipv4_neighbor[0] in dev_data["router_bgp"]["address_family_ipv4"]["neighbors"]:
                            dev_data["router_bgp"]["address_family_ipv4"]["neighbors"][ipv4_neighbor[0]]["password"] = re.sub(r'\s\sneighbor\s\S+\spassword\s\d+\s', "", bgp_ipv4_params_text)
                        elif "activate" in bgp_ipv4_params_text and ipv4_neighbor[0] not in dev_data["router_bgp"]["address_family_ipv4"]["neighbors"]:
                            dev_data["router_bgp"]["address_family_ipv4"]["neighbors"][ipv4_neighbor[0]] = {} 
                            dev_data["router_bgp"]["address_family_ipv4"]["neighbors"][ipv4_neighbor[0]]["activate"] = True
                        elif "activate" in bgp_ipv4_params_text and ipv4_neighbor[0] in dev_data["router_bgp"]["address_family_ipv4"]["neighbors"]:
                            dev_data["router_bgp"]["address_family_ipv4"]["neighbors"][ipv4_neighbor[0]]["activate"] = True
                        elif "route-reflector-client" in bgp_ipv4_params_text and ipv4_neighbor[0] not in dev_data["router_bgp"]["address_family_ipv4"]["neighbors"]:
                            dev_data["router_bgp"]["address_family_ipv4"]["neighbors"][ipv4_neighbor[0]] = {} 
                            dev_data["router_bgp"]["address_family_ipv4"]["neighbors"][ipv4_neighbor[0]]["route-reflector-client"] = True
                        elif "route-reflector-client" in bgp_ipv4_params_text and ipv4_neighbor[0] in dev_data["router_bgp"]["address_family_ipv4"]["neighbors"]:
                            dev_data["router_bgp"]["address_family_ipv4"]["neighbors"][ipv4_neighbor[0]]["route-reflector-client"] = True
                        elif "soft-reconfiguration inbound" in bgp_ipv4_params_text and ipv4_neighbor[0] not in dev_data["router_bgp"]["address_family_ipv4"]["neighbors"]:
                            dev_data["router_bgp"]["address_family_ipv4"]["neighbors"][ipv4_neighbor[0]] = {} 
                            dev_data["router_bgp"]["address_family_ipv4"]["neighbors"][ipv4_neighbor[0]]["soft-reconfiguration inbound"] = True
                        elif "soft-reconfiguration inbound" in bgp_ipv4_params_text and ipv4_neighbor[0] in dev_data["router_bgp"]["address_family_ipv4"]["neighbors"]:
                            dev_data["router_bgp"]["address_family_ipv4"]["neighbors"][ipv4_neighbor[0]]["soft-reconfiguration inbound"] = True
                        elif ipv4_route_map_filter_match and ipv4_neighbor[0] not in dev_data["router_bgp"]["address_family_ipv4"]["neighbors"]:
                            ipv4_route_map_filter = re.findall(r'neighbor\s\S+\s\S+\s(\S+)\s(\w+)', bgp_ipv4_params_text)
                            dev_data["router_bgp"]["address_family_ipv4"]["neighbors"][ipv4_neighbor[0]] = {} 
                            dev_data["router_bgp"]["address_family_ipv4"]["neighbors"][ipv4_neighbor[0]][f'route_map_{ipv4_route_map_filter[0][1]}'] = ipv4_route_map_filter[0][0]
                        elif ipv4_route_map_filter_match and ipv4_neighbor[0] in dev_data["router_bgp"]["address_family_ipv4"]["neighbors"]:
                            ipv4_route_map_filter = re.findall(r'neighbor\s\S+\s\S+\s(\S+)\s(\w+)', bgp_ipv4_params_text)
                            dev_data["router_bgp"]["address_family_ipv4"]["neighbors"][ipv4_neighbor[0]][f'route_map_{ipv4_route_map_filter[0][1]}'] = ipv4_route_map_filter[0][0]

            ### ADDRESS FAMILIES EVALUATION ###
            ### IPV4 VRFS FAMILY ###
            elif ipv4_vrf_af_name and "address_family_ipv4_vrfs" not in dev_data["router_bgp"]:
                dev_data["router_bgp"]["address_family_ipv4_vrfs"] = {}
                dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]] = {}
                dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["no_auto_summary"] = True
                dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["no_synchronization"] = True
                for bgp_ipv4_vrf_params in bgp_line.children:
                    bgp_ipv4_vrf_params_text = bgp_ipv4_vrf_params.text
                    ipv4_vrf_neigh_match = re.match(r'\s\sneighbor\s\S+\s', bgp_ipv4_vrf_params_text)
                    ipv4_vrf_route_map_filter_match = re.match(r'\s\sneighbor\s\S+\sroute-map', bgp_ipv4_vrf_params_text)
                    ipv4_vrf_network_match = re.match(r'\s\snetwork\s', bgp_ipv4_vrf_params_text)
                    if ipv4_vrf_network_match and "networks" not in dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]:
                        ipv4_vrf_network_parameters = re.findall(r'(?<=network\s)(\S+)\smask\s(\S+)(?(?=\s\S+)\sroute-map\s(\S+))', bgp_ipv4_vrf_params_text)
                        dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["networks"] = {}
                        dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["networks"][ipv4_vrf_network_parameters[0][0]] = {}
                        dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["networks"][ipv4_vrf_network_parameters[0][0]]["mask"] =  ipv4_vrf_network_parameters[0][1]
                        if ipv4_vrf_network_parameters[0][2]:
                            dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["networks"][ipv4_vrf_network_parameters[0][0]]["route_map"] = ipv4_vrf_network_parameters[0][2]
                    elif ipv4_vrf_network_match and "networks" in dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]:
                        ipv4_vrf_network_parameters = re.findall(r'(?<=network\s)(\S+)\smask\s(\S+)(?(?=\s\S+)\sroute-map\s(\S+))', bgp_ipv4_vrf_params_text)
                        dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["networks"][ipv4_vrf_network_parameters[0][0]] = {}
                        dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["networks"][ipv4_vrf_network_parameters[0][0]]["mask"] =  ipv4_vrf_network_parameters[0][1]
                        if ipv4_vrf_network_parameters[0][2]:
                            dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["networks"][ipv4_vrf_network_parameters[0][0]]["route_map"] = ipv4_vrf_network_parameters[0][2]
                    elif "redistribute" in bgp_ipv4_vrf_params_text and "redistribution" not in dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]:
                        ipv4_vrf_redistribute_type = re.findall(r'redistribute\s(\w+)', bgp_ipv4_vrf_params_text )
                        ipv4_vrf_redistribute_type = ipv4_vrf_redistribute_type[0]
                        ipv4_vrf_redistribute_route_map = re.findall(r'redistribute\s\w+\sroute-map\s(\S+)', bgp_ipv4_vrf_params_text)
                        dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["redistribution"] = {}
                        dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["redistribution"][ipv4_vrf_redistribute_type] = {}
                        if ipv4_vrf_redistribute_route_map:
                            ipv4_vrf_redistribute_route_map = ipv4_vrf_redistribute_route_map[0]
                            dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["redistribution"][ipv4_vrf_redistribute_type]["route_map"] = ipv4_vrf_redistribute_route_map
                    elif "redistribute" in bgp_ipv4_vrf_params_text and "redistribution" in dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]:
                        ipv4_vrf_redistribute_type = re.findall(r'redistribute\s(\w+)', bgp_ipv4_vrf_params_text )
                        ipv4_vrf_redistribute_type = ipv4_vrf_redistribute_type[0]
                        ipv4_vrf_redistribute_route_map = re.findall(r'redistribute\s\w+\sroute-map\s(\S+)', bgp_ipv4_vrf_params_text)
                        dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["redistribution"][ipv4_vrf_redistribute_type] = {}
                        if ipv4_vrf_redistribute_route_map:
                            ipv4_vrf_redistribute_route_map = ipv4_vrf_redistribute_route_map[0]
                            dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["redistribution"][ipv4_vrf_redistribute_type]["route_map"] = ipv4_vrf_redistribute_route_map
                    elif "aggregate-address" in bgp_ipv4_vrf_params_text and "aggregate_addresses" not in dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]: 
                        ipv4_vrf_aggregate_address = re.findall(r'aggregate-address\s(\S+)\s(\S+)\s(\S+)', bgp_ipv4_vrf_params_text)
                        dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["aggregate_addresses"] = {}
                        dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["aggregate_addresses"][ipv4_vrf_aggregate_address[0][0]] = {}
                        dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["aggregate_addresses"][ipv4_vrf_aggregate_address[0][0]]["mask"] = ipv4_vrf_aggregate_address[0][1]
                        if ipv4_vrf_aggregate_address[0][2] == "summary-only":
                            dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["aggregate_addresses"][ipv4_vrf_aggregate_address[0][2]] = True
                    elif "aggregate-address" in bgp_ipv4_vrf_params_text and "aggregate_addresses" in dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]: 
                        ipv4_vrf_aggregate_address = re.findall(r'aggregate-address\s(\S+)\s(\S+)\s(\S+)', bgp_ipv4_vrf_params_text)
                        dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["aggregate_addresses"][ipv4_vrf_aggregate_address[0][0]] = {}
                        dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["aggregate_addresses"][ipv4_vrf_aggregate_address[0][0]]["mask"] = ipv4_vrf_aggregate_address[0][1]
                        if ipv4_vrf_aggregate_address[0][2] == "summary-only":
                            dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["aggregate_addresses"][ipv4_vrf_aggregate_address[0][2]] = True
                    elif ipv4_vrf_neigh_match and "neighbors" not in dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]: 
                        ipv4_vrf_neighbor = re.findall(r'neighbor\s(\S+)', bgp_ipv4_vrf_params_text)
                        dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["neighbors"] = {}
                        dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["neighbors"][ipv4_vrf_neighbor[0]] = {} 
                        if "description" in bgp_ipv4_vrf_params_text:
                            dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["neighbors"][ipv4_vrf_neighbor[0]]["description"] = re.sub(r'\s\sneighbor\s\S+\sdescription\s', "", bgp_ipv4_vrf_params_text)
                        elif "password" in bgp_ipv4_vrf_params_text:
                            dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["neighbors"][ipv4_vrf_neighbor[0]]["password"] = re.sub(r'\s\sneighbor\s\S+\spassword\s\d+\s', "", bgp_ipv4_vrf_params_text)
                        elif "activate" in bgp_ipv4_vrf_params_text:
                            dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["neighbors"][ipv4_vrf_neighbor[0]]["activate"] = True
                        elif "route-reflector-client" in bgp_ipv4_vrf_params_text:
                            dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["neighbors"][ipv4_vrf_neighbor[0]]["route-reflector-client"] = True
                        elif "soft-reconfiguration inbound" in bgp_ipv4_vrf_params_text:
                            dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["neighbors"][ipv4_vrf_neighbor[0]]["soft-reconfiguration inbound"] = True
                        elif ipv4_vrf_route_map_filter_match:
                            ipv4_route_map_filter = re.findall(r'neighbor\s\S+\s\S+\s(\S+)\s(\w+)', bgp_ipv4_vrf_params_text)
                            dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["neighbors"][ipv4_vrf_neighbor[0]][f'route_map_{ipv4_route_map_filter[0][1]}'] = ipv4_route_map_filter[0][0]
                    elif ipv4_vrf_neigh_match and "neighbors" in dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]: 
                        ipv4_vrf_neighbor = re.findall(r'neighbor\s(\S+)', bgp_ipv4_vrf_params_text)
                        if "description" in bgp_ipv4_vrf_params_text and ipv4_vrf_neighbor not in dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["neighbors"]:
                            dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["neighbors"][ipv4_vrf_neighbor] = {} 
                            dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["neighbors"][ipv4_vrf_neighbor]["description"] = re.sub(r'\s\sneighbor\s\S+\sdescription\s', "", bgp_ipv4_vrf_params_text)
                        elif "description" in bgp_ipv4_vrf_params_text and ipv4_vrf_neighbor in dev_data["router_bgp"]["address_family_ipv4"]["neighbors"]:
                            dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["neighbors"][ipv4_vrf_neighbor[0]]["description"] = re.sub(r'\s\sneighbor\s\S+\sdescription\s', "", bgp_ipv4_vrf_params_text)
                        elif "password" in bgp_ipv4_vrf_params_text and ipv4_vrf_neighbor[0] not in dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["neighbors"]:
                            dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["neighbors"][ipv4_vrf_neighbor[0]] = {} 
                            dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["neighbors"][ipv4_vrf_neighbor[0]]["password"] = re.sub(r'\s\sneighbor\s\S+\spassword\s\d+\s', "", bgp_ipv4_vrf_params_text)
                        elif "password" in bgp_ipv4_vrf_params_text and ipv4_vrf_neighbor[0] in dev_data["router_bgp"]["address_family_ipv4"]["neighbors"]:
                            dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["neighbors"][ipv4_vrf_neighbor[0]]["password"] = re.sub(r'\s\sneighbor\s\S+\spassword\s\d+\s', "", bgp_ipv4_vrf_params_text)
                        elif "activate" in bgp_ipv4_vrf_params_text and ipv4_vrf_neighbor[0] not in dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["neighbors"]:
                            dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["neighbors"][ipv4_vrf_neighbor[0]] = {} 
                            dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["neighbors"][ipv4_vrf_neighbor[0]]["activate"] = True
                        elif "activate" in bgp_ipv4_vrf_params_text and ipv4_vrf_neighbor[0] in dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["neighbors"]:
                            dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["neighbors"][ipv4_vrf_neighbor[0]]["activate"] = True
                        elif "route-reflector-client" in bgp_ipv4_vrf_params_text and ipv4_vrf_neighbor[0] not in dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["neighbors"]:
                            dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["neighbors"][ipv4_vrf_neighbor[0]] = {} 
                            dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["neighbors"][ipv4_vrf_neighbor[0]]["route-reflector-client"] = True
                        elif "route-reflector-client" in bgp_ipv4_vrf_params_text and ipv4_vrf_neighbor[0] in dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["neighbors"]:
                            dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["neighbors"][ipv4_vrf_neighbor[0]]["route-reflector-client"] = True
                        elif "soft-reconfiguration inbound" in bgp_ipv4_vrf_params_text and ipv4_vrf_neighbor[0] not in dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["neighbors"]:
                            dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["neighbors"][ipv4_vrf_neighbor[0]] = {} 
                            dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["neighbors"][ipv4_vrf_neighbor[0]]["soft-reconfiguration inbound"] = True
                        elif "soft-reconfiguration inbound" in bgp_ipv4_vrf_params_text and ipv4_vrf_neighbor[0] in dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["neighbors"]:
                            dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["neighbors"][ipv4_vrf_neighbor[0]]["soft-reconfiguration inbound"] = True
                        elif ipv4_vrf_route_map_filter_match and ipv4_vrf_neighbor[0] not in dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["neighbors"]:
                            ipv4_route_map_filter = re.findall(r'neighbor\s\S+\s\S+\s(\S+)\s(\w+)', bgp_ipv4_vrf_params_text)
                            dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["neighbors"][ipv4_vrf_neighbor[0]] = {} 
                            dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["neighbors"][ipv4_vrf_neighbor[0]][f'route_map_{ipv4_route_map_filter[0][1]}'] = ipv4_route_map_filter[0][0]
                        elif ipv4_vrf_route_map_filter_match and ipv4_vrf_neighbor[0] in dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["neighbors"]:
                            ipv4_route_map_filter = re.findall(r'neighbor\s\S+\s\S+\s(\S+)\s(\w+)', bgp_ipv4_vrf_params_text)
                            dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["neighbors"][ipv4_vrf_neighbor[0]][f'route_map_{ipv4_route_map_filter[0][1]}'] = ipv4_route_map_filter[0][0]
            
            elif ipv4_vrf_af_name and "address_family_ipv4_vrfs" in dev_data["router_bgp"]:
                for bgp_ipv4_vrf_params in bgp_line.children:
                    bgp_ipv4_vrf_params_text = bgp_ipv4_vrf_params.text
                    ipv4_vrf_neigh_match = re.match(r'\s\sneighbor\s\S+\s', bgp_ipv4_vrf_params_text)
                    ipv4_vrf_route_map_filter_match = re.match(r'\s\sneighbor\s\S+\sroute-map', bgp_ipv4_vrf_params_text)
                    ipv4_vrf_network_match = re.match(r'\s\snetwork\s', bgp_ipv4_vrf_params_text)
                    if ipv4_vrf_network_match and "networks" not in dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]:
                        ipv4_vrf_network_parameters = re.findall(r'(?<=network\s)(\S+)\smask\s(\S+)(?(?=\s\S+)\sroute-map\s(\S+))', bgp_ipv4_vrf_params_text)
                        dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["networks"] = {}
                        dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["networks"][ipv4_vrf_network_parameters[0][0]] = {}
                        dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["networks"][ipv4_vrf_network_parameters[0][0]]["mask"] =  ipv4_vrf_network_parameters[0][1]
                        if ipv4_vrf_network_parameters[0][2]:
                            dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["networks"][ipv4_vrf_network_parameters[0][0]]["route_map"] = ipv4_vrf_network_parameters[0][2]
                    elif ipv4_vrf_network_match and "networks" in dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]:
                        ipv4_vrf_network_parameters = re.findall(r'(?<=network\s)(\S+)\smask\s(\S+)(?(?=\s\S+)\sroute-map\s(\S+))', bgp_ipv4_vrf_params_text)
                        dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["networks"][ipv4_vrf_network_parameters[0][0]] = {}
                        dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["networks"][ipv4_vrf_network_parameters[0][0]]["mask"] =  ipv4_vrf_network_parameters[0][1]
                        if ipv4_vrf_network_parameters[0][2]:
                            dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["networks"][ipv4_vrf_network_parameters[0][0]]["route_map"] = ipv4_vrf_network_parameters[0][2]
                    elif "redistribute" in bgp_ipv4_vrf_params_text and "redistribution" not in dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]:
                        ipv4_vrf_redistribute_type = re.findall(r'redistribute\s(\w+)', bgp_ipv4_vrf_params_text )
                        ipv4_vrf_redistribute_type = ipv4_vrf_redistribute_type[0]
                        ipv4_vrf_redistribute_route_map = re.findall(r'redistribute\s\w+\sroute-map\s(\S+)', bgp_ipv4_vrf_params_text)
                        dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["redistribution"] = {}
                        dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["redistribution"][ipv4_vrf_redistribute_type] = {}
                        if ipv4_vrf_redistribute_route_map:
                            ipv4_vrf_redistribute_route_map = ipv4_vrf_redistribute_route_map[0]
                            dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["redistribution"][ipv4_vrf_redistribute_type]["route_map"] = ipv4_vrf_redistribute_route_map
                    elif "redistribute" in bgp_ipv4_vrf_params_text and "redistribution" in dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]:
                        ipv4_vrf_redistribute_type = re.findall(r'redistribute\s(\w+)', bgp_ipv4_vrf_params_text )
                        ipv4_vrf_redistribute_type = ipv4_vrf_redistribute_type[0]
                        ipv4_vrf_redistribute_route_map = re.findall(r'redistribute\s\w+\sroute-map\s(\S+)', bgp_ipv4_vrf_params_text)
                        dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["redistribution"][ipv4_vrf_redistribute_type] = {}
                        if ipv4_vrf_redistribute_route_map:
                            ipv4_vrf_redistribute_route_map = ipv4_vrf_redistribute_route_map[0]
                            dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["redistribution"][ipv4_vrf_redistribute_type]["route_map"] = ipv4_vrf_redistribute_route_map
                    elif "aggregate-address" in bgp_ipv4_vrf_params_text and "aggregate_addresses" not in dev_data["router_bgp"]["address_family_ipv4"]: 
                        ipv4_vrf_aggregate_address = re.findall(r'aggregate-address\s(\S+)\s(\S+)\s(\S+)', bgp_ipv4_vrf_params_text)
                        dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["aggregate_addresses"] = {}
                        dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["aggregate_addresses"][ipv4_vrf_aggregate_address[0][0]] = {}
                        dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["aggregate_addresses"][ipv4_vrf_aggregate_address[0][0]]["mask"] = ipv4_vrf_aggregate_address[0][1]
                        if ipv4_vrf_aggregate_address[0][2] == "summary-only":
                            dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["aggregate_addresses"][ipv4_vrf_aggregate_address[0][2]] = True
                    elif "aggregate-address" in bgp_ipv4_vrf_params_text and "aggregate_addresses" in dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]: 
                        ipv4_vrf_aggregate_address = re.findall(r'aggregate-address\s(\S+)\s(\S+)\s(\S+)', bgp_ipv4_vrf_params_text)
                        dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["aggregate_addresses"][ipv4_vrf_aggregate_address[0][0]] = {}
                        dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["aggregate_addresses"][ipv4_vrf_aggregate_address[0][0]]["mask"] = ipv4_vrf_aggregate_address[0][1]
                        if ipv4_vrf_aggregate_address[0][2] == "summary-only":
                            dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["aggregate_addresses"][ipv4_vrf_aggregate_address[0][2]] = True
                    elif ipv4_vrf_neigh_match and "neighbors" not in dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]: 
                        ipv4_vrf_neighbor = re.findall(r'neighbor\s(\S+)', bgp_ipv4_vrf_params_text)
                        dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["neighbors"] = {}
                        dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["neighbors"][ipv4_vrf_neighbor[0]] = {} 
                        if "description" in bgp_ipv4_vrf_params_text:
                            dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["neighbors"][ipv4_vrf_neighbor[0]]["description"] = re.sub(r'\s\sneighbor\s\S+\sdescription\s', "", bgp_ipv4_vrf_params_text)
                        elif "password" in bgp_ipv4_vrf_params_text:
                            dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["neighbors"][ipv4_vrf_neighbor[0]]["password"] = re.sub(r'\s\sneighbor\s\S+\spassword\s\d+\s', "", bgp_ipv4_vrf_params_text)
                        elif "activate" in bgp_ipv4_vrf_params_text:
                            dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["neighbors"][ipv4_vrf_neighbor[0]]["activate"] = True
                        elif "route-reflector-client" in bgp_ipv4_vrf_params_text:
                            dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["neighbors"][ipv4_vrf_neighbor[0]]["route-reflector-client"] = True
                        elif "soft-reconfiguration inbound" in bgp_ipv4_vrf_params_text:
                            dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["neighbors"][ipv4_vrf_neighbor[0]]["soft-reconfiguration inbound"] = True
                        elif ipv4_vrf_route_map_filter_match:
                            ipv4_route_map_filter = re.findall(r'neighbor\s\S+\s\S+\s(\S+)\s(\w+)', bgp_ipv4_vrf_params_text)
                            dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["neighbors"][ipv4_vrf_neighbor[0]][f'route_map_{ipv4_route_map_filter[0][1]}'] = ipv4_route_map_filter[0][0]
                    elif ipv4_vrf_neigh_match and "neighbors" in dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]: 
                        ipv4_vrf_neighbor = re.findall(r'neighbor\s(\S+)', bgp_ipv4_vrf_params_text)
                        if "description" in bgp_ipv4_vrf_params_text and ipv4_vrf_neighbor not in dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["neighbors"]:
                            dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["neighbors"][ipv4_vrf_neighbor] = {} 
                            dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["neighbors"][ipv4_vrf_neighbor]["description"] = re.sub(r'\s\sneighbor\s\S+\sdescription\s', "", bgp_ipv4_vrf_params_text)
                        elif "description" in bgp_ipv4_vrf_params_text and ipv4_vrf_neighbor in dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["neighbors"]:
                            dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["neighbors"][ipv4_vrf_neighbor[0]]["description"] = re.sub(r'\s\sneighbor\s\S+\sdescription\s', "", bgp_ipv4_vrf_params_text)
                        elif "password" in bgp_ipv4_vrf_params_text and ipv4_vrf_neighbor[0] not in dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["neighbors"]:
                            dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["neighbors"][ipv4_vrf_neighbor[0]] = {} 
                            dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["neighbors"][ipv4_vrf_neighbor[0]]["password"] = re.sub(r'\s\sneighbor\s\S+\spassword\s\d+\s', "", bgp_ipv4_vrf_params_text)
                        elif "password" in bgp_ipv4_vrf_params_text and ipv4_vrf_neighbor[0] in dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["neighbors"]:
                            dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["neighbors"][ipv4_vrf_neighbor[0]]["password"] = re.sub(r'\s\sneighbor\s\S+\spassword\s\d+\s', "", bgp_ipv4_vrf_params_text)
                        elif "activate" in bgp_ipv4_vrf_params_text and ipv4_vrf_neighbor[0] not in dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["neighbors"]:
                            dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["neighbors"][ipv4_vrf_neighbor[0]] = {} 
                            dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["neighbors"][ipv4_vrf_neighbor[0]]["activate"] = True
                        elif "activate" in bgp_ipv4_vrf_params_text and ipv4_vrf_neighbor[0] in dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["neighbors"]:
                            dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["neighbors"][ipv4_vrf_neighbor[0]]["activate"] = True
                        elif "route-reflector-client" in bgp_ipv4_vrf_params_text and ipv4_vrf_neighbor[0] not in dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["neighbors"]:
                            dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["neighbors"][ipv4_vrf_neighbor[0]] = {} 
                            dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["neighbors"][ipv4_vrf_neighbor[0]]["route-reflector-client"] = True
                        elif "route-reflector-client" in bgp_ipv4_vrf_params_text and ipv4_vrf_neighbor[0] in dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["neighbors"]:
                            dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["neighbors"][ipv4_vrf_neighbor[0]]["route-reflector-client"] = True
                        elif "soft-reconfiguration inbound" in bgp_ipv4_vrf_params_text and ipv4_vrf_neighbor[0] not in dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["neighbors"]:
                            dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["neighbors"][ipv4_vrf_neighbor[0]] = {} 
                            dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["neighbors"][ipv4_vrf_neighbor[0]]["soft-reconfiguration inbound"] = True
                        elif "soft-reconfiguration inbound" in bgp_ipv4_vrf_params_text and ipv4_vrf_neighbor[0] in dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["neighbors"]:
                            dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["neighbors"][ipv4_vrf_neighbor[0]]["soft-reconfiguration inbound"] = True
                        elif ipv4_vrf_route_map_filter_match and ipv4_vrf_neighbor[0] not in dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["neighbors"]:
                            ipv4_route_map_filter = re.findall(r'neighbor\s\S+\s\S+\s(\S+)\s(\w+)', bgp_ipv4_vrf_params_text)
                            dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["neighbors"][ipv4_vrf_neighbor[0]] = {} 
                            dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["neighbors"][ipv4_vrf_neighbor[0]][f'route_map_{ipv4_route_map_filter[0][1]}'] = ipv4_route_map_filter[0][0]
                        elif ipv4_vrf_route_map_filter_match and ipv4_vrf_neighbor[0] in dev_data["router_bgp"]["address_family_ipv4"]["neighbors"]:
                            ipv4_route_map_filter = re.findall(r'neighbor\s\S+\s\S+\s(\S+)\s(\w+)', bgp_ipv4_vrf_params_text)
                            dev_data["router_bgp"]["address_family_ipv4_vrfs"][ipv4_vrf_af_name[0]]["neighbors"][ipv4_vrf_neighbor[0]][f'route_map_{ipv4_route_map_filter[0][1]}'] = ipv4_route_map_filter[0][0]

    return dev_data