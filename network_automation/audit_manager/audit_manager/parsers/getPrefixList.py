#! /usr/bin/env python
"""
Script to parse Prefix Lists configs
"""
import re


def audit_prefix_list(parse_obj):
    """ Parse Prefix Lists """
    dev_data = {}
    dev_data["prefix_lists"] = {}
    prefix_list_lines = parse_obj.find_objects(r'^ip\sprefix-list')

    ### EVALUATE PREFIX LISTS ###
    for prefix_line in prefix_list_lines:
        prefix_line_text = prefix_line.text
        prefix_list_parameters = re.findall(r'ip\sprefix-list\s(\S+)\sseq\s(\d+)\s(.+)', prefix_line_text)
        prefix_list_name = prefix_list_parameters[0][0]
        prefix_list_seq = int(prefix_list_parameters[0][1])
        prefix_action = prefix_list_parameters[0][2]
        if prefix_list_name not in dev_data["prefix_lists"]:
            dev_data["prefix_lists"][prefix_list_name] = {}
            dev_data["prefix_lists"][prefix_list_name]["sequence_numbers"] = {}
            dev_data["prefix_lists"][prefix_list_name]["sequence_numbers"][prefix_list_seq] = {}
            dev_data["prefix_lists"][prefix_list_name]["sequence_numbers"][prefix_list_seq]["action"] = prefix_action
        elif prefix_list_name in dev_data["prefix_lists"]: 
            if "sequence_numbers" not in dev_data["prefix_lists"][prefix_list_name]:
                dev_data["prefix_lists"][prefix_list_name]["sequence_numbers"] = {}
                dev_data["prefix_lists"][prefix_list_name]["sequence_numbers"][prefix_list_seq] = {}
                dev_data["prefix_lists"][prefix_list_name]["sequence_numbers"][prefix_list_seq]["action"] = prefix_action
            elif "sequence_numbers" in dev_data["prefix_lists"][prefix_list_name]:
                dev_data["prefix_lists"][prefix_list_name]["sequence_numbers"][prefix_list_seq] = {}
                dev_data["prefix_lists"][prefix_list_name]["sequence_numbers"][prefix_list_seq]["action"] = prefix_action            

    return dev_data