#! /usr/bin/env python
"""
Module to display the available diagrams
"""

from pathlib import Path

def get_hostname_data():
    """ Get diagrams path information """

    src_dir = Path("documentation/hostname_changes/")
    hostname_data_list = []
    for hostname_path in src_dir.iterdir():
        if hostname_path.suffix == ".txt":
            hostname_dir = str(hostname_path)
            hostname_name = str(hostname_path).replace(str(src_dir) + "/", "")
            hostname_data = (hostname_dir, hostname_name)
            hostname_data_list.append(hostname_data)
    
    return hostname_data_list
