#! /usr/bin/env python
"""
Build inventory from audits
"""
from pathlib import Path
from yaml import dump

def build_audit_inv(site_code: str):
    """ Build Inventory from Audit Files

    Args:
    site_code (str) -> From User input

    Return:
    open_file (file) -> Writes the inventory file
    """
    ### VARS ###
    inv_dict = {}
    INV_PATH_FILE = (Path("network_automation/standards_ops/inventory/") / "hosts.yml")

    ### GET HOSTS IP ADDRESSES ###
    audit_docs = Path(f"file_display/public/documentation/{site_code.lower()}/audits/")    
    host_list = [(str(hostname_dir)).replace(str(audit_docs), "").replace("/","") for hostname_dir in audit_docs.iterdir()]

    for host in host_list:
        inv_dict[host] = {}
        inv_dict[host]["groups"] = ["ios_devices"]
        inv_dict[host]["hostname"] = host

    ### CREATE INVENTORY FILE ###
    yaml_inv = dump(inv_dict, default_flow_style=False)
    with open(INV_PATH_FILE, "w+") as open_file:
        open_file.write("\n" + yaml_inv)
