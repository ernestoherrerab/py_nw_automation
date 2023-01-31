#! /usr/bin/env python
"""
Apply AAA standard configurations
"""
import logging
from pathlib import Path
from yaml import dump
from yaml.loader import FullLoader
import network_automation.standards_ops.ipfabric_api as ipfabric
import network_automation.standards_ops.infoblox_helper.add_ib_helper as ib_helper

### LOGGING SETUP ###
LOG_FILE = Path("logs/standards_ops.log")
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler(LOG_FILE)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

def format_dhcp_relay_data(dhcp_data):
    """
    Format DHCP relay data 

    Args:
    data (dict) : IPFabric Data Input

    Returns:
    dhcp_data (dict) : DHCP data formatted
    """
    ### VARS ###
    dhcp_dict = {}

    for data in dhcp_data:
        if data["hostname"] not in dhcp_dict:
            dhcp_dict[data["hostname"]] = []
            dhcp_dict[data["hostname"]].append(data["intName"])
        elif data["hostname"] in dhcp_dict and data["intName"] not in dhcp_dict[data["hostname"]]:
            dhcp_dict[data["hostname"]].append(data["intName"])

    return dhcp_dict

def format_inv_filter(input):
    """
    Format devices management filter for IPFabric

    Args:
    input (dict): From DHCP Relay Data

    Returns:
    inv_data (dict) : To be used as inventory for Nornir
    """


def build_inventory(site_code: str, username: str, password: str):
    """Build the inventory 

    Args:
    site_code (str) : From user input
    username (str) : From user input
    password (str) : From user input
    """
    ### VARS ###
    INV_DIR = Path("network_automation/standards_ops/inventory/hosts.yml")
    site_code = site_code.lower()
    dhcp_relay_filter = {"hostname": ["like", site_code]}
    mgmt_filter = {"or": []}
    nornir_inv_dict = {}

    ### GENERATE IPFABRIC SESSION ###
    print("Authenticating to IPFabric...")
    ipf_session = ipfabric.auth()
    logger.info("IPFabric: Authenticated")
    
    ### GET DHCP RELAY INTERFACES ###
    dhcp_dev_ifs = ipfabric.get_dhcp_relay_ifs(ipf_session, dhcp_relay_filter)
    logger.info(f'IPFabric: Got Interfaces Used for DHCP Relay {site_code}')
    dhcp_data = format_dhcp_relay_data(dhcp_dev_ifs)
    logger.info(f'Format DHCP Relay data from IPFabric')

    ### GET MANAGEMENT IPS FOR NORNIR INVENTORY ###
    ### CREATE FILTER ###
    for host in list(dhcp_data.keys()):
        mgmt_filter["or"].append({"hostname": ["eq", host]})

    ### APPLY FILTER TO INVENTORY SEARCH ###
    inv_data = ipfabric.get_mgmt_ips(ipf_session, mgmt_filter)

    for data in inv_data:
        if "sdw" not in data["hostname"]:
            nornir_inv_dict[data["hostname"]] = {"groups": ["ios_devices"], "hostname": data["loginIp"]}
        elif "sdw" in data["hostname"]:
            nornir_inv_dict[data["hostname"]] = {"groups": ["sdwan_routers"], "hostname": data["loginIp"]}

 
    ### DUMP INVENTORY DICTIONARY ###
    with open(INV_DIR, "w+") as open_file:
        open_file.write("\n" + dump(nornir_inv_dict, default_flow_style=False))

    ### BUILD CONFIGURATION FILE ###
    result, failed_hosts = ib_helper.add_helper(username, password, dhcp_data)

    return result, failed_hosts