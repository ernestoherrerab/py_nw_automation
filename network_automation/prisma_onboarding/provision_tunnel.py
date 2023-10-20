#! /usr/bin/env python
"""
Script to Provision Prisma Access Tunnels
"""
from getpass import getpass
import logging
from pathlib import Path
import urllib3
import infoblox_ops
import ipfabric_ops
import prisma_access_ops
import sdwan_ops


### LOGGING SETUP ###
LOG_FILE = Path("logs/sdwan_ops.log")
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler(LOG_FILE)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

def main():
    """ Main function to provision tunnels """
    
    ### DISABLE CERTIFICATE WARNINGS ###
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    ### VARS ###
    site_data = {}


    print(
        '''Welcome to the Prisma Access Onboarding Tool\n\n
        * The compute location and Prisma Access location can be found in:
          Prisma Access -> Service Setup -> Remote Networks -> Bandwidth Management\n
        ** The locations must be exactly entered as displayed
        *** BANDWIDTH MUST HAVE BEEN ALLOCATED TO THE REGION ALREADY\n
        '''
    )
    username = input("vManage Username: ")
    password = getpass("vManage Password: ")
    site_code = input("Site code: ")
    region_id = input("Compute Location: ")
    location_id = input("Prisma Access Location: ")
    site_data["site_code"] = site_code.lower()
    site_data["region_id"] = region_id
    site_data["location_id"] = location_id

    ### GET SDWAN IPSEC FEATURE TEMPLATE VALUES ###
    ### GET SUBNETS FOR REMOTE NETWORKS IN PRISMA ACCESS ###
    hostname_ip_set, remote_nw_subnets = ipfabric_ops.get_ipfabric_data(site_data)
    print(f'IPFabric Ops Result: {hostname_ip_set}, {remote_nw_subnets}\n')
    
    ### PROVISION TUNNEL INTERFACES IN INFOBLOX ###
    infoblox_response = infoblox_ops.create_tunnel_ips(hostname_ip_set, site_data)
    print(f'Infoblox Ops Result: {infoblox_response}\n')

    ### CREATE REMOTE NETWORKS IN PRISMA ACCESS ###
    ### GET PUBLIC IP FOR SDWAN TUNNEL DESTINATION ###
    public_ip, bgp_asn, bgp_peers = prisma_access_ops.create_remote_networks(site_data, hostname_ip_set, remote_nw_subnets, infoblox_response)
    print(f'Prisma Access Ops Result: {public_ip}, {bgp_asn}, {bgp_peers}\n')

    ### CREATE IPSEC TUNNELS ON SDWAN VMANAGE ###
    summary_list = sdwan_ops.create_ipsec_tunnels(site_data, username, password, hostname_ip_set, public_ip, bgp_asn, bgp_peers, infoblox_response)
    print(f'SDWAN Ops Result: {summary_list} \n')

    summary_list = sdwan_ops.create_ipsec_tunnels(site_data, username, password, hostname_ip_set, public_ip, bgp_asn, bgp_peers, infoblox_response)
    print(f'SDWAN Ops Result: {summary_list} \n')

if __name__ == '__main__' :
    """
    The main execution block of the script.

    This block is executed only if the script is run directly (not imported as a module).
    It calls the main() function to start the process of retrieving and processing MAC address information from ISE.
    """
    main()