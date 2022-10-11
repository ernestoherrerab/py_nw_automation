#! /usr/bin/env python
"""
Prisma Access API Functions
"""
from decouple import config
import logging
from json import dumps, loads
from pathlib import Path, PosixPath
from requests import post
from panapi import PanApiSession
from panapi.config.management import ConfigVersion
from panapi.config.network import BandwidthAllocation, IKEGateway, IPSecTunnel, Location, RemoteNetwork


### LOGGING SETUP ###
LOG_FILE = Path("logs/tunnel_provision.log")
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler(LOG_FILE)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

def auth(config_path:PosixPath) -> PanApiSession:
    """Authenticate Prisma

    Args:
    config_path (PosixPath): PANAPI configuration file

    Returns:
    session (PanApiSession obj): Session object
    """
    session = PanApiSession()
    session._configfile = config_path
    session.authenticate()
    
    return session

def create_ike_gw(session: PanApiSession, router_data: set) -> tuple[set, list]:
    """Create IKEA Gateway
    
    Args:
    session (PanApiSession): Session Object
    router_data (set): SDW Public IPs

    Returns:
    response (tuple): A set containing the response codes and a list of IKE Gateways names
    """
    response_code = set()
    ike_gws_names = []
    PRISMA_PSK = config("PRISMA_PSK")
    psk_dict = {"pre_shared_key": {"key": PRISMA_PSK}}
    protocol_var = {
				"version": "ikev2",
				"ikev2": {
					"ike_crypto_profile": "Cisco-ISR-IKE-Crypto",
					"dpd": {
						"enable": True
					}
				},
				"ikev1": {
					"dpd": {
						"enable": True
					}
				}
			}
    protocol_common_var = {"passive_mode": True}
		       
    for index, router in enumerate(router_data):
        peer_addr = {"ip": router[1]}
        ike_gw = IKEGateway(
            folder = "Remote Networks",
            name = f'IKE_GW_{router[0].upper().replace("-", "_")}_{index}',
            authentication = psk_dict,
            peer_address = peer_addr,
            protocol = protocol_var,
            protocol_common = protocol_common_var
        )
        ike_gw.create(session)
        print(f'IKE GW Creation for {router[0]} resulted in {session.response.status_code}')
        logger.info(f'Prisma: IKE GW Creation for {router[0]} resulted in {session.response.status_code}')
        response_code.add(session.response.status_code)
        ike_gws_names.append(f'IKE_GW_{router[0].upper().replace("-", "_")}_{index}')

    return response_code, ike_gws_names

def create_ipsec_tunnel(session: PanApiSession, ike_gws: list) -> tuple[set, list]:
    """"Create IPSec Tunnels 
    
    Args:
    session (PanApiSession): Session Object
    ike_gws (list): IKE Gateways names

    Returns:
    response (tuple): A set containing the response codes and a list of IPSec Tunnel names 
    """
    response_code = set()
    ipsec_tunnel_names = []
    for ike_gw in ike_gws:
        auto_key_dict = {"ike_gateway": [{"name": ike_gw}],"ipsec_crypto_profile": "Cisco-ISR-IPSec-Crypto"}
        ipsec_tunnel =  IPSecTunnel(
            folder = "Remote Networks",
            anti_replay = True,
            auto_key = auto_key_dict,
            name = f'IPSEC_TUN_{ike_gw.replace("IKE_GW_","")}'
            )
        ipsec_tunnel.create(session)
        print(f'IPSec Tunnel Creation for {ike_gw} resulted in {session.response.status_code}')
        logger.info(f'Prisma: IPSec Tunnel Creation for {ike_gw} resulted in {session.response.status_code}')
        response_code.add(session.response.status_code)
        ipsec_tunnel_names.append(f'IPSEC_TUN_{ike_gw.replace("IKE_GW_","")}')

    return response_code, ipsec_tunnel_names

def create_remote_nw(session: PanApiSession, site_id: str, spn_location: str, tunnel_names: list, region_id: str, networks: list) -> int:
    """ Create remote network & Tunnels 
    
    Args:
    session (PanApiSession): Session Object
    site_id (str): From frontend input
    spn_location (str): SPN location based on frontend input
    tunnel_names (list): List of IPSec tunnel names
    region_id (str): Region ID based on frontend input
    networks (list): Subnets to Advertise

    Returns:
    response (int): Status code of API Call 
    """
    if len(tunnel_names) > 1:
        primary_tunnel = tunnel_names[0]
        secondary_tunnel = tunnel_names[1]
    else:
        primary_tunnel = tunnel_names[0]
        secondary_tunnel = ""

    remote_network = RemoteNetwork(
    folder = "Remote Networks",
    license_type = "FWAAS-AGGREGATE",
    ecmp_load_balancing = "disable",
    name = site_id,
    region = region_id,
    spn_name = spn_location,
    ipsec_tunnel = primary_tunnel,
    secondary_ipsec_tunnel = secondary_tunnel,
    subnets = networks    
    )
    remote_network.create(session)
    print(f'Remote Network Creation for {site_id} resulted in {session.response.status_code}')
    logger.info(f'Prisma: Remote Network Creation for {site_id} resulted in {session.response.status_code}')
    response_code = session.response.status_code

    return response_code

def del_ike_gateways(session: PanApiSession, ike_gw_ids: list) -> set:
    """Delete IKE Gateways
    
    Args:
    session (PanApiSession): Session Object
    ike_gw_ids (list): IKE Gateway ids

    Returns:
    response (set): A set containing the response codes 
    """
    response_code = set()
    for ike_gw_id in ike_gw_ids:
        ike_gw_del = IKEGateway(
            id = ike_gw_id
        )
        print(f'Roll back: Deleting IKE Gateway {ike_gw_id}')
        logger.info(f'Prisma: Deleting IKE Gateway {ike_gw_id}')
        ike_gw_del.delete(session)
        response_code.add(session.response.status_code)
    
    return response_code

def del_ipsec_tunnels(session: PanApiSession, ipsec_tun_ids: list) -> set:
    """Delete IKE Gateways

    Args:
    session (PanApiSession): Session Object
    ipsec_tun_ids (list): IPSec Tunnel ids

    Returns:
    response (set): A set containing the response codes 
    """
    response_code = set()
    for ipsec_tun_id in ipsec_tun_ids:
        ipsec_tun_del = IPSecTunnel(
            id = ipsec_tun_id
        )
        print(f'Roll back: Deleting IPSec Tunnel {ipsec_tun_id}')
        logger.info(f'Prisma: Deleting IPSec Tunnel {ipsec_tun_id}')
        ipsec_tun_del.delete(session)
        response_code.add(session.response.status_code)
    
    return response_code

def get_ike_gateways(session: PanApiSession, ike_gws: list) -> list:
    """Get IKE Gateways 
    
    Args:
    session (PanApiSession): Session Object
    ike_gws (list): IKE Gateway names

    Returns:
    response (list): List of IKE Gateway dictionaries  
    """
    ike_gws_list = []
    for ike_gw in ike_gws:
        ike_gws = IKEGateway(
            folder = "Remote Networks",
            name = ike_gw
        )
        response = ike_gws.read(session)
        response_json =dumps(response.payload, indent=4)
        response_dict = loads(response_json)
        ike_gws_list.append(response_dict)

    return ike_gws_list

def get_ipsec_tunnels(session: PanApiSession, ipsec_tunnels: list) -> list:
    """Get IPSec Tunnels
    
    Args:
    session (PanApiSession): Session Object
    ipsec_tunnels (list): IPSec Tunnel names

    Returns:
    response (list): List of IPSec tunnels dictionaries  
    """
    ipsec_tuns_list = []
    for ipsec_tunnel in ipsec_tunnels:
        ipsec_tuns = IPSecTunnel(
            folder = "Remote Networks",
            name = ipsec_tunnel
        )
        response = ipsec_tuns.read(session)
        response_json =dumps(response.payload, indent=4)
        response_dict = loads(response_json)
        ipsec_tuns_list.append(response_dict)

    return ipsec_tuns_list

def get_public_ip(api_key: str) -> list:
    """
    Get Prisma Tunnel Endpoints

    Args:
    api_key (str): Prisma API Key

    Returns:
    response (list): List of Public IPs
    """
    url = "https://api.prod.datapath.prismaaccess.com/getPrismaAccessIP/v2"
    payload = dumps({
      "serviceType": "all",
      "addrType": "all",
      "location": "all"
    })
    headers = {
      'header-api-key': api_key,
      'Content-Type': 'application/json'
    }

    response = post(url, headers=headers, data=payload)
    response = loads(response.text)
    return response["result"] 

def get_region(session: PanApiSession) -> dict:
    """Get Region Name based on Location 
    
    Args:
    session (PanApiSession): Session Object

    Returns:
    response (dict): Region Locations
    """
    region_id = Location()
    response = region_id.read(session)

    return response

def get_remote_nws(session: PanApiSession, site_id: str) -> RemoteNetwork:
    """Get existing remote networks

    Args:
    session (PanApiSession): Session Object
    site_id (str): From frontend input

    Returns:
    response (RemoteNetwork Obj): Searched Remote Network
    """
    remote_networks = RemoteNetwork(
    folder = "Remote Networks",
    name = site_id

    )
    response = remote_networks.read(session)
    
    return response

def get_spn_location(session: PanApiSession, location: str) -> dict:
    """Get SPN based on Location 

    Args:
    session (PanApiSession): Session Object
    location (str): From frontend input

    Returns:
    response (dict): SPN Locations
    """
    location = location.lower().replace(" ","-")
    spn_location = BandwidthAllocation(
    name = location
    )
    response = spn_location.read(session)
    if response != None:
        response_json =dumps(response.payload, indent=4)
        response_dict = loads(response_json)
        return response_dict
    else:
        print("The location does not exist or no bandwidth has not been allocated to this region...")
        logger.error(f'Prisma: The location does not exist or no bandwidth has not been allocated to this region')
        return None

def push_config(session: PanApiSession) -> dict:
    """
    Push configuration to Panorama
    """
    push_config = ConfigVersion(
        folders = ["Remote Networks", "Service Connections"]
    )
    response = push_config.push(session)

    return response


