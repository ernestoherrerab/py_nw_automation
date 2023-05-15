#! /usr/bin/env python
"""
Script to add DHCP Scopes To Infoblox
"""
import csv
from decouple import config
import logging
from netaddr import IPNetwork
from pathlib import Path
import urllib3
from network_automation.InfobloxApi import Infoblox
from network_automation.infoblox_ops import containers as container

### LOGGING SETUP ###
LOG_FILE = Path("logs/infoblox_ops.log")
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler(LOG_FILE)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


def csv_to_dict(filename: str) -> dict:
    """
    Function to Convert CSV Data to YAML
    """
    with open(filename) as f:
        csv_data = csv.DictReader(f)
        data = [row for row in csv_data]
    return data

def add_scope(filename) -> list:
    """Provision SDWAN Tunnels IPs

    Args:
    num_nws (list): Number of required networks
    site_data (dict): Frontend input data

    Returns 
    tunnel_ips_list (list): List of IP addresses to use for the SDWAN tunnels
    """
    ### DISABLE WARNINGS ###
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    ### VARS ###
    INFOBLOX_URL = config("INFOBLOX_URL")
    INFOBLOX_AUTHENTICATION = config("INFOBLOX_AUTHENTICATION")
    INFOBLOX_CPH_DHCP = config("INFOBLOX_CPH_DHCP")
    INFOBLOX_MAA_DHCP = config("INFOBLOX_MAA_DHCP")
    INFOBLOX_SLC_DHCP = config("INFOBLOX_SLC_DHCP")
    post_results = set()
    
    ### TRANSFORM CSV DATA TO DICT ###
    scope_data = csv_to_dict(filename)
    
    ### INITIALIZE API OBJECT ###
    ib = Infoblox(INFOBLOX_AUTHENTICATION)

    ### CHECK FOR PARENT NETWORKS IN CONTAINERS ###
    main_container_params = {"network_container": "10.0.0.0/8", "_return_as_object": "1"}
    containers = ib.get_operations("networkcontainer", INFOBLOX_URL, main_container_params) 
    container_parent_nws = [IPNetwork(nw["network"]) for nw in containers["result"]]
    nws = [IPNetwork(nw["Network"]) for nw in scope_data]
    print(scope_data)

    container_check = container.container_check(nws, container_parent_nws)

    if container_check is None:
        ### CREATE NETWORK WITH MEMBERS ###
        new_nw_params = {"_return_fields": "network,members", "_return_as_object": "1"}
        nw_payload_list = list(map(lambda x: {"network": x["Network"], "comment": x["Comment"], "options": [{"name": "routers", "num": 3, "use_option": True, "value": x["Default_Gateway"], "vendor_class": "DHCP"}], "members": [{"_struct": "dhcpmember","ipv4addr": INFOBLOX_CPH_DHCP}, {"_struct": "dhcpmember","ipv4addr": INFOBLOX_MAA_DHCP}, {"_struct": "dhcpmember","ipv4addr":INFOBLOX_SLC_DHCP}]}, scope_data))

        print("Adding Networks to IPAM")
        for nw_payload in nw_payload_list:
            new_nw = ib.post_operations("network", INFOBLOX_URL, nw_payload, params=new_nw_params)
            post_results.add(new_nw)
            logger.info(f'Infoblox: The result of adding a new network was {new_nw}')
            print(f'Infoblox: The result of adding a new network was {new_nw}')

        ### CREATE DHCP SCOPES ###
        new_dhcp_params = {"_return_fields": "start_addr,end_addr", "_return_as_object": "1"}
        range_payload_list = list(map(lambda x: {"start_addr": x["Range"].split('-')[0], "end_addr": x["Range"].split('-')[1]}, scope_data))
        
        print("Adding Ranges to IPAM")
        for range_payload in range_payload_list:
            new_range = ib.post_operations("range", INFOBLOX_URL, range_payload, params=new_dhcp_params)
            post_results.add(new_range)
            logger.info(f'Infoblox: The result of adding a new dhcp range was {new_range}')
            print(f'Infoblox: The result of adding a new dhcp range was {new_range}')
        
        if post_results == {201}:
            return True, post_results
        else:
            return False, post_results
    
    elif False in container_check and container_check is not None:
        return False, container_check[1]    