#! /usr/bin/env python
"""
Script to add DHCP Scopes To Infoblox
"""
import logging
from pathlib import Path

### LOGGING SETUP ###
LOG_FILE = Path("logs/infoblox_ops.log")
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler(LOG_FILE)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

def is_subnet_of_any(subnet, network_list):
    for network in network_list:
        if subnet.network in network:
            return True
    return False

def container_check(nws, container_parent_nws): 
    for nw in nws:
        if is_subnet_of_any(nw, container_parent_nws):
            print(f"{nw} is part of a larger network.")
        else:
            error_str = f"A container for {nw} needs to be created first!!!"
            logger.error(f'Infoblox: {nw} is not part of any larger network.')
            return False, error_str