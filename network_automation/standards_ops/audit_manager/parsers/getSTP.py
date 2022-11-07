#! /usr/bin/env python
"""
Script to parse STP configs
"""
import re

def audit_stp(parse_obj):
    """ Parse STP """

    dev_data = {}
    dev_data["spanning_tree"] = {}
    stp_lines = parse_obj.find_objects(r"^spanning-tree")

    for stp_line in stp_lines:
        ### EVALUATE STP MODE ###
        stp_data = stp_line.text.replace("spanning-tree ", "")
        if "mode" in stp_data:
            dev_data["spanning_tree"]["mode"] = stp_data.replace("mode ", "")
        ### EVALUATE MST INSTANCES ###
        if "mst" in stp_data and ("root" in stp_data or "priority" in stp_data ):   
            if "mst" not in dev_data["spanning_tree"]:
                mst_params = re.findall(r'mst\s(\S+)\s(\w+)\s(\S+)', stp_data)
                dev_data["spanning_tree"]["mst"] = {}
                dev_data["spanning_tree"]["mst"]["mst_instances"] = {}
                dev_data["spanning_tree"]["mst"]["mst_instances"][mst_params[0][0]] = {}
                dev_data["spanning_tree"]["mst"]["mst_instances"][mst_params[0][0]][mst_params[0][1]] = mst_params[0][2]
            elif "mst" in dev_data["spanning_tree"] and "mst_instances" not in dev_data["spanning_tree"]["mst"]:
                mst_params = re.findall(r'mst\s(\S+)\s(\w+)\s(\S+)', stp_data)
                dev_data["spanning_tree"]["mst"]["mst_instances"] = {}
                dev_data["spanning_tree"]["mst"]["mst_instances"][mst_params[0][0]] = {}
                dev_data["spanning_tree"]["mst"]["mst_instances"][mst_params[0][0]][mst_params[0][1]] = mst_params[0][2]
            elif "mst" in dev_data["spanning_tree"] and "mst_instances" in dev_data["spanning_tree"]["mst"]:
                mst_params = re.findall(r'mst\s(\S+)\s(\w+)\s(\S+)', stp_data)
                dev_data["spanning_tree"]["mst"]["mst_instances"][mst_params[0][0]] = {}
                dev_data["spanning_tree"]["mst"]["mst_instances"][mst_params[0][0]][mst_params[0][1]] = mst_params[0][2]      
        ### EVALUATE MST CONFIGURATION ###
        elif "mst configuration" in stp_data:
            for stp_conf in stp_line.children:
                stp_conf = stp_conf.text.replace(" ", "", 1)
                if "mst" not in dev_data["spanning_tree"]:
                    dev_data["spanning_tree"]["mst"] = {}
                    dev_data["spanning_tree"]["mst"]["configuration"] = {}
                    if "name" in stp_conf:
                        dev_data["spanning_tree"]["mst"]["configuration"]["name"] = stp_conf.replace("name ", "")
                    elif "revision" in stp_conf:
                        dev_data["spanning_tree"]["mst"]["configuration"]["revision"] = int(stp_conf.replace("revision ", ""))
                    elif "instance" in stp_conf and "instance" not in dev_data["spanning_tree"]["mst"]["configuration"]:
                        mst_instance_params = re.findall(r'instance\s(\d+)\svlan\s(\S+)', stp_conf)
                        dev_data["spanning_tree"]["mst"]["configuration"]["instances"] = {}
                        dev_data["spanning_tree"]["mst"]["configuration"]["instances"][mst_instance_params[0][0]] = {}
                        dev_data["spanning_tree"]["mst"]["configuration"]["instances"][mst_instance_params[0][0]]["vlans"] = mst_instance_params[0][1]
                    elif "instance" in stp_conf and "instance" in dev_data["spanning_tree"]["mst"]["configuration"]:
                        mst_instance_params = re.findall(r'instance\s(\d+)\svlan\s(\S+)', stp_conf)
                        dev_data["spanning_tree"]["mst"]["configuration"]["instances"][mst_instance_params[0][0]] = {}
                        dev_data["spanning_tree"]["mst"]["configuration"]["instances"][mst_instance_params[0][0]]["vlans"] = mst_instance_params[0][1]
                elif "mst" in dev_data["spanning_tree"] and "configuration" not in dev_data["spanning_tree"]["mst"] :
                    dev_data["spanning_tree"]["mst"]["configuration"] = {}
                    if "name" in stp_conf:
                        dev_data["spanning_tree"]["mst"]["configuration"]["name"] = stp_conf.replace("name ", "")
                    elif "revision" in stp_conf:
                        dev_data["spanning_tree"]["mst"]["configuration"]["revision"] = int(stp_conf.replace("revision ", ""))
                    elif "instance" in stp_conf and "instance" not in dev_data["spanning_tree"]["mst"]["configuration"]:
                        mst_instance_params = re.findall(r'instance\s(\d+)\svlan\s(\S+)', stp_conf)
                        dev_data["spanning_tree"]["mst"]["configuration"]["instances"] = {}
                        dev_data["spanning_tree"]["mst"]["configuration"]["instances"][mst_instance_params[0][0]] = {}
                        dev_data["spanning_tree"]["mst"]["configuration"]["instances"][mst_instance_params[0][0]]["vlans"] = mst_instance_params[0][1] 
                    elif "instance" in stp_conf and "instance" in dev_data["spanning_tree"]["mst"]["configuration"]:
                        mst_instance_params = re.findall(r'instance\s(\d+)\svlan\s(\S+)', stp_conf)
                        dev_data["spanning_tree"]["mst"]["configuration"]["instances"][mst_instance_params[0][0]] = {}
                        dev_data["spanning_tree"]["mst"]["configuration"]["instances"][mst_instance_params[0][0]]["vlans"] = mst_instance_params[0][1]
                elif "mst" in dev_data["spanning_tree"] and "configuration" in dev_data["spanning_tree"]["mst"] :
                    if "name" in stp_conf:
                        dev_data["spanning_tree"]["mst"]["configuration"]["name"] = stp_conf.replace("name ", "")
                    elif "revision" in stp_conf:
                        dev_data["spanning_tree"]["mst"]["configuration"]["revision"] = int(stp_conf.replace("revision ", ""))
                    elif "instance" in stp_conf and "instance" not in dev_data["spanning_tree"]["mst"]["configuration"]:
                        mst_instance_params = re.findall(r'instance\s(\d+)\svlan\s(\S+)', stp_conf)
                        dev_data["spanning_tree"]["mst"]["configuration"]["instances"] = {}
                        dev_data["spanning_tree"]["mst"]["configuration"]["instances"][mst_instance_params[0][0]] = {}
                        dev_data["spanning_tree"]["mst"]["configuration"]["instances"][mst_instance_params[0][0]]["vlans"] = mst_instance_params[0][1]
                    elif "instance" in stp_conf and "instance" in dev_data["spanning_tree"]["mst"]["configuration"]:
                        mst_instance_params = re.findall(r'instance\s(\d+)\svlan\s(\S+)', stp_conf)
                        dev_data["spanning_tree"]["mst"]["configuration"]["instances"][mst_instance_params[0][0]] = {}
                        dev_data["spanning_tree"]["mst"]["configuration"]["instances"][mst_instance_params[0][0]]["vlans"] = mst_instance_params[0][1] 
    return dev_data