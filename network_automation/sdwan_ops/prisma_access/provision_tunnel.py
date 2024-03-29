#! /usr/bin/env python
"""
Script to Provision Prisma Access Tunnels
"""
import logging
from pathlib import Path
import urllib3
import network_automation.sdwan_ops.prisma_access.infoblox as infoblox
import network_automation.sdwan_ops.prisma_access.ipfabric as ipfabric
import network_automation.sdwan_ops.prisma_access.prisma_access as prisma
import network_automation.sdwan_ops.prisma_access.sdwan as sdwan

### LOGGING SETUP ###
LOG_FILE = Path("logs/sdwan_ops.log")
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler(LOG_FILE)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

def provision_tunnel(site_data, username, password):
    """ Main function to provision tunnels """
    
    ### DISABLE CERTIFICATE WARNINGS ###
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    ### GET SDWAN IPSEC FEATURE TEMPLATE VALUES ###
    ### GET SUBNETS FOR REMOTE NETWORKS IN PRISMA ACCESS ###
    hostname_ip_set, remote_nw_subnets = ipfabric.get_ipfabric_data(site_data)
    print(f'IPFabric Ops Result: {hostname_ip_set}, {remote_nw_subnets}\n')
    logger.info(f'IPFabric Ops Result: {hostname_ip_set}, {remote_nw_subnets}\n')
    
    ### PROVISION TUNNEL INTERFACES IN INFOBLOX ###
    infoblox_response = infoblox.create_tunnel_ips(hostname_ip_set, site_data)
    print(f'Infoblox Ops Result: {infoblox_response}\n')
    logger.info(f'Infoblox Ops Result: {infoblox_response}\n')
    
    ### CREATE REMOTE NETWORKS IN PRISMA ACCESS ###
    ### GET PUBLIC IP FOR SDWAN TUNNEL DESTINATION ###
    public_ip, bgp_asn, bgp_peers = prisma.create_remote_networks(site_data, hostname_ip_set, remote_nw_subnets, infoblox_response)
    logger.info(f'Prisma Access Ops Result: {public_ip}, {bgp_asn}, {bgp_peers}\n')
    print(f'Prisma Access Ops Result: {public_ip}, {bgp_asn}, {bgp_peers}\n')
    
    ### CREATE IPSEC TUNNELS ON SDWAN VMANAGE ###
    summary_list = sdwan.create_ipsec_tunnels(site_data, username, password, hostname_ip_set, public_ip, bgp_asn, bgp_peers, infoblox_response)
    logger.info(f'SDWAN Ops Result: {summary_list} \n')
    print(f'SDWAN Ops Result: {summary_list} \n')

    return summary_list