#! /usr/bin/env python
"""
Script to Provision Prisma Access Tunnels
"""

import logging
from pathlib import Path
from netaddr import IPAddress, cidr_merge
import network_automation.sdwan_ops.ipfabric_api as ipfabric
import network_automation.sdwan_ops.prisma_api as prisma
import network_automation.sdwan_ops.sdwan_api as sdwan

### LOGGING SETUP ###
LOG_FILE = Path("logs/tunnel_provision.log")
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler(LOG_FILE)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.info("Begin tunnel provisioning")

def provision_tunnel(config, site_data, url_var, username, password):
    """ Main function to provision tunnels """

    ### VARIABLES ###
    site_id = site_data["site_id"].upper()
    location = site_data["location_id"]
    hostname_ip_list = set()
    subnets = []
    ike_gws_del = []
    ipsec_tuns_del = []

    ### GENERATE IPFABRIC SESSION ###
    print("Authenticating to IPFabric...")
    ipf_session = ipfabric.auth()
    logger.info("IPFabric: Authenticated")

    ### RETRIEVE INTERFACE DATA FROM DEVICE ###
    print("Getting Public Interface Data of Site Routers...")
    if_filter_input = {"and": [{"hostname": ["reg",f'{site_id.lower()}-r\\d+-sdw']}]}
    dev_data = ipfabric.get_if_data(ipf_session, if_filter_input)
    logger.info("IPFabric: Retrieved Interface Data from router")
    
    ### GET PUBLIC IPS FROM IPFABRIC DATA ###
    for interface in dev_data:
        if interface["primaryIp"] != None:
            ip =  IPAddress(interface["primaryIp"])
            if ip.is_unicast() and not ip.is_private():
                hostname_ip_list.add((interface["hostname"], interface["primaryIp"]))
    logger.info("IPFabric: Retrieved Public IPs from routers")

    ### GET SUBNET FROM IP FABRIC ###
    print("Getting Networks Data of Site Routers...")
    subnets_filter_input = {"and": [{"hostname": ["reg",f'{site_id.lower()}-r\\d+-sdw']},{"vrf": ["eq","10"]},{"protocol": ["reg","S|C"]}]}
    routes = ipfabric.get_subnets_data(ipf_session, subnets_filter_input)
    logger.info("IPFabric: Retrieved Static/Connected routes of SDWAN Routers")

    ### SUMMARIZE NETWORKS ###
    for subnet in routes:
        subnets.append(subnet["network"])
    summary_subnets = cidr_merge(subnets)   
    remote_nw_subnets = [str(subnet) for subnet in summary_subnets]
    logger.info("IPFabric: Summarized Static/Connected routes of SDWAN Routers")
    
    ### GENERATE PRISMA SESSION ###
    print("Authenticating to Prisma...")
    prisma_session = prisma.auth(config)
    logger.info("Prisma: Authenticated")

    ### CHECK IF Remote Network ALREADY EXISTS ###
    print("Checking if the remote network already exists in Prisma...")
    remote_network = prisma.get_remote_nws(prisma_session, site_id)
    logger.info(f'Prisma: Checking if {site_id} remote network exists')

    if remote_network != None:
        print(remote_network)
        logger.error(f'Prisma: Remote Network {site_id} already exists')
        return False
    else:
        print(f'Remote Network {site_id} does not exist')
        logger.info(f'Prisma: Remote Network {site_id} does not exist')

    print(f'Getting SPN Location based on location entered: {location} ...')
    spn_location_dict = prisma.get_spn_location(prisma_session, location)
    if spn_location_dict == None:
        print("SPN Location not found, check location input is correct...")
        logger.error(f'Prisma: SPN Location for {location} not found')
        return False
    else:
        spn_location = spn_location_dict["spn_name_list"][0]
        logger.info(f'Prisma: Retrieved SPN Location from {location}: {spn_location}')

    print(f'Getting Region Name based on location entered: {location}')
    regions = prisma.get_region(prisma_session)
    for region in regions:
        if region["display"] == location:
            region_id = region["region"]
    
    logger.info(f'Prisma: Retrieved Region ID from {location}: {region_id}')

    print(hostname_ip_list)

    ### CREATE IKE GATEWAY(S) ###
    print("Creating IKE Gateways in Prisma...")
    ike_gw_result, ike_gw_names = prisma.create_ike_gw(prisma_session, hostname_ip_list)
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
        print("Deleting IKE Gateways...")
        ike_gws = prisma.get_ike_gateways(prisma_session, ike_gw_names)
        for ike_gw in ike_gws:
            ike_gws_del.append(ike_gw["id"])
        ike_gw_del_response = prisma.del_ike_gateways(prisma_session, ike_gws_del)
        if ike_gw_del_response != {200}:
            print("Unable to Roll Back IKE Gateways, delete manually!!")
            logger.error(f'Prisma: Unable to delete IKE Gateways')
        else:
            print("Roll back successful, IKE Gateways Successfully Deleted")
            logger.warning(f'Prisma: IKE Gateways Successfully Deleted')
        
        return False
    else:
        logger.info(f'Prisma: IPSec Tunnels {ipsec_tun_names} Successfully Created')
        print("IPSec Tunnels Successfully Created!")
        
    
    ##### CREATE REMOTE NETWORK ###
    remote_network_result = prisma.create_remote_nw(prisma_session, site_id, spn_location, ipsec_tun_names, region_id, remote_nw_subnets)
    if remote_network_result != 201:
        print("Remote Network could not be created...")
        print("Rolling Back...")
        print("Deleting IPSec Tunnels...")
        logger.error(f'Prisma: Remote Network {site_id} could not be created')
        ipsec_tuns = prisma.get_ipsec_tunnels(prisma_session, ipsec_tun_names)
        for ipsec_tun in ipsec_tuns:
            ipsec_tuns_del.append(ipsec_tun["id"])
        ipsec_tun_del_response = prisma.del_ipsec_tunnels(prisma_session, ipsec_tuns_del)
        if ipsec_tun_del_response != {200}:
            print("Unable to Roll Back IPSec Tunnels delete manually!!")
            logger.error(f'Prisma: Unable to delete IPSec Tunnels')
        else:
            print("Roll back successful, IPSec Tunnels Successfully Deleted")
            logger.warning(f'Prisma: IPSec Tunnels Successfully Deleted')
        
        print("Deleting IKE Gateways...")
        ike_gws = prisma.get_ike_gateways(prisma_session, ike_gw_names)
        for ike_gw in ike_gws:
            ike_gws_del.append(ike_gw["id"])
        ike_gw_del_response = prisma.del_ike_gateways(prisma_session, ike_gws_del)
        if ike_gw_del_response != {200}:
            print("Unable to Roll Back IKE Gateways, delete manually!!")
            logger.error(f'Prisma: Unable to delete IKE Gateways')
        else:
            print("Roll back successful, IKE Gateways Successfully Deleted")
            logger.warning(f'Prisma: IKE Gateways Successfully Deleted')

        return False
    else:
        print("Remote Network Successfully Created!")
        logger.info(f'Remote Network {site_id} Successfully Created!')
        return True

#    ### VMANAGE AUTHENTICATION ###
#    auth_header = sdwan.auth(url_var, username, password)
#
#    ### VMANAGE GET DEVICE DATA ###
#    vedge_data_ops = "dataservice/system/device/vedges"
#    vedge_data = sdwan.get_dev_data(url_var, vedge_data_ops, auth_header)
#    return vedge_data


    


