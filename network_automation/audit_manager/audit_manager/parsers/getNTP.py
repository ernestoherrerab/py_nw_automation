#! /usr/bin/env python
"""
Script to parse AAA configs
"""

def audit_ntp(parse_obj):
    dev_data = {}
    """ Parse NTP """
    dev_data["ntp"] = {}
    dev_data["ntp"]["ntp"] = {}
    ntp_server_lines = parse_obj.find_objects(r"^ntp server")
    ntp_source_line = parse_obj.find_objects(r"^ntp source")
    dev_data["ntp"]["ntp"]["servers"] = {}
    if ntp_source_line:
        dev_data["ntp"]["ntp"]["source"] = ntp_source_line[0].text.replace("ntp source", "").replace(" ", "", 1)

    for ntp_server_line in ntp_server_lines:
        if "prefer" in ntp_server_line.text:
            ntp_server_line = ntp_server_line.text.replace("prefer", "").replace("ntp server", "").replace(" ", "", 1)
            ntp_server_line = ntp_server_line[:-1]
            dev_data["ntp"]["ntp"]["servers"][ntp_server_line] = {}
            dev_data["ntp"]["ntp"]["servers"][ntp_server_line]["prefer"] = "true"
        elif "prefer" not in ntp_server_line.text:
            ntp_server_line = ntp_server_line.text.replace("prefer", "").replace("ntp server", "").replace(" ", "")
            dev_data["ntp"]["ntp"]["servers"][ntp_server_line] = {}
            dev_data["ntp"]["ntp"]["servers"][ntp_server_line]["prefer"] = "false"

    return dev_data