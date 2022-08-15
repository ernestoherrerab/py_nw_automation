#! /usr/bin/env python
"""
Script to parse SNMP configs
"""
import re


def audit_snmp(parse_obj):
    """ Parse SNMP """
    dev_data = {}
    dev_data["snmp_server"] = {}
    dev_data["snmp_server"]["traps"] = {}
    dev_data["snmp_server"]["traps"]["hosts"] = []
    snmp_lines = parse_obj.find_objects(r'^snmp-server')

    ### EVALUATE SNMP ###
    for snmp_line in snmp_lines:
        snmp_line_text = snmp_line.text
        snmp_communities = re.findall(r'snmp-server\scommunity\s(\S+)\s(\w+)\s(\S+)', snmp_line_text)
        snmp_location = re.findall(r'snmp-server\slocation\s(\S+)', snmp_line_text)
        snmp_contact = re.findall(r'snmp-server\scontact\s(\S+)', snmp_line_text)
        snmp_traps = re.findall(r'snmp-server\senable\straps\s(.+)$', snmp_line_text)
        snmp_host = re.findall(r'snmp-server\shost\s(\S+)\s(\w+)', snmp_line_text)
        if snmp_communities and "communities" not in dev_data["snmp_server"]:
            dev_data["snmp_server"]["communities"] = {}
            dev_data["snmp_server"]["communities"][snmp_communities[0][0]] = {}
            dev_data["snmp_server"]["communities"][snmp_communities[0][0]]["access"] = snmp_communities[0][1]
            if snmp_communities[0][2] != "":
                dev_data["snmp_server"]["communities"][snmp_communities[0][0]]["access_list_ipv4"] = snmp_communities[0][2]
        elif snmp_communities and "communities" in dev_data["snmp_server"]:
            dev_data["snmp_server"]["communities"][snmp_communities[0][0]] = {}
            dev_data["snmp_server"]["communities"][snmp_communities[0][0]]["access"] = snmp_communities[0][1]
            if snmp_communities[0][2] != "":
                dev_data["snmp_server"]["communities"][snmp_communities[0][0]]["access_list_ipv4"] = snmp_communities[0][2]
        elif snmp_location: 
            dev_data["snmp_server"]["location"] = snmp_location[0]
        elif snmp_contact: 
            dev_data["snmp_server"]["contact"] = snmp_contact[0]
        elif snmp_traps and "snmp_traps" not in dev_data["snmp_server"]["traps"]:
            dev_data["snmp_server"]["traps"]["snmp_traps"] = []
            dev_data["snmp_server"]["traps"]["snmp_traps"].append(snmp_traps[0])
        elif snmp_traps and "snmp_traps" in dev_data["snmp_server"]["traps"]:
            dev_data["snmp_server"]["traps"]["snmp_traps"].append(snmp_traps[0])
        elif snmp_host:
            dev_data["snmp_server"]["traps"]["hosts"].append({"name": snmp_host[0][0], "community": snmp_host[0][1]})

    return dev_data