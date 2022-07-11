#! /usr/bin/env python
"""
Script to parse AAA configs
"""

def audit_ntp(parse_obj):
    """ Parse NTP & Clock """

    dev_data = {}
    dev_data["ntp"] = {}
    dev_data["ntp"]["servers"] = {}
    dev_data["clock"] = {}
    ntp_server_lines = parse_obj.find_objects(r"^ntp server")
    ntp_source_line = parse_obj.find_objects(r"^ntp source")
    clock_lines = parse_obj.find_objects(r"^clock")

    if ntp_source_line:
        dev_data["ntp"]["source"] = ntp_source_line[0].text.replace("ntp source", "").replace(" ", "", 1)

    for ntp_server_line in ntp_server_lines:
        if "prefer" in ntp_server_line.text:
            ntp_server_line = ntp_server_line.text.replace("prefer", "").replace("ntp server", "").replace(" ", "", 1)
            ntp_server_line = ntp_server_line[:-1]
            dev_data["ntp"]["servers"][ntp_server_line] = {}
            dev_data["ntp"]["servers"][ntp_server_line]["prefer"] = "true"
        elif "prefer" not in ntp_server_line.text:
            ntp_server_line = ntp_server_line.text.replace("prefer", "").replace("ntp server", "").replace(" ", "")
            dev_data["ntp"]["servers"][ntp_server_line] = {}
            dev_data["ntp"]["servers"][ntp_server_line]["prefer"] = "false"
    
    for clock_line in clock_lines:
        if "timezone" in clock_line.text:
            clock_line = clock_line.text.replace("clock timezone", "").replace(" ", "", 1)
            dev_data["clock"]["timezone"] = clock_line
        elif "summer-time" in clock_line.text:
            clock_line = clock_line.text.replace("clock summer-time", "").replace(" ", "", 1)
            clock_line = clock_line[:-1]
            dev_data["clock"]["summertime"] = clock_line

    return dev_data