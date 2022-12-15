#! /usr/bin/env python
"""
Apply AAA standard configurations
"""
import logging
from pathlib import Path
from yaml import dump, load
from yaml.loader import FullLoader
import network_automation.standards_ops.audit_inv as build_inv
import network_automation.standards_ops.aaa.configure_aaa as aaa
import network_automation.standards_ops.nornir_commands as nornir

### LOGGING SETUP ###
LOG_FILE = Path("logs/standards_ops.log")
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler(LOG_FILE)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

def build_inventory(site_code: str, username: str, password: str):
    """Apply AAA standard configurations

    Args:
    site_code (str) : From user input
    username (str) : From user input
    password (str) : From user input
    """
    ### VARS ###
    INV_DIR = Path("network_automation/standards_ops/inventory/hosts.yml")
    
    ### BUILD THE SITE INVENTORY ###
    build_inv.build_audit_inv(site_code)
    logger.info(f'Nornir: Build inventory file for {site_code}')

    ### LOAD INVENTORY AS DICT ###
    with open(INV_DIR) as f:
        inv_dict = load(f, Loader=FullLoader)

     ### GET THE VERSION OUTPUT ###
    results = nornir.init_nornir(username, password, nornir.get_version_task)
    logger.info(f'Nornir: Retrieved "show version" output')
    for key, value in results.items():
        if "chassis" in value["version"] and ("WS-C2960S" in value["version"]["chassis"] or "WS-C2960" in value["version"]["chassis"] or "WS-C2960S" in value["version"]["chassis"] or "WS-C2960G" in value["version"]["chassis"] or "WS-C2960C" in value["version"]["chassis"]):
            inv_dict[key]["groups"].append("ws_c2960s")
        elif "chassis" in value["version"] and ("WS-C3560X" in value["version"]["chassis"] or "WS-C3560CG" in value["version"]["chassis"] or "WS-C3560G" in value["version"]["chassis"] ):
            inv_dict[key]["groups"].append("ws_c3560x")
        elif "chassis" in value["version"] and "WS-C3560CX" in value["version"]["chassis"]:
            inv_dict[key]["groups"].append("ws_c3560cx")
        elif "chassis" in value["version"] and ("WS-C2960X" in value["version"]["chassis"] or "WS-C2960CX" in value["version"]["chassis"] or "WS-C2960L" in value["version"]["chassis"] or "WS-C2960CPD" in value["version"]["chassis"]):
            inv_dict[key]["groups"].append("ws_c2960x")
        elif "chassis" in value["version"] and ("WS-C3750G" in value["version"]["chassis"] or "WS-C3750X" in value["version"]["chassis"]):
            inv_dict[key]["groups"].append("ws_c3750g")
        elif "chassis" in value["version"] and ("C9200" in value["version"]["chassis"] or "C9300" in value["version"]["chassis"] or "C9410R" in value["version"]["chassis"] or "C9407R" in value["version"]["chassis"] or "C9500" in value["version"]["chassis"]):
            inv_dict[key]["groups"].append("c9200")
        elif "chassis" in value["version"] and ("WS-C4510R" in value["version"]["chassis"] or "WS-C4506-E" in value["version"]["chassis"]):
            inv_dict[key]["groups"].append("ws_c4510r")
        elif "chassis" in value["version"] and "WS-C3650" in value["version"]["chassis"]:
            inv_dict[key]["groups"].append("ws_c3650")
    
    ### DUMP INVENTORY DICTIONARY ###
    with open(INV_DIR, "w+") as open_file:
        open_file.write("\n" + dump(inv_dict, default_flow_style=False))

    ### BUILD CONFIGURATION FILE ###
    result, failed_hosts = aaa.replace_aaa(username, password, site_code)

    return result, failed_hosts