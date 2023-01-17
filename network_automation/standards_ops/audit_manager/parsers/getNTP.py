#! /usr/bin/env python
"""
Script to parse NTP & Clock configs
"""

def audit_ntp(parse_obj, hostname):
    """ Parse NTP & Clock """

    dev_data = {}
    dev_data[hostname] = {}
    dev_data[hostname]["servers"] = []
    dev_data[hostname]["clock"] = []
    ntp_server_lines = parse_obj.find_objects(r"^ntp server")
    ntp_source_line = parse_obj.find_objects(r"^ntp source")
    clock_lines = parse_obj.find_objects(r"^clock")

    if ntp_source_line:
        dev_data[hostname]["source"] = ntp_source_line[0].text
    if ntp_server_lines:
        for ntp_server_line in ntp_server_lines:
            dev_data[hostname]["servers"].append(ntp_server_line.text)
    if clock_lines:
        for clock_line in clock_lines:
            dev_data[hostname]["clock"].append(clock_line.text)

    return dev_data