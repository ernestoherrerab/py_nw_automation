#! /usr/bin/env python
"""
Apply NTP standard configurations
"""
import logging
from pathlib import Path
import network_automation.standards_ops.audit_inv as build_inv
import network_automation.standards_ops.ntp.configure_ntp as ntp

### LOGGING SETUP ###
LOG_FILE = Path("logs/standards_ops.log")
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler(LOG_FILE)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

def build_inventory(ntp_dict: dict, username: str, password: str):
    """Apply NTP standard configurations

    Args:
    ntp_dict (dict) : From user input
    username (str) : From user input
    password (str) : From user input
    """
    ### VARS ###
    INV_DIR = Path("network_automation/standards_ops/inventory/hosts.yml")
    site_code = ntp_dict["site_code"]
    ### BUILD THE SITE INVENTORY ###
    build_inv.build_audit_inv(site_code)
    logger.info(f'Nornir: Build inventory file for {site_code}')

    ### BUILD CONFIGURATION FILE ###
    result, failed_hosts = ntp.replace_ntp(username, password, ntp_dict)

    return result, failed_hosts