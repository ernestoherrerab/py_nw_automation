#! /usr/bin/env python
"""
Script to Provision IPSec Tunnel IPs
"""
from decouple import config
import logging
from pathlib import Path
import re
import os
import sys
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
from netaddr import IPNetwork
from libs.InfobloxApi import Infoblox

### LOGGING SETUP ###
LOG_FILE = Path("logs/sdwan_ops.log")
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler(LOG_FILE)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

def create_tunnel_ips(num_nws: list, site_data: dict) -> list:
    """Provision SDWAN Tunnels IPs

    Args:
    num_nws (list): Number of required networks
    site_data (dict): Frontend input data

    Returns 
    tunnel_ips_list (list): List of IP addresses to use for the SDWAN tunnels
    """
    ### VARS ###
    INFOBLOX_URL = config("INFOBLOX_URL")
    INFOBLOX_AUTHENTICATION = config("INFOBLOX_AUTHENTICATION")
    TUNNEL_NETWORK = config("INFOBLOX_TUNNEL_NETWORK")
    site_code = site_data["site_code"].lower()
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
    iterations = len(num_nws)  
    
    ### POST API CALL TO CREATE NEXT AVAILABLE /30 NETWORK ###
    print("Creating networks in Infoblox...")
    response_list = []
    counter = 1
    infoblox_network = Infoblox(INFOBLOX_AUTHENTICATION)
  
    while counter <= iterations:
      response, _ = infoblox_network.post_operations("network", INFOBLOX_URL, payload=payload)
      print(response)
      response_list.append(response)
      logger.info(f'Infoblox: Subnet Created {response}')
      counter += counter

    ### ADD SITE ID TO COMMENTS ###
    print("Documenting Site Code in Infoblox...")
    print(response_list)
    for network in response_list:
      payload = {"comment": site_code.upper()}
      response = infoblox_network.put_operations(network, INFOBLOX_URL, payload=payload)
      logger.info(f'Infoblox: Subnet Edited {response}')
    
    ### GET SUBNETS FOR TUNNELS ###
    print("Getting Tunnel IP...")
    tunnel_subnet_list = []
    for subnet in response_list:
      tunnel_subnet = re.findall(r'network\/\w+:(\S+)\/default', subnet)
      tunnel_subnet_list.append(tunnel_subnet[0])
      logger.info(f'Infoblox: Tunnel subnets {tunnel_subnet[0]}')

    ### GET TUNNEL IPS FOR TUNNELS ###
    tunnel_ips_list = []
    for tunnel_ip in tunnel_subnet_list:
      network = IPNetwork(tunnel_ip)
      tunnel_ip_list = list(network)
      tunnel_ips_list.append(str(tunnel_ip_list[1]))
      logger.info(f'Infoblox: Tunnel IP {tunnel_ip_list[1]}')
      
    return tunnel_ips_list