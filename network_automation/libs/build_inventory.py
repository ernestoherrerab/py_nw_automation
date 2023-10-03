#! /usr/bin/env python
"""
Build Nornir Inventory From IPFabric Data
"""
import logging
from pathlib import Path
from yaml import dump
import network_automation.libs.ipfabric_api as ipfabric

### LOGGING SETUP ###
LOG_FILE = Path("logs/standards_ops.log")
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler(LOG_FILE)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


def build_inventory(site_code: str):
    """Build the inventory 

    Args:
    site_code (str) : From user input
    username (str) : From user input
    password (str) : From user input
    """
    ### VARS ###
    INV_DIR = Path("network_automation/standards_ops/inventory/hosts.yml")
    site_code = site_code.lower()
    site_filter = {"hostname": ["like", site_code + "-"]}
    nornir_inv_dict = {}

    ### GENERATE IPFABRIC SESSION ###
    print("Authenticating to IPFabric...")
    ipf_session = ipfabric.auth()
    logger.info("IPFabric: Authenticated")
    ipf_inv = ipfabric.get_inv_data(ipf_session, site_filter)
    logger.info(f'IPFabric: Got Site Inventory for: {site_code}')
    
    for data in ipf_inv:
        if "sdw" in data["hostname"]:
            nornir_inv_dict[data["hostname"]] = {"groups": ["sdwan_routers"], "hostname": data["loginIp"]}
        elif data["devType"] == "wlc":
            nornir_inv_dict[data["hostname"]] = {"groups": ["wireless_controllers"], "hostname": data["loginIp"]}
        elif data["devType"] == "ap":
            nornir_inv_dict[data["hostname"]] = {"groups": ["access_points"], "hostname": data["loginIp"]}
        elif data["devType"] == "fw":
            nornir_inv_dict[data["hostname"]] = {"groups": ["firewalls"], "hostname": data["loginIp"]}
        elif data["family"] == "nx-os":
            nornir_inv_dict[data["hostname"]] = {"groups": ["nxos_devices"], "hostname": data["loginIp"]}
        else:
            nornir_inv_dict[data["hostname"]] = {"groups": ["ios_devices"], "hostname": data["loginIp"]}
    
    ### DUMP INVENTORY DICTIONARY ###
    with open(INV_DIR, "w+") as open_file:
        open_file.write("\n" + dump(nornir_inv_dict, default_flow_style=False))
    
    return ipf_inv