#! /usr/bin/env python
"""
Main program to audit devices configurations 
"""

from pathlib import Path
from ciscoconfparse import CiscoConfParse
from yaml import dump
from yaml import SafeDumper
import network_automation.standards_ops.audit_manager.getConfig as get_config
import network_automation.standards_ops.audit_manager.parsers.getAAA as getAAA
import network_automation.standards_ops.audit_manager.parsers.getACL as getACL
import network_automation.standards_ops.audit_manager.parsers.getBase as getBase
import network_automation.standards_ops.audit_manager.parsers.getBGP as getBGP
import network_automation.standards_ops.audit_manager.parsers.getInterfaces as getInterfaces
import network_automation.standards_ops.audit_manager.parsers.getNTP as getNTP
import network_automation.standards_ops.audit_manager.parsers.getPrefixList as getPrefixList
import network_automation.standards_ops.audit_manager.parsers.getRouteMap as getRouteMap
import network_automation.standards_ops.audit_manager.parsers.getSNMP as getSNMP
import network_automation.standards_ops.audit_manager.parsers.getStatic as getStatic
import network_automation.standards_ops.audit_manager.parsers.getSTP as getSTP
import network_automation.standards_ops.audit_manager.parsers.getSVI as getSVI
import network_automation.standards_ops.audit_manager.parsers.getVLAN as getVLAN
import network_automation.standards_ops.audit_manager.parsers.getVRF as getVRF


class NoAliasDumper(SafeDumper):
    def ignore_aliases(self, data):
        return True
    def increase_indent(self, flow=False, indentless=False):
        return super(NoAliasDumper, self).increase_indent(flow, False)

def build_yml_file(section, input, directory):
    """Convert Python Dict into YAML format and dumps it in a file"""
    yaml_file = section + '.yml'
    yaml_file_path = directory / yaml_file
    with open(str(yaml_file_path), 'w+') as yaml_file:
        dump(input, yaml_file, default_flow_style=False, width=1000, Dumper=NoAliasDumper)   

def do_audit(username, password, depth_levels=3):
    """ Parse configurations """

    dev_configs = get_config.get_config(username, password, depth_levels)

    for dev_config in dev_configs:
        Path(str(dev_config[1]).replace("run_config", "audits") + "/").mkdir(exist_ok=True)
        dev_audit_path = Path(str(dev_config[1]).replace("run_config", "audits") + "/")
        dev_data = {}
        dev_data[dev_config[0]] = {}
        parse_obj = CiscoConfParse(dev_config[1])
        print(dev_config[1])
        
        #### PARSE BASE CONFIGS & DUMP INTO FILE ###
        print("Getting Base Configs...")
        dev_data[dev_config[0]] = getBase.audit_base(parse_obj)
        build_yml_file("base", dev_data[dev_config[0]], dev_audit_path)

        #### PARSE AAA & DUMP INTO FILE ###
        print("Getting AAA Configs...")
        dev_data[dev_config[0]] = getAAA.audit_aaa(parse_obj, dev_config[0])
        build_yml_file("aaa", dev_data[dev_config[0]], dev_audit_path)

        #### PARSE NTP & CLOCK & DUMP INTO FILE ###
        print("Getting NTP Configs...")
        dev_data[dev_config[0]] = getNTP.audit_ntp(parse_obj, dev_config[0])
        build_yml_file("ntp", dev_data[dev_config[0]], dev_audit_path)

        #### PARSE VLANS & DUMP INTO FILE ###
        print("Getting VLAN Configs...")
        dev_data[dev_config[0]] = getVLAN.audit_vlan(parse_obj)
        build_yml_file("vlans", dev_data[dev_config[0]], dev_audit_path)

        #### PARSE SVIS & DUMP INTO FILE ###
        print("Getting SVIs Configs...")
        dev_data[dev_config[0]] = getSVI.audit_svi(parse_obj)
        build_yml_file("svis", dev_data[dev_config[0]], dev_audit_path)

        #### PARSE INTERFACES & DUMP INTO FILE ###
        print("Getting interfaces Configs...")
        dev_data[dev_config[0]] = getInterfaces.audit_interfaces(parse_obj)
        build_yml_file("interfaces", dev_data[dev_config[0]], dev_audit_path)

        #### PARSE STP & DUMP INTO FILE ###
        print("Getting STP Configs...")
        dev_data[dev_config[0]] = getSTP.audit_stp(parse_obj)
        build_yml_file("stp", dev_data[dev_config[0]], dev_audit_path)

        #### PARSE VRF & DUMP INTO FILE ###
        print("Getting VRF Configs...")
        dev_data[dev_config[0]] = getVRF.audit_vrf(parse_obj)
        build_yml_file("vrf", dev_data[dev_config[0]], dev_audit_path)

        #### PARSE BGP & DUMP INTO FILE ###
        print("Getting BGP Configs...")
        dev_data[dev_config[0]] = getBGP.audit_bgp(parse_obj)
        build_yml_file("router_bgp", dev_data[dev_config[0]], dev_audit_path)

        ##### PARSE STATIC ROUTES & DUMP INTO FILE ###
        #print("Getting Static Routes Configs...")
        #dev_data[dev_config[0]] = getStatic.audit_static(parse_obj)
        #build_yml_file("routing_static", dev_data[dev_config[0]], dev_audit_path)

        #### PARSE ACLS & DUMP INTO FILE ###
        print("Getting ACLs Configs...")
        dev_data[dev_config[0]] = getACL.audit_acl(parse_obj)
        build_yml_file("access_lists", dev_data[dev_config[0]], dev_audit_path)

        #### PARSE PREFIX LISTS & DUMP INTO FILE ###
        print("Getting Prefix Lists Configs...")
        dev_data[dev_config[0]] = getPrefixList.audit_prefix_list(parse_obj)
        build_yml_file("prefix_lists", dev_data[dev_config[0]], dev_audit_path)

        #### PARSE ROUTE MAPS & DUMP INTO FILE ###
        print("Getting Route Maps Configs...")
        dev_data[dev_config[0]] = getRouteMap.audit_route_map(parse_obj)
        build_yml_file("route_maps", dev_data[dev_config[0]], dev_audit_path)

        #### PARSE SNMP & DUMP INTO FILE ###
        print("Getting SNMP Server Configs...")
        dev_data[dev_config[0]] = getSNMP.audit_snmp(parse_obj)
        build_yml_file("snmp", dev_data[dev_config[0]], dev_audit_path)