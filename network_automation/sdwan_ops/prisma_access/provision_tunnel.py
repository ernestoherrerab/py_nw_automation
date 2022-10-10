#! /usr/bin/env python
"""
Script to Provision Prisma Access Tunnels
"""
from decouple import config
from json import dumps, loads
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

def provision_tunnel(config_file, site_data, vmanage_url, username, password):
    """ Main function to provision tunnels """
    
    ### DISABLE CERTIFICATE WARNINGS ###
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    ### VARIABLES ###
    VMANAGE_PRISMA_TEMPLATE_ID = config("VMANAGE_PRISMA_TEMPLATE_ID")
    #site_code = site_data["site_code"].upper()
    site_code = "CPH"
    location = site_data["location_id"]
    vedge_tunnel_ip = site_data["tunnel_ip"]
    
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
    print("Getting public IP data...")
    hostname_ip_set= set()
    for interface in dev_data:
        if interface["primaryIp"] != None:
            ip =  IPAddress(interface["primaryIp"])
            if ip.is_unicast() and not ip.is_private() and "Tunnel" not in interface["nameOriginal"]:
                hostname_ip_set.add((interface["hostname"], interface["primaryIp"], interface["nameOriginal"]))
    logger.info("IPFabric: Retrieved Public IPs from routers")
    

    ### GET SUBNET FROM IP FABRIC ###
    print("Getting Networks Data of Site Routers...")
    subnets_filter_input = {"and": [{"hostname": ["reg",f'{site_code.lower()}-r\\d+-sdw']},{"vrf": ["eq","10"]},{"protocol": ["reg","S|C"]}]}
    routes = ipfabric.get_subnets_data(ipf_session, subnets_filter_input)
    logger.info("IPFabric: Retrieved Static/Connected routes of SDWAN Routers")

    ### SUMMARIZE NETWORKS ###
    subnets = []
    for subnet in routes:
        subnets.append(subnet["network"])
    summary_subnets = cidr_merge(subnets)   
    remote_nw_subnets = [str(subnet) for subnet in summary_subnets]
    logger.info("IPFabric: Summarized Static/Connected routes of SDWAN Routers")
    
    ### GENERATE PRISMA SESSION ###
    print("Authenticating to Prisma...")
    prisma_session = prisma.auth(config_file)
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

    print(hostname_ip_set)

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
    ike_gws_del = []
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
    print("Creating remote network...")
    ipsec_tuns_del = []
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
    prisma_dest_ip = "1.1.1.1"
    vedge_tunnel_ip = "169.254.0.1/30"

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

    ### GET DEVICE IDS FOR VPN10 FEATURE TEMPLATE FROM VEDGE DATA ###
    device_type_set = {dev_type["deviceModel"] for dev_type in vedge_list}
    feature_templates = sdwan.get_dev_feature_template(auth, vmanage_url)
    cisco_vpn_template_ids_list = [cisco_vpn_templates["templateId"] for cisco_vpn_templates in feature_templates if cisco_vpn_templates["templateType"] == "cisco_vpn" and "vpn10" in cisco_vpn_templates["templateName"].lower() and any(ele in device_type_set for ele in cisco_vpn_templates["deviceType"])]

    ### MAP HOST TO TEMPLATES ###
    print("Mapping Host to Templates...")
    vedge_template_map = sdwan.host_template_mapping(vedge_list)
    logger.info(f'vManage: Map Hosts to Templates')
    vedge_template_ids = {template_id["templateId"] for template_id in vedge_template_map}


    ### GET SDWAN TEMPLATES AND APPEND NEW IPSEC SUB TEMPLATE ###
    print("Retrieving Templates to clone...")
    create_template_payload_tran_list = []
    new_templates_names = []
    for vedge_template_id in vedge_template_ids:
        create_template_payload = {}
        current_template = sdwan.get_template_config(auth, vmanage_url, vedge_template_id)
        for index, sub_templates in enumerate(current_template["generalTemplates"]):
            if sub_templates["templateId"] in cisco_vpn_template_ids_list:
                current_template["generalTemplates"][index]["subTemplates"].append({"templateId": VMANAGE_PRISMA_TEMPLATE_ID, "templateType": "cisco_vpn_interface_ipsec"})
        logger.info(f'vManage: Format Payload to create New Template for template {current_template["templateName"]}')
        ##feature_template_uids = [uid["templateId"] for uid in current_template["generalTemplates"]]
        create_template_payload["templateName"] = f'PRISMA_{current_template["templateName"]}'
        new_templates_names.append(create_template_payload["templateName"])
        create_template_payload["templateDescription"] = f'PRISMA_{current_template["templateDescription"]}'
        create_template_payload["deviceType"] = current_template["deviceType"]
        create_template_payload["factoryDefault"] = current_template["factoryDefault"]
        create_template_payload["configType"] = current_template["configType"]
        create_template_payload["generalTemplates"] = current_template["generalTemplates"]
        #create_template_payload["featureTemplateUidRange"] = feature_template_uids
        create_template_payload["policyId"] = current_template["policyId"]
        if 'securityPolicyId' in current_template:
            create_template_payload['securityPolicyId'] = current_template['securityPolicyId']
        create_template_payload_tran_list.append(create_template_payload)    
    create_template_payload_list = [i for n, i in enumerate(create_template_payload_tran_list) if i not in create_template_payload_tran_list[n + 1:]]
    logger.info(f'vManage: Retrieved templates to clone and formatted payload')
    
    #### CREATE NEW TEMPLATE(S) ###
    print("Creating new cloned Templates...")
    for index, template_payload in enumerate(create_template_payload_list):
        response = sdwan.clone_template(auth, vmanage_url, template_payload)
        if response == None:
            return False
        elif response["status_code"] != 200 and index > 0:
            print(f'Template creation for { template_payload["templateName"]} failed!!')
            logger.error(f'Template creation for { template_payload["templateName"]} failed')
            return False
        elif response["status_code"] != 200 and index >= 1:
            print(f'Template creation for { template_payload["templateName"]} failed!!')
            logger.error(f'Template creation for { template_payload["templateName"]} failed')
            print("Continuing provisioning since at least one template has already been cloned...")
            print(f'This failed template { template_payload["templateName"]} needs to be manually added...')
        elif response["status_code"] == 200:
            print(f'Template creation for { template_payload["templateName"]} was successful')
            logger.info(f'Template creation for { template_payload["templateName"]} successful')


    ### GET NEW TEMPLATE ID ### 
    print("Getting New Template Data...")
    logger.info(f'vManage: New template name: { new_templates_names}')
    new_templates = sdwan.get_all_templates_config(auth, vmanage_url, templates_names=new_templates_names)
    logger.info(f'vManage: Retrieved new template data for {new_templates_names}')
    new_template_ids = [template_id["templateId"] for template_id in new_templates]
        
    #### GET CURRENT TEMPLATE INPUT INFORMATION ###
    print("Getting current template input information...")
    current_dev_input_list = []
    for current_template_input in vedge_template_map:
        current_dev_input = sdwan.get_template_input(auth, vmanage_url, current_template_input["templateId"], current_template_input["deviceIds"])
        logger.info(f'vManage: Retrieved current template input info for {current_template_input["templateId"]}')
        current_dev_input_list.append(current_dev_input)
    logger.info(f'vManage: Retrieved current template input for all current templates')

    ### EVALUATE IF THERE ARE MORE INPUT LISTS THAN COPIES OF THE TEMPLATE TO ALLOW MAP ###
    if len(current_dev_input_list) > len(new_templates):
        rev_new_templates = [item for item in new_templates for _ in (0, len(current_dev_input_list) - len(new_templates))]
        logger.info(f'vManage: Replicated new templates')
    else:
        rev_new_templates = new_templates
        logger.info(f'vManage: No need to replicate new templates')

    #### GET NEW TEMPLATE INPUT INFORMATION ###
    new_dev_input_list = []
    for new_template_input in rev_new_templates:
        new_dev_input = sdwan.get_template_input(auth, vmanage_url, new_template_input["templateId"])
        new_dev_input_list.append(new_dev_input)
        logger.info(f'vManage: Retrieved new template input info for {new_template_input["templateId"]}')
    
    ### COPY CURRENT DEV DATA TO NEW DEV DATA IN INPUT ###
    print("Copying data from current input to new input...")
    for new_input, current_input in zip(new_dev_input_list, current_dev_input_list):
        new_input["data"] = current_input["data"]
        logger.info(f'vManage: Generated new template input for: {new_input["data"][0]["csv-host-name"]}')

    #### ENTER INPUT DATA FOR PRISMA FEATURE TEMPLATE ###
    #hostname_ip_set = {('cph-r03-sdw', '172.16.0.80', 'GigabitEthernet0/0/0'), ('cph-r01-sdw', '172.16.0.80', 'GigabitEthernet0/0/0')}
    print("Entering input data for prisma feature template")
    for input_data in new_dev_input_list:
        for host_tunnel_if in hostname_ip_set:
            if  host_tunnel_if[0] == input_data["data"][0]["csv-host-name"]:
                input_data["data"][0]["/10/ipsec10/interface/tunnel-source-interface"] = host_tunnel_if[2]
                input_data["data"][0]["/10/ipsec10/interface/tunnel-destination"] = prisma_dest_ip
                input_data["data"][0]["/10/ipsec10/interface/ip/address"] = vedge_tunnel_ip
        logger.info(f'vManage: Added new template feature input for: {input_data["data"][0]["csv-host-name"]}')

    ### EVALUATE IF THERE ARE MORE TEMPLATE IDS THAN INPUT DATA TEMPLATES ###
    if len(new_dev_input_list) > len(new_template_ids):
        rev_new_template_ids = [item for item in new_template_ids for _ in (0, len(new_dev_input_list) - len(new_template_ids))]
        logger.info(f'vManage: Replicated new templates ids')
    else:
        rev_new_template_ids = new_template_ids
        logger.info(f'vManage: No need to replicate new templates ids')
    
    ### FORMAT FINAL DATA STRUCTURE ###
    print("Formatting data to push to vManage...")
    feature_template_dict = {}
    feature_template_dict["deviceTemplateList"] = []
    for template_id, template in zip(rev_new_template_ids, new_dev_input_list):
        feature_template_dict["deviceTemplateList"].append(
            {"templateId": template_id, 
            "device": template["data"], 
            "isEdited": False, 
            "isMasterEdited": False})
    logger.info(f'vManage: Data ready to be uploaded to vManage')

    ### REMOVE PROBLEM DEVICES IF THEY EXIST ###
    print("Evaluating if there are problem templates and remove them...")
    for dev_index, dev in enumerate(feature_template_dict["deviceTemplateList"].copy()):
        for failed_dev in dev["device"]:
            if failed_dev["csv-status"] != "complete":
                feature_template_dict["deviceTemplateList"].pop(dev_index)
                print(f'Removing {failed_dev["csv-host-name"]} for payload due to {failed_dev["csv-status"]}')
                logger.info(f'vManage: Removed {failed_dev["csv-host-name"]} for payload due to {failed_dev["csv-status"]}')
            else:
                feature_template_dict["deviceTemplateList"][dev_index]["device"][0]["csv-templateId"] = feature_template_dict["deviceTemplateList"][dev_index]["templateId"] 
    logger.info(f'vManage: Evaluated templates to push')

    #### PUSH TEMPLATES TO DEVICES ###
    print("Pushing templates to devices...")
    response = sdwan.attach_dev_template(auth, vmanage_url, feature_template_dict)
    print(response)
    
    return feature_template_dict


    


