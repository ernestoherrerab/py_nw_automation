#! /usr/bin/env python
"""
Script to Create SDWAN IPSec Tunnels
"""

from decouple import config
from json import loads
import logging
from pathlib import Path
import re
from rich import print as pprint
from time import sleep
from netaddr import IPAddress
import libs.sdwan_api as sdwan


### LOGGING SETUP ###
LOG_FILE = Path("logs/sdwan_ops.log")
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler(LOG_FILE)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

def format_data_structure(template_id: str, dev_input: dict, auth_session: object, vmanage_url: str) -> list:

    ### VARS ###
    summary_list = []
    
    ### FORMAT FINAL DATA STRUCTURE ###
    print("Formatting data to push to vManage...")
    feature_template_dict = {}
    feature_template_dict["deviceTemplateList"] = []
    feature_template_dict["deviceTemplateList"].append(
        {"templateId": template_id, 
        "device": dev_input, 
        "isEdited": False, 
        "isMasterEdited": False})
    logger.info(f'vManage: Data ready to be uploaded to vManage')
    
    ### REMOVE PROBLEM DEVICES IF THEY EXIST ###
    print("Evaluating if there are problem templates and remove them...")
    csv_status = feature_template_dict["deviceTemplateList"][0]["device"][0]["csv-status"]
    csv_hostname = feature_template_dict["deviceTemplateList"][0]["device"][0]["csv-host-name"]
    if csv_status != "complete":
        print(f'Removing {csv_hostname} for payload due to {csv_status}')
        print("Device will not be attached...")
        logger.info(f'vManage: Removed {{csv_hostname}} for payload due to {csv_status}')
        summary_list.append(
            {
                "action_status": csv_status,
                "action_activity": "Not Pushed",
                "action_config": "Not Pushed"
                })
        return summary_list
    else:
        feature_template_dict["deviceTemplateList"][0]["device"][0]["csv-templateId"] = feature_template_dict["deviceTemplateList"][0]["templateId"] 
        logger.info(f'vManage: Evaluated templates to push')

        ### PUSH TEMPLATES TO DEVICES ###
        print("Pushing templates to devices...")
        print(feature_template_dict)
        ops_id, summary_obj = sdwan.attach_dev_template(auth_session, vmanage_url, feature_template_dict)
        summary = dict(summary_obj)
        logger.info(f'vManage: {ops_id}') 

        ### FORMAT SUMMARY FOR LOGGING ###
        summary_status = summary["action_status"]
        summary_activity = summary["action_activity"]
        summary_config = loads(summary["action_config"])
        summary_list.append(                {
                "action_status": summary_status,
                "action_activity": summary_activity,
                "action_config": summary_config
                })
        if summary_status == "success":
            logger.info(f'vManage: Provisioning was {summary_status}')
            for activity in summary_activity:
                logger.info(f'vManage:  {activity}')
            for configuration in summary_config:
                logger.info(f'vManage:  {configuration}')
            return summary_list
        else:
            logger.error(f'vManage: Provisioning was {summary_status}') 
            for activity in summary_activity:
                logger.error(f'vManage:  {activity}')
            for configuration in summary_config:
                logger.error(f'vManage:  {configuration}')
        return summary_list
    
def create_ipsec_tunnels(site_data: dict, username: str, password: str, hostname_ip_set: set, public_ip: list, bgp_asn: str, bgp_peers: list, tunnel_ips: list) -> list:
    """ Create SDWAN IPSec Tunnels
    Args:
    site_data (dict): From frontend input
    username (str): From frontend input
    password (str): From frontend input
    hostname_ip_set (set): Contains IPFabric parameters to create IPSec Tunnels
    public_ip (list): Contains the Public IP of the Prisma Access node 
    bgp_asn (str): BGP ASN Required for SDWAN 
    bgp_peers (list): BGP Peer IPs
    tunnel_ips (list): List of IP addresses to use for the SDWAN tunnels

    Return:
    summary_list (list): Contains a summary of the result

    """
    ### VARS ###
    VMANAGE_URL_VAR = config("VMANAGE_URL_VAR")
    VMANAGE_PRISMA_PRIM_TEMPLATE_ID = config("VMANAGE_PRISMA_PRIM_TEMPLATE_ID")
    VMANAGE_PRISMA_SEC_TEMPLATE_ID = config("VMANAGE_PRISMA_SEC_TEMPLATE_ID")
    VMANAGE_AZURE_LIST_ID = config("VMANAGE_AZURE_LIST_ID")
    VMANAGE_VSMART_TEMPLATE_ID = config("VMANAGE_VSMART_TEMPLATE_ID")
    VMANAGE_PRISMA_BGP = config("VMANAGE_PRISMA_BGP")
    site_code = site_data["site_code"].upper()
    new_template_name = ""
    summary_list = []
    red_nw_list = ["10105","30117","30040","10123","10040"]

    ### CONVERT TUPLES TO LISTS ###
    staging_set = set()
    for hostname_ip_tuple, tunnel_ip in zip(hostname_ip_set, tunnel_ips):
        peer_id = IPAddress(hostname_ip_tuple[1])
        if peer_id.is_unicast() and peer_id.is_private():
            staging_set.add((hostname_ip_tuple[0], tunnel_ip, hostname_ip_tuple[2]))
        else:
            staging_set.add(hostname_ip_tuple)

    device_parameters = list(map(list, hostname_ip_set ))
    print(f'staging_set VAR: {staging_set}')
    print(f'device_parameters VAR: {device_parameters}')
    ### ADD TUNNEL IP TO DEVICE PARAMETERS ###
    for hostname_ip, tunnel_ip in zip(device_parameters, tunnel_ips):
        hostname_ip.append(tunnel_ip)
    print(f'hostname_ip VAR: {hostname_ip}')

    ### DEFINE IF A SECONDARY IPSEC TUNNEL IS NEEDED ###
    sec_tunnel = False
    if len(device_parameters)> 1:
        if device_parameters[0][0] == device_parameters[1][0]:
            sec_tunnel = True
            logger.info(f'vManage: Secondary Tunnel is needed')
            print("Secondary Tunnel is needed...")
        elif device_parameters[0][0] != device_parameters[1][0]:
            logger.info(f'vManage: Secondary Tunnel is NOT needed')
            print("Secondary Tunnel is NOT needed...")
    else:
        logger.info(f'vManage: Single router Single Link')
        

    ### VMANAGE AUTHENTICATION ###
    print("Authenticate vManage")
    auth = sdwan.auth(VMANAGE_URL_VAR, username, password)
    logger.info("vManage: Authenticated")

    ### VMANAGE GET DEVICE DATA ###
    vedge_data = sdwan.get_vedge_list(auth, VMANAGE_URL_VAR)
    logger.info("vManage: Get vEdge Data")

    ### FILTER DEVICES BY SITE CODE AND REACHABILITY ###  
    site_code = site_code.lower()
    vedge_list = [online_dev for online_dev in vedge_data if "reachability" in online_dev and online_dev["reachability"] == "reachable" and re.match(rf'{site_code}-r\d+-sdw', online_dev["host-name"]) ]
    logger.info(f'vManage: Filter vEdge Data by site code: {site_code}')
        
    
    ### FOR LOOP USED TO FORMAT NEW TEMPLATE DATA FOR DEVICE ATTACHMENT ####
    for vedge in vedge_list:
        ### GET DEVICE ID FOR VPN10 FEATURE TEMPLATE FROM VEDGE DATA ###
        sdwan_site_id = vedge["site-id"]
        template_name = vedge["template"]
        template_list = sdwan.get_all_templates_config(auth, VMANAGE_URL_VAR, [f'DT-PRISMA-{template_name}'])
        feature_templates = sdwan.get_dev_feature_template(auth, VMANAGE_URL_VAR)

        ### MAP HOST TO TEMPLATE ###
        print("Mapping Host to Templates...")
        vedge_template_map = sdwan.host_template_mapping(vedge)
        logger.info(f'vManage: Map Hosts to Templates')
        vedge_template_id = vedge_template_map["templateId"] 
        
        if not template_list:
            ### FILTER DATA TO GET ID OF DEVICE VPN10 FEATURETEMPLATE ###
            cisco_vpn_template_id_list = [cisco_vpn_templates["templateId"] for cisco_vpn_templates in feature_templates if cisco_vpn_templates["templateType"] == "cisco_vpn" and cisco_vpn_templates["templateName"] == "FT-VPN10-CEDGE"]  

            ### GET SDWAN CURRENT TEMPLATE AND APPEND NEW IPSEC SUB TEMPLATE ###
            ### ONLY NEEDED IF ITS A NEW TEMPLATE ###
            print("Retrieving Templates to clone...")
            create_template_payload = {}
            current_template = sdwan.get_template_config(auth, VMANAGE_URL_VAR, vedge_template_id)
            for index, sub_templates in enumerate(current_template["generalTemplates"]):
                if sub_templates["templateId"] in cisco_vpn_template_id_list and not sec_tunnel:
                    current_template["generalTemplates"][index]["subTemplates"].append({"templateId": VMANAGE_PRISMA_PRIM_TEMPLATE_ID, "templateType": "cisco_vpn_interface_ipsec"})
                    current_template["generalTemplates"][index]["subTemplates"].append({"templateId":  VMANAGE_PRISMA_BGP, "templateType": "cisco_bgp"})    
                elif sub_templates["templateId"] in cisco_vpn_template_id_list and sec_tunnel:
                    current_template["generalTemplates"][index]["subTemplates"].append({"templateId": VMANAGE_PRISMA_PRIM_TEMPLATE_ID, "templateType": "cisco_vpn_interface_ipsec"})
                    current_template["generalTemplates"][index]["subTemplates"].append({"templateId": VMANAGE_PRISMA_SEC_TEMPLATE_ID, "templateType": "cisco_vpn_interface_ipsec"})
                    current_template["generalTemplates"][index]["subTemplates"].append({"templateId":  VMANAGE_PRISMA_BGP, "templateType": "cisco_bgp"})
            logger.info(f'vManage: Format Payload to create New Template for template {current_template["templateName"]}')

            ### CLONE NEW DEVICE TEMPLATE DATA WITH CURRENT NEW TEMPLATE + NEW PRISMA FEATURE TEMPLATE ###
            ### ONLY NEEDED IF ITS A NEW TEMPLATE ###
            create_template_payload["templateName"] = f'DT-PRISMA-{current_template["templateName"]}'
            create_template_payload["templateDescription"] = f'DT-PRISMA-{current_template["templateDescription"]}'
            create_template_payload["deviceType"] = current_template["deviceType"]
            create_template_payload["factoryDefault"] = current_template["factoryDefault"]
            create_template_payload["configType"] = current_template["configType"]
            create_template_payload["generalTemplates"] = current_template["generalTemplates"]
            create_template_payload["policyId"] = current_template["policyId"]
            if 'securityPolicyId' in current_template:
                create_template_payload['securityPolicyId'] = current_template['securityPolicyId']
            logger.info(f'vManage: Format Payload created for template {current_template["templateName"]}')  
            print(create_template_payload)
            if new_template_name == "" or new_template_name != create_template_payload["templateName"]:
                #### CREATE NEW TEMPLATE(S) ###
                print("Creating new cloned Templates...")
                response = sdwan.clone_template(auth, VMANAGE_URL_VAR, create_template_payload)
                if response == None:
                    return False
                elif response["status_code"] != 200:
                    print(f'Template creation for { create_template_payload["templateName"]} failed!!')
                    logger.error(f'Template creation for { create_template_payload["templateName"]} failed')
                    return False
                elif response["status_code"] == 200:
                    print(f'Template creation for { create_template_payload["templateName"]} was successful')
                    logger.info(f'Template creation for { create_template_payload["templateName"]} successful')

            ### GET NEW TEMPLATE ID ### 
            ### ONLY NEEDED IF ITS A NEW TEMPLATE ###
            print("Getting New Template Data...")
            logger.info(f'vManage: New template name: { create_template_payload["templateName"]}')
            new_template = sdwan.get_all_templates_config(auth, VMANAGE_URL_VAR, template_name=[create_template_payload["templateName"]])
            logger.info(f'vManage: Retrieved new template data for {create_template_payload["templateName"]}')
            new_template_id = new_template[0]["templateId"]
            new_template_name = new_template[0]["templateName"]

            #### GET CURRENT TEMPLATE INPUT INFORMATION ###
            print("Getting current template input information...")
            current_dev_input = sdwan.get_template_input(auth, VMANAGE_URL_VAR, vedge_template_map["templateId"], vedge_template_map["deviceIds"])
            logger.info(f'vManage: Retrieved current template input info for {vedge_template_map["templateId"]}')

            ##### GET NEW TEMPLATE INPUT INFORMATION ###
            ### ONLY NEEDED IF ITS A NEW TEMPLATE ###
            print("Getting new template input information...")
            new_dev_input = sdwan.get_template_input(auth, VMANAGE_URL_VAR, new_template_id)
            logger.info(f'vManage: Retrieved new template input info for {new_template_id}')

            ### COPY CURRENT DEV DATA TO NEW DEV DATA IN INPUT ###
            ### ONLY NEEDED IF ITS A NEW TEMPLATE ###
            print("Copying data from current input to new input...")
            new_dev_input["data"] = current_dev_input["data"]
            logger.info(f'vManage: Generated new template input for: {new_dev_input["data"][0]["csv-host-name"]}')

            #### ENTER INPUT DATA FOR PRISMA FEATURE TEMPLATE ###
            ### ONLY NEEDED IF ITS A NEW TEMPLATE ###
            print("Entering input data for prisma feature template")
            for index, host_tunnel_if in enumerate(device_parameters):
                print(host_tunnel_if)
                if  host_tunnel_if[0] == new_dev_input["data"][0]["csv-host-name"] and not sec_tunnel:
                    new_dev_input["data"][0]["/10/ipsec10/interface/tunnel-source-interface"] = host_tunnel_if[2]
                    new_dev_input["data"][0]["/10/ipsec10/interface/tunnel-destination"] = public_ip[0]
                    new_dev_input["data"][0]["/10/ipsec10/interface/ip/address"] =  (f'{host_tunnel_if[3]}/30') 
                    new_dev_input["data"][0]["/10//router/bgp/as-num"] = bgp_asn
                    new_dev_input["data"][0]["/10//router/bgp/neighbor/bgp_neighbor_address_pri/address"] = bgp_peers[0]
                    new_dev_input["data"][0]["/10//router/bgp/neighbor/bgp_neighbor_address_sec/address"] = "TEMPLATE_IGNORE"
                    logger.info(f'vManage: Added new template feature input for primary ipsec tunnel: {new_dev_input["data"][0]["csv-host-name"]}')
                elif sec_tunnel and index == 0:
                    new_dev_input["data"][0]["/10/ipsec10/interface/tunnel-source-interface"] = host_tunnel_if[2]
                    new_dev_input["data"][0]["/10/ipsec10/interface/tunnel-destination"] = public_ip[0]
                    new_dev_input["data"][0]["/10/ipsec10/interface/ip/address"] =  (f'{host_tunnel_if[3]}/30') 
                    new_dev_input["data"][0]["/10//router/bgp/as-num"] = bgp_asn
                    new_dev_input["data"][0]["/10//router/bgp/neighbor/bgp_neighbor_address_pri/address"] = bgp_peers[0]
                    logger.info(f'vManage: Added new template feature input for primary ipsec tunnel: {new_dev_input["data"][0]["csv-host-name"]}')
                elif sec_tunnel and index == 1:
                    new_dev_input["data"][0]["/10/ipsec20/interface/tunnel-source-interface"] = host_tunnel_if[2]
                    new_dev_input["data"][0]["/10/ipsec20/interface/tunnel-destination"] = public_ip[0]
                    new_dev_input["data"][0]["/10/ipsec20/interface/ip/address"] =  (f'{host_tunnel_if[3]}/30')
                    new_dev_input["data"][0]["/10//router/bgp/neighbor/bgp_neighbor_address_sec/address"] = bgp_peers[1]
                    logger.info(f'vManage: Added new template feature input for secondary ipsec tunnel: {new_dev_input["data"][0]["csv-host-name"]}')
            print("The Template Input is:")
            pprint(new_dev_input)

            #### FORMAT FINAL DATA STRCUTURE ###
            summary_list = format_data_structure(new_template_id, new_dev_input["data"], auth, VMANAGE_URL_VAR)  
            sleep(240)
            if sdwan_site_id not in red_nw_list:
                list_update = sdwan.update_site_list(auth, VMANAGE_AZURE_LIST_ID, sdwan_site_id, VMANAGE_URL_VAR, VMANAGE_VSMART_TEMPLATE_ID)
                logger.info(f'vManage: The vSmart controllers were updated: {list_update}')         
            else:
                logger.info(f'vManage: The site ID belongs to the red_green site list') 
                print(f'vManage: The site ID belongs to the red_green site list')            

        else:
            ### GET EXISTING PRISMA TEMPLATE ID ###
            prisma_template_id = template_list[0]['templateId'] 

            #### GET CURRENT TEMPLATE INPUT INFORMATION ###
            print("Getting current template input information...")
            current_dev_input = sdwan.get_template_input(auth, VMANAGE_URL_VAR, vedge_template_map["templateId"], vedge_template_map["deviceIds"])
            logger.info(f'vManage: Retrieved current template input info for {vedge_template_map["templateId"]}')

            ##### GET PRISMA TEMPLATE INPUT INFORMATION ###
            print("Getting new template input information...")
            prisma_dev_input = sdwan.get_template_input(auth, VMANAGE_URL_VAR, prisma_template_id)
            print("The input information for the prisma template is:")
            pprint(prisma_dev_input)
            logger.info(f'vManage: Retrieved new template input info for {prisma_template_id}')

            ### COPY CURRENT DEV DATA TO NEW DEV DATA IN INPUT ###
            print("Copying data from current input to new input...")
            prisma_dev_input["data"] = current_dev_input["data"]
            logger.info(f'vManage: Generated new template input for: {prisma_dev_input["data"][0]["csv-host-name"]}')

            #### ENTER INPUT DATA FOR PRISMA FEATURE TEMPLATE ###
            ### ONLY NEEDED IF ITS A NEW TEMPLATE ###
            print("Entering input data for prisma feature template")
            for index, host_tunnel_if in enumerate(device_parameters):
                print(host_tunnel_if)
                if  host_tunnel_if[0] == prisma_dev_input["data"][0]["csv-host-name"] and not sec_tunnel:
                    prisma_dev_input["data"][0]["/10/ipsec10/interface/tunnel-source-interface"] = host_tunnel_if[2]
                    prisma_dev_input["data"][0]["/10/ipsec10/interface/tunnel-destination"] = public_ip[0]
                    prisma_dev_input["data"][0]["/10/ipsec10/interface/ip/address"] =  (f'{host_tunnel_if[3]}/30') 
                    prisma_dev_input["data"][0]["/10//router/bgp/as-num"] = bgp_asn
                    prisma_dev_input["data"][0]["/10//router/bgp/neighbor/bgp_neighbor_address_pri/address"] = bgp_peers[0]
                    prisma_dev_input["data"][0]["/10//router/bgp/neighbor/bgp_neighbor_address_sec/address"] = "TEMPLATE_IGNORE"
                    logger.info(f'vManage: Added new template feature input for primary ipsec tunnel: {prisma_dev_input["data"][0]["csv-host-name"]}')
                elif sec_tunnel and index == 0:
                    prisma_dev_input["data"][0]["/10/ipsec10/interface/tunnel-source-interface"] = host_tunnel_if[2]
                    prisma_dev_input["data"][0]["/10/ipsec10/interface/tunnel-destination"] = public_ip[0]
                    prisma_dev_input["data"][0]["/10/ipsec10/interface/ip/address"] =  (f'{host_tunnel_if[3]}/30') 
                    prisma_dev_input["data"][0]["/10//router/bgp/as-num"] = bgp_asn
                    prisma_dev_input["data"][0]["/10//router/bgp/neighbor/bgp_neighbor_address_pri/address"] = bgp_peers[0]
                    logger.info(f'vManage: Added new template feature input for primary ipsec tunnel: {prisma_dev_input["data"][0]["csv-host-name"]}')
                elif sec_tunnel and index == 1:
                    prisma_dev_input["data"][0]["/10/ipsec20/interface/tunnel-source-interface"] = host_tunnel_if[2]
                    prisma_dev_input["data"][0]["/10/ipsec20/interface/tunnel-destination"] = public_ip[0]
                    prisma_dev_input["data"][0]["/10/ipsec20/interface/ip/address"] =  (f'{host_tunnel_if[3]}/30')
                    prisma_dev_input["data"][0]["/10//router/bgp/neighbor/bgp_neighbor_address_pri/address"] = bgp_peers[1]
                    logger.info(f'vManage: Added new template feature input for secondary ipsec tunnel: {prisma_dev_input["data"][0]["csv-host-name"]}')
            print("The Template Input is:")
            pprint(prisma_dev_input)
            #### FORMAT FINAL DATA STRCUTURE ###
            summary_list = format_data_structure(prisma_template_id, prisma_dev_input["data"], auth, VMANAGE_URL_VAR)
            sleep(240)
            if sdwan_site_id not in red_nw_list:
                list_update = sdwan.update_site_list(auth, VMANAGE_AZURE_LIST_ID, sdwan_site_id, VMANAGE_URL_VAR, VMANAGE_VSMART_TEMPLATE_ID)
                logger.info(f'vManage: The vSmart controllers were updated')
                print(list_update)
            else:
                logger.info(f'vManage: The site ID belongs to the red_green site list') 
                print(f'vManage: The site ID belongs to the red_green site list')
    return summary_list       
             
