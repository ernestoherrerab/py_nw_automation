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
from time import sleep
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
    PRISMA_API_KEY = config("PRISMA_API_KEY")
    site_code = site_data["site_code"].upper()
    location = site_data["location_id"]
    vedge_tunnel_ip = site_data["tunnel_ip"]
    summary_list = []

    
    ### GENERATE IPFABRIC SESSION ###
    print("Authenticating to IPFabric...")
    ipf_session = ipfabric.auth()
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
    for interface in dev_data:
        if interface["primaryIp"] != None:
            ip =  IPAddress(interface["primaryIp"])
            if ip.is_unicast() and not ip.is_private() and "Tunnel" not in interface["nameOriginal"]:
                hostname_ip_set.add((interface["hostname"], interface["primaryIp"], interface["nameOriginal"]))
    logger.info("IPFabric: Retrieved Public IPs from routers")
    

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
    
    ### GENERATE PRISMA SESSION ###
    print("Authenticating to Prisma...")
    prisma_session = prisma.auth(config_file)
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

    ### RETRIEVE SPN VALUE BASED ON THE LOCATION INPUT ###
    print(f'Getting SPN Location based on location entered: {location} ...')
    spn_location_dict = prisma.get_spn_location(prisma_session, location)
    if spn_location_dict == None:
        print("SPN Location not found, check location input is correct...")
        logger.error(f'Prisma: SPN Location for {location} not found')
        return False
    else:
        spn_location = spn_location_dict["spn_name_list"][0]
        logger.info(f'Prisma: Retrieved SPN Location from {location}: {spn_location}')

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
    
    ### ROLL BACK IF PROCESS FAILS ###
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
        logger.info(f'Prisma: Remote Network {site_code} Successfully Created!')
        
        ### PUSH CONFIG ###
        prisma.push_config(prisma_session)
        
        ### GET PUBLIC IP FOR SDWAN TUNNEL DESTINATION ###
        public_ip = []
        while public_ip == []:
            public_ips = prisma.get_public_ip(PRISMA_API_KEY)
            public_ip = [ip["address"] for item in public_ips for ip in item["address_details"] if ip["addressType"] == "active" and site_code in ip["node_name"] ]
            sleep(20)
        logger.info(f'Prisma: The public IP is {public_ip[0]}')

    ### VMANAGE AUTHENTICATION ###
    print("Authenticate vManage")
    auth = sdwan.auth(vmanage_url, username, password)
    logger.info("vManage: Authenticated")

    ### VMANAGE GET DEVICE DATA ###
    vedge_data = sdwan.get_vedge_list(auth, vmanage_url)
    logger.info("vManage: Get vEdge Data")

    ### FILTER DEVICES BY SITE CODE AND REACHABILITY ###  
    site_code = site_code.lower()
    vedge_list = [online_dev for online_dev in vedge_data if "reachability" in online_dev and online_dev["reachability"] == "reachable" and re.match(rf'{site_code}-r\d+-sdw', online_dev["host-name"]) ]
    logger.info(f'vManage: Filter vEdge Data...by site code')
    
    ### FOR LOOP USED TO FORMAT NEW TEMPLATE DATA FOR DEVICE ATTACHMENT ####
    for vedge in vedge_list:
        ### GET DEVICE ID FOR VPN10 FEATURE TEMPLATE FROM VEDGE DATA ###
        ### HEAVILY DEPENDANT ON FEATURE VPN TEMPLATE BEING USING "VPN10" ON ITS NAMING ### 
        device_type = vedge["deviceModel"]
        feature_templates = sdwan.get_dev_feature_template(auth, vmanage_url)

        ### FILTER DATA TO GET ID OF DEVICE VPN10 FEATURETEMPLATE ###
        cisco_vpn_template_id_list = [cisco_vpn_templates["templateId"] for cisco_vpn_templates in feature_templates if cisco_vpn_templates["templateType"] == "cisco_vpn" and "vpn10" in cisco_vpn_templates["templateName"].lower() and device_type in cisco_vpn_templates["deviceType"]]
               
        ### MAP HOST TO TEMPLATE ###
        print("Mapping Host to Templates...")
        vedge_template_map = sdwan.host_template_mapping(vedge)
        logger.info(f'vManage: Map Hosts to Templates')
        vedge_template_id = vedge_template_map["templateId"] 
    
        ### GET SDWAN CURRENT TEMPLATE AND APPEND NEW IPSEC SUB TEMPLATE ###
        print("Retrieving Templates to clone...")
        new_templates_names = []
        create_template_payload = {}
        current_template = sdwan.get_template_config(auth, vmanage_url, vedge_template_id)
        for index, sub_templates in enumerate(current_template["generalTemplates"]):
            if sub_templates["templateId"] in cisco_vpn_template_id_list:
                current_template["generalTemplates"][index]["subTemplates"].append({"templateId": VMANAGE_PRISMA_TEMPLATE_ID, "templateType": "cisco_vpn_interface_ipsec"})
        logger.info(f'vManage: Format Payload to create New Template for template {current_template["templateName"]}')
        ### CLONE NEW DEVICE TEMPLATE DATA WITH CURRENT NEW TEMPLATE + NEW PRISMA FEATURE TEMPLATE ###
        create_template_payload["templateName"] = f'PRISMA_{current_template["templateName"]}'
        create_template_payload["templateDescription"] = f'PRISMA_{current_template["templateDescription"]}'
        create_template_payload["deviceType"] = current_template["deviceType"]
        create_template_payload["factoryDefault"] = current_template["factoryDefault"]
        create_template_payload["configType"] = current_template["configType"]
        create_template_payload["generalTemplates"] = current_template["generalTemplates"]
        create_template_payload["policyId"] = current_template["policyId"]
        if 'securityPolicyId' in current_template:
            create_template_payload['securityPolicyId'] = current_template['securityPolicyId']
        logger.info(f'vManage: Format Payload created for template {current_template["templateName"]}')         

        #### CREATE NEW TEMPLATE(S) ###
        print("Creating new cloned Templates...")
        response = sdwan.clone_template(auth, vmanage_url, create_template_payload)
        if response == None:
            return False
        elif response["status_code"] != 200 and index > 0:
            print(f'Template creation for { create_template_payload["templateName"]} failed!!')
            logger.error(f'Template creation for { create_template_payload["templateName"]} failed')
            return False
        elif response["status_code"] != 200 and index >= 1:
            print(f'Template creation for { create_template_payload["templateName"]} failed!!')
            logger.error(f'Template creation for { create_template_payload["templateName"]} failed')
            print("Continuing provisioning since at least one template has already been cloned...")
            print(f'This failed template { create_template_payload["templateName"]} needs to be manually added...')
        elif response["status_code"] == 200:
            print(f'Template creation for { create_template_payload["templateName"]} was successful')
            logger.info(f'Template creation for { create_template_payload["templateName"]} successful')

        ### GET NEW TEMPLATE ID ### 
        print("Getting New Template Data...")
        logger.info(f'vManage: New template name: { create_template_payload["templateName"]}')
        new_template = sdwan.get_all_templates_config(auth, vmanage_url, template_name=[create_template_payload["templateName"]])
        logger.info(f'vManage: Retrieved new template data for {create_template_payload["templateName"]}')
        new_template_id = new_template[0]["templateId"]
        
        #### GET CURRENT TEMPLATE INPUT INFORMATION ###
        print("Getting current template input information...")
        current_dev_input = sdwan.get_template_input(auth, vmanage_url, vedge_template_map["templateId"], vedge_template_map["deviceIds"])
        logger.info(f'vManage: Retrieved current template input info for {vedge_template_map["templateId"]}')
        
        ##### GET NEW TEMPLATE INPUT INFORMATION ###
        print("Getting new template input information...")
        new_dev_input = sdwan.get_template_input(auth, vmanage_url, new_template_id)
        logger.info(f'vManage: Retrieved new template input info for {new_template_id}')
    
        ### COPY CURRENT DEV DATA TO NEW DEV DATA IN INPUT ###
        print("Copying data from current input to new input...")
        new_dev_input["data"] = current_dev_input["data"]
        logger.info(f'vManage: Generated new template input for: {new_dev_input["data"][0]["csv-host-name"]}')

        #### ENTER INPUT DATA FOR PRISMA FEATURE TEMPLATE ###
        print("Entering input data for prisma feature template")
        for host_tunnel_if in hostname_ip_set:
            if  host_tunnel_if[0] == new_dev_input["data"][0]["csv-host-name"]:
                new_dev_input["data"][0]["/10/ipsec10/interface/tunnel-source-interface"] = host_tunnel_if[2]
                new_dev_input["data"][0]["/10/ipsec10/interface/tunnel-destination"] = public_ip[0]
                new_dev_input["data"][0]["/10/ipsec10/interface/ip/address"] = vedge_tunnel_ip
        logger.info(f'vManage: Added new template feature input for: {new_dev_input["data"][0]["csv-host-name"]}')

        ### FORMAT FINAL DATA STRUCTURE ###
        print("Formatting data to push to vManage...")
        feature_template_dict = {}
        feature_template_dict["deviceTemplateList"] = []
        feature_template_dict["deviceTemplateList"].append(
            {"templateId": new_template_id, 
            "device": new_dev_input["data"], 
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
        else:
            feature_template_dict["deviceTemplateList"][0]["device"][0]["csv-templateId"] = feature_template_dict["deviceTemplateList"][0]["templateId"] 
            logger.info(f'vManage: Evaluated templates to push')
            
            ### PUSH TEMPLATES TO DEVICES ###
            print("Pushing templates to devices...")
            ops_id, summary_obj = sdwan.attach_dev_template(auth, vmanage_url, feature_template_dict)
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
            else:
                logger.error(f'vManage: Provisioning was {summary_status}') 
                for activity in summary_activity:
                    logger.error(f'vManage:  {activity}')
                for configuration in summary_config:
                    logger.error(f'vManage:  {configuration}')       
    print(summary_list)
    return summary_list


    


