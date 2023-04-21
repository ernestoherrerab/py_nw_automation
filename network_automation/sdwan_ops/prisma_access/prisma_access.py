#! /usr/bin/env python
"""
Script to Create Prisma Access Remote Networks
"""

from decouple import config
from yaml import dump
import logging
from pathlib import Path
from time import sleep
import urllib3
import network_automation.prisma_api as prisma


### LOGGING SETUP ###
LOG_FILE = Path("logs/sdwan_ops.log")
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler(LOG_FILE)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

def create_remote_networks(site_data: dict, hostname_ip_set: set, remote_nw_subnets: list, tunnel_ips: list) -> list:
    """ Main function to provision tunnels 
    
    Args:
    site_data (dict): From frontend input
    hostname_ip_set (set): Contains Public IPs to create IKE Gateways
    remote_nw_subnets (list): Networks to be configured on the Prisma Access Remote Network

    Returns:
    public_ip (list): Contains the public IP address to use as destination on SDWAN IPSec Tunnels
    """
    
    ### DISABLE CERTIFICATE WARNINGS ###
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    ### VARIABLES ###
    PRISMA_API_KEY = config("PRISMA_API_KEY")
    PANAPI_CONFIG_PATH = Path("network_automation/sdwan_ops/prisma_access/config.yml")
    PRISMA_CLIENT_ID = config("PRISMA_CLIENT_ID")
    PRISMA_CLIENT_SECRET = config("PRISMA_CLIENT_SECRET")
    PRISMA_CLIENT_SCOPE = config("PRISMA_CLIENT_SCOPE")
    PRISMA_TOKEN_URL = "https://auth.apps.paloaltonetworks.com/oauth2/access_token"
    site_code = site_data["site_code"].upper()
    region = site_data["region_id"]
    location = site_data["location_id"]

    ### CREATE PANAPI AUTH INPUT DATA ###

    auth_input = {
        "client_id" : PRISMA_CLIENT_ID,
        "client_secret" : PRISMA_CLIENT_SECRET,
        "scope": PRISMA_CLIENT_SCOPE,
        "token_url": PRISMA_TOKEN_URL
    }
    with open(PANAPI_CONFIG_PATH, "w+") as f:
        dump(auth_input, f)
    
    ### GENERATE PRISMA SESSION ###
    print("Authenticating to Prisma...")
    prisma_session = prisma.auth(PANAPI_CONFIG_PATH)
    logger.info("Prisma: Authenticated")

    ### CHECK IF REMOTE NETWORK ALREADY EXISTS ###
    print("Checking if the remote network already exists in Prisma...")
    remote_network = prisma.get_remote_nws(prisma_session, site_code)
    logger.info(f'Prisma: Checking if {site_code} remote network exists')
    if remote_network != None:
        print(remote_network)
        logger.error(f'Prisma: Remote Network {site_code} already exists')
        return False
    else:
        print(f'Remote Network {site_code} does not exist')
        logger.info(f'Prisma: Remote Network {site_code} does not exist')

    ### RETRIEVE SPN VALUE BASED ON THE REGION INPUT ###
    print(f'Getting SPN Location based on region entered: {region} ...')
    spn_location_dict = prisma.get_spn_location(prisma_session, region)
    if spn_location_dict == None:
        print("SPN Location not found, check region input is correct...")
        logger.error(f'Prisma: SPN Location for {location} not found')
        return False
    else:
        spn_location = spn_location_dict["spn_name_list"][0]
        print(spn_location)
        logger.info(f'Prisma: Retrieved SPN Location from {region}: {spn_location}')

    ### RETRIEVE REGION NAME BASED ON LOCATION INPUT ###
    print(f'Getting Region Name based on location entered: {location}')
    regions = prisma.get_region(prisma_session)
    region_id = [region["value"] for region in regions if region["display"] == location]
    region_id = region_id[0]
    logger.info(f'Prisma: Retrieved Region ID from {location}: {region_id}')

    ### CREATE IKE GATEWAY(S) ###
    print("Creating IKE Gateways in Prisma...")
    ike_gw_result, ike_gw_names = prisma.create_ike_gw(prisma_session, hostname_ip_set)
    if ike_gw_result != {201}:
        logger.error(f'Prisma: Could not create IKE Gateways')
        return False
    else:
        print("IKE Gateways Successfully Created!")
        logger.info(f'Prisma: IKE Gateways Successfully Created: {ike_gw_names}')

    ### CREATE IPSEC TUNNEL(S) ###
    print("Creating IPSEC Tunnels in Prisma...")
    ipsec_tun_result, ipsec_tun_names = prisma.create_ipsec_tunnel(prisma_session, ike_gw_names)
    if ipsec_tun_result != {201}:
        ### ROLL BACK IKE GATEWAYS IF IPSEC TUNNELS FAIL ###
        print("IPSec Tunnels could not be created...")
        logger.error(f'Prisma: Could not create IPSec Tunnels ')
        print("Rolling back...")
        rollback_response = prisma.rollback(prisma_session)
        logger.error(f'Prisma: Rollback activated response: {rollback_response["message"]}')
        return False
    else:
        logger.info(f'Prisma: IPSec Tunnels {ipsec_tun_names} Successfully Created')
        print("IPSec Tunnels Successfully Created!")

    ### CREATE ADDRESS OBJECTS ###
    print("Creating address objects...")
    addr_obj_response, addr_obj_list = prisma.create_address(prisma_session, site_code, remote_nw_subnets)
    if addr_obj_response != {201}:
        logger.error(f'Prisma: Could not create Address Objects')
    else:
        print("Address Objects Successfully Created!")
        logger.info(f'Prisma: Address Objects: {addr_obj_list}')

    ### CREATE ADDRESS GROUPS ###
    print("Creating address groups...")
    addr_group_obj_response, addr_group_obj_name = prisma.create_address_group(prisma_session, site_code, addr_obj_list)
    if addr_group_obj_response != {201}:
        logger.error(f'Prisma: Could not create Address Group Objects')
        return False
    else:
        print("Address Objects Groups Successfully Created!")
        logger.info(f'Prisma: Address Group Objects: { addr_group_obj_name}')

    ##### CREATE REMOTE NETWORK ###
    print("Creating remote network...")
    remote_network_result, peer_asn, bgp_peers = prisma.create_remote_nw(prisma_session, site_code, spn_location, ipsec_tun_names, region_id, tunnel_ips)
    
    
    ### ROLL BACK IF PROCESS FAILS ###
    if remote_network_result != 201:
        print("Remote Network could not be created...")
        logger.error(f'Prisma: Remote Network {site_code} could not be created')
        rollback_response = prisma.rollback(prisma_session)
        logger.error(f'Prisma: Rollback activated response: {rollback_response["message"]}')
        return False
    else:
        print("Remote Network Successfully Created!")
        logger.info(f'Prisma: Remote Network {site_code} Successfully Created!')
        
        ### PUSH CONFIG ###
        prisma.push_config(prisma_session)
        
        ### GET PUBLIC IP FOR SDWAN TUNNEL DESTINATION ###
        public_ip = []
        while public_ip == []:
            public_ips = prisma.get_public_ip(PRISMA_API_KEY)
            public_ip = [ip["address"] for item in public_ips for ip in item["address_details"] if ip["addressType"] == "service_ip" and site_code in ip["node_name"] ]
            sleep(20)
        print(public_ip)
        logger.info(f'Prisma: The public IP is {public_ip}')
        
        return public_ip, peer_asn, bgp_peers