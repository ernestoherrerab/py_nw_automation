#! /usr/bin/env python
"""
Script to Provision Prisma Access Tunnels
"""

import logging
from pathlib import Path
import re
import urllib3
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

def provision_tunnel(config, site_data, vmanage_url, username, password):
    """ Main function to provision tunnels """
    
    ### DISABLE CERTIFICATE WARNINGS ###
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    ### VARIABLES ###
    site_code = site_data["site_code"].upper()
    location = site_data["location_id"]
    hostname_ip_list = set()
    subnets = []
    ike_gws_del = []
    ipsec_tuns_del = []
    current_template_list = []
    create_template_payload_list = []

    ### GENERATE IPFABRIC SESSION ###
    print("Authenticating to IPFabric...")
    ipf_session = ipfabric.auth()
    logger.info("IPFabric: Authenticated")

    ### RETRIEVE INTERFACE DATA FROM DEVICE ###
    print("Getting Public Interface Data of Site Routers...")
    if_filter_input = {"and": [{"hostname": ["reg",f'{site_code.lower()}-r\\d+-sdw']}]}
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
    subnets_filter_input = {"and": [{"hostname": ["reg",f'{site_code.lower()}-r\\d+-sdw']},{"vrf": ["eq","10"]},{"protocol": ["reg","S|C"]}]}
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
    remote_network = prisma.get_remote_nws(prisma_session, site_code)
    logger.info(f'Prisma: Checking if {site_code} remote network exists')

    if remote_network != None:
        print(remote_network)
        logger.error(f'Prisma: Remote Network {site_code} already exists')
        return False
    else:
        print(f'Remote Network {site_code} does not exist')
        logger.info(f'Prisma: Remote Network {site_code} does not exist')

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
    remote_network_result = prisma.create_remote_nw(prisma_session, site_code, spn_location, ipsec_tun_names, region_id, remote_nw_subnets)
    if remote_network_result != 201:
        print("Remote Network could not be created...")
        print("Rolling Back...")
        print("Deleting IPSec Tunnels...")
        logger.error(f'Prisma: Remote Network {site_code} could not be created')
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
        logger.info(f'Remote Network {site_code} Successfully Created!')


    site_code = "cph"
    ### VMANAGE AUTHENTICATION ###
    print("Authenticate vManage")
    auth = sdwan.auth(vmanage_url, username, password)
    logger.info("vManage: Authenticated")

    ### VMANAGE GET DEVICE DATA ###
    vedge_data = sdwan.get_vedge_list(auth, vmanage_url)
    logger.info("vManage: Get vEdge Data")

    ### FILTER DEVICES BY STATUS ###   
    vedge_list = [online_dev for online_dev in vedge_data if "reachability" in online_dev and online_dev["reachability"] == "reachable" and re.match(rf'{site_code}-r\d+-sdw', online_dev["host-name"]) ]
    logger.info(f'vManage: Filter vEdge Data...by site code')

    ### MAP HOST TO TEMPLATES ###
    print("Mapping Host to Templates...")
    vedge_template_map = sdwan.host_template_mapping(vedge_list)
    logger.info(f'vManage: Map Hosts to Templates')
    vedge_template_ids = [template_id["templateId"] for template_id in vedge_template_map]
    
    ### GET SDWAN TEMPLATES ###
    print("Retrieving Templates to clone...")
    for vedge_template_id in vedge_template_ids:
        create_template_payload = {}
        current_template = sdwan.get_template_config(auth, vmanage_url, vedge_template_id)
        logger.info(f'vManage: Format Payload to create New Template for template {current_template["templateName"]}')
        #feature_template_uids = [uid["templateId"] for uid in current_template["generalTemplates"]]
        create_template_payload["templateName"] = f'prisma_{current_template["templateName"]}'
        create_template_payload["templateDescription"] = f'prisma_{current_template["templateDescription"]}'
        create_template_payload["deviceType"] = current_template["deviceType"]
        create_template_payload["factoryDefault"] = current_template["factoryDefault"]
        create_template_payload["configType"] = current_template["configType"]
        create_template_payload["generalTemplates"] = current_template["generalTemplates"]
        #create_template_payload["featureTemplateUidRange"] = feature_template_uids
        create_template_payload["policyId"] = current_template["policyId"]
        if 'securityPolicyId' in current_template:
            create_template_payload['securityPolicyId'] = current_template['securityPolicyId']
        create_template_payload_list.append(create_template_payload)
    logger.info(f'vManage: Retrieved templates to clone and formatted payload')
    
    print(create_template_payload_list)
    ### CREATE NEW TEMPLATE(S) ###
    print("Creating new cloned Templates...")
    for template_payload in create_template_payload_list:
        response = sdwan.clone_template(auth, vmanage_url, template_payload)
        print(response)

    return response






#    ### GET SDWAN TEMPLATES ###
#    print("Retrieving SDWAN Templates")
#    sdwan_templates = sdwan.get_template_config(auth, url_var)
#    logger.info(f'vManage: Get SDWAN Templates')
    
#    ### FILTER SDWAN TEMPLATES BY ID ###
#    print("Filtering Relevant Template IDs")
#    vedge_templates = []
#    for sdwan_template in sdwan_templates:
#        for vedge_template_id in vedge_template_ids:
#            if vedge_template_id == sdwan_template["templateId"]:
#                vedge_templates.append(sdwan_template)
#    logger.info(f'vManage: Filter SDWAN Templates by ID')
#
#    print(vedge_templates)
    

#    ### VMANAGE AUTHENTICATION ###
#    print("Authenticate vManage")
#    auth_header = sdwan.auth(url_var, username, password)
#    logger.info("vManage: Authenticated")
#
#    ### VMANAGE GET DEVICE DATA ###
#    vedge_data_ops = "dataservice/system/device/vedges"
#    vedge_data = sdwan.get_dev_data(url_var, vedge_data_ops, auth_header)
#    logger.info("vManage: Get vEdge Data")
#
#    ### MAP HOST TO TEMPLATES ###
#    print("Mapping Host to Templates...")
#    vedge_list = sdwan.host_template_mapping(vedge_data)
#    logger.info(f'vManage: Map Hosts to Templates')
#    
#    #### FILTER VEDGE DATA BY SITE ID ###
#    for vedge in vedge_list["data"]:
#        site_code = site_code.lower()
#        vedge_match = re.match(rf'{site_code}-r\d+-sdw', vedge_data["host-name"])
#        if vedge_match:
#            template_id = vedge_data["templateId"]
#    return vedge_list


    


