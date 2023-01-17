#! /usr/bin/env python
"""
Script to parse Static Routing configs
"""
import regex as re
from netaddr import valid_ipv4, IPAddress

def audit_static(parse_obj):
    """ Parse Static Routing """
    dev_data = {}
    dev_data["static_routes"] = []
    static_routes = parse_obj.find_objects(r'^ip\sroute')

    for static_lines in static_routes:
        route_dict = {}
        static_lines_text = static_lines.text
        static_route = re.findall(r'(?<=ip\sroute\s)(?(?=vrf\s)\S+\s(\S+)\s)(\S+)\s(\S+)\s(\S+)', static_lines_text)
        ### EVALUATE WHEN ROUTE BELONGS TO GLOBAL ###
        if static_route:
            if static_route[0][0]:
                dest_ip = static_route[0][1]
                dest_prefix = IPAddress(static_route[0][2]).netmask_bits()
                route_dict["destination_address_prefix"] = f'{dest_ip}/{dest_prefix}'
                if valid_ipv4(static_route[0][3]):
                    route_dict["gateway"] = static_route[0][3]
                else:
                    route_dict["interface"] = static_route[0][3]
                dev_data["static_routes"].append(route_dict)
            ### EVALUATE WHEN ROUTE BELONGS TO A VRF ###
            else:
                dest_ip = static_route[0][1]
                print(static_route)
                dest_prefix = IPAddress(static_route[0][2]).netmask_bits()
                route_dict["vrf"] = static_route[0][0]
                route_dict["destination_address_prefix"] = f'{dest_ip}/{dest_prefix}'
                if valid_ipv4(static_route[0][3]):
                        route_dict["gateway"] = static_route[0][3]
                else:
                    route_dict["interface"] = static_route[0][3]
                dev_data["static_routes"].append(route_dict)

    return dev_data