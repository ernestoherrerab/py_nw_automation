#! /usr/bin/env python
"""
Script to Provision IPSec Tunnel IPs
"""
from decouple import config
from json import dumps
import logging
from pathlib import Path
import network_automation.sdwan_ops.api_calls as infoblox


### LOGGING SETUP ###
LOG_FILE = Path("logs/tunnel_provision.log")
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler(LOG_FILE)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

def create_tunnel_ips():
    """Provision SDWAN Tunnels IPs

    """
    ### VARS ###
    INFOBLOX_URL = config("INFOBLOX_URL")
    INFOBLOX_AUTHENTICATION = config("INFOBLOX_AUTHENTICATION")
    TUNNEL_NETWORK = config("INFOBLOX_TUNNEL_NETWORK")
    payload = {
                  "network": {
                    "_object_function": "next_available_network",
                    "_parameters": {
                      "cidr": 30
                    },
                    "_result_field": "networks",
                    "_object": "networkcontainer",
                    "_object_parameters": {
                      "network": TUNNEL_NETWORK
                    }
                  }
                }

    headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Basic {INFOBLOX_AUTHENTICATION}'
            }
    ### POST API CALL TO CREATE NEXT AVAILABLE /30 NETWORK ###
    response = infoblox.post_operations("network", INFOBLOX_URL, payload=payload, headers=headers)
    logger.info(f'Infoblox: Subnet Created {response}')
    
    return response