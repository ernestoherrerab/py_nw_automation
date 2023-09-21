#! /usr/bin/env python
"""
Script to Retrieve IP Fabric to Provision Prisma Access Tunnels
"""

import logging
from pathlib import Path
import urllib3
from netaddr import IPAddress, cidr_merge
import network_automation.libs.ipfabric_api as ipfabric

### LOGGING SETUP ###
LOG_FILE = Path("logs/sdwan_ops.log")
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler(LOG_FILE)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

def get_ipfabric_data(site_data: dict) -> tuple:    
    """"Retrieval of needed data to provision tunnels
    
    Args:
    site_data (dict): From frontend input

    Returns: 
    hostname_ip_set, remote_nw_subnets (set, list): 
    Contains data to fill in the variable values for SDWAN IPSec tunnels
    and the networks to be configured on the Prisma Access Remote Network    
    """

    ### DISABLE CERTIFICATE WARNINGS ###
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    ### VARIABLES ###
    site_code = site_data["site_code"].upper()

    ### GENERATE IPFABRIC SESSION ###
    print("Authenticating to IPFabric...")
    ipf_session = ipfabric.auth()
    #ipf_session = ipfabric.auth()
    logger.info("IPFabric: Authenticated")

    ### RETRIEVE INTERFACE DATA FROM DEVICE FROM IPFABRIC ###
    ### SEARCHES FOR ALL INTERFACES BELONGING TO SDW ROUTERS STARTING WITH SITE CODE VAR ###
    print("Getting Public Interface Data of Site Routers...")
    if_filter_input = {"and": [{"hostname": ["reg",f'{site_code.lower()}-r\\d+-sdw']}]}
    dev_data = ipfabric.get_if_data(ipf_session, if_filter_input)
    logger.info("IPFabric: Retrieved Interface Data from router")

    ### GET PUBLIC IPS FROM INTERFACE RETRIEVED IPFABRIC DATA ###
    ### FILTERS ALL INTERFACES WITH AN IP CONFIGURED AND SEARCHES FOR PUBLIC IPS ###
    print("Getting public IP data...")
    hostname_ip_set= set()

    tunnel_ip = [False]
    for interface in dev_data:
        if interface["primaryIp"] != None:
            ip =  IPAddress(interface["primaryIp"])
            if ip.is_unicast() and not ip.is_private() and "Tunnel" not in interface["nameOriginal"] and interface["l1"] == "up":
                hostname_ip_set.add((interface["hostname"], interface["primaryIp"], interface["nameOriginal"]))
            elif interface["intName"] == "Tunnel0":
                tunnel_ip = [interface["hostname"], interface["primaryIp"], True]
    
    ### GET WAN INTERFACE WITH PUBLIC IP IF IT EXISTS ###
    if True in tunnel_ip:
        key = "primaryIp" 
        ip_add = tunnel_ip[1]
        ### SEARCH FOR THE INTERFACE NAME THAT SHARES THE SAME IP AS TUNNEL0 FROM THE IPFABRIC IF DATA ###
        dict_item = next(filter(lambda dict_item: dict_item.get(key) == ip_add if ( dict_item["intName"] != "Tunnel0") else None, dev_data), None)
        tunnel_ip[2] = dict_item["intName"]
        hostname_ip_set.add(tuple(tunnel_ip))

    ### GET CONNECTED AND STATIC ROUTES FROM SDW ROUTERS FROM IP FABRIC ###
    print("Getting Networks Data of Site Routers...")
    subnets_filter_input = {"and": [{"hostname": ["reg",f'{site_code.lower()}-r\\d+-sdw']},{"vrf": ["eq","10"]},{"protocol": ["reg","S|C"]}]}
    routes = ipfabric.get_subnets_data(ipf_session, subnets_filter_input)
    logger.info("IPFabric: Retrieved Static/Connected routes of SDWAN Routers")
    

    ### SUMMARIZE NETWORKS OBTAINED BY IPFABRIC ROUTES USING THE NETADDR LIBRARY ###
    subnets = []
    for subnet in routes:
        subnets.append(subnet["network"])
    summary_subnets = cidr_merge(subnets)   
    remote_nw_subnets = [str(subnet) for subnet in summary_subnets]
    logger.info("IPFabric: Summarized Static/Connected routes of SDWAN Routers")
    
    return hostname_ip_set, remote_nw_subnets
