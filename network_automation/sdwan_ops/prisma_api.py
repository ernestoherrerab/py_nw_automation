#! /usr/bin/env python
"""
Prisma Access API Functions
"""
from decouple import config
from json import dumps, loads
from panapi import PanApiSession
from panapi.config.network import BandwidthAllocation, IKEGateway, IPSecTunnel, Location, RemoteNetwork

def auth(config_path):
    """ Authenticate Prisma"""

    session = PanApiSession()
    session._configfile = config_path
    session.authenticate()
    
    return session

def create_ike_gw(session, router_data):
    """ Create IKEA Gateway """

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
		       
    for router in router_data:
        peer_addr = {"ip": router[1]}
        ike_gw = IKEGateway(
            folder = "Remote Networks",
            name = f'IKE_GW_{router[0].upper().replace("-", "_")}',
            authentication = psk_dict,
            peer_address = peer_addr,
            protocol = protocol_var,
            protocol_common = protocol_common_var
        )
        ike_gw.create(session)
        print(f'IKE GW Creation for {router[0]} resulted in {session.response.status_code}')
        response_code.add(session.response.status_code)
        ike_gws_names.append(f'IKE_GW_{router[0].upper().replace("-", "_")}')

    return response_code, ike_gws_names

def create_ipsec_tunnel(session, ike_gws):
    """" Create IPSec Tunnels """
    
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
        response_code.add(session.response.status_code)
        ipsec_tunnel_names.append(f'IPSEC_TUN_{ike_gw.replace("IKE_GW_","")}')

    return response_code, ipsec_tunnel_names

def create_remote_nw(session, site_id, spn_location, tunnel_names, region_id, networks):
    """ Create remote network & Tunnels """

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
    response_code = session.response.status_code

    return response_code

def del_ike_gateways(session, ike_gw_ids):
    """ Delete IKE Gateways"""

    response_code = set()
    for ike_gw_id in ike_gw_ids:
        ike_gw_del = IKEGateway(
            id = ike_gw_id
        )
        print(f'Roll back: Deleting IKE Gateway {ike_gw_id}')
        ike_gw_del.delete(session)
        response_code.add(session.response.status_code)
    
    return response_code

def del_ipsec_tunnels(session, ipsec_tun_ids):
    """ Delete IKE Gateways"""

    response_code = set()
    for ipsec_tun_id in ipsec_tun_ids:
        ipsec_tun_del = IPSecTunnel(
            id = ipsec_tun_id
        )
        print(f'Roll back: Deleting IKE Gateway {ipsec_tun_id}')
        ipsec_tun_del.delete(session)
        response_code.add(session.response.status_code)
    
    return response_code


def get_ike_gateways(session, ike_gws):
    """ Get IKE Gateways """
    
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

def get_ipsec_tunnels(session, ipsec_tunnels):
    """ Get IPSec Tunnels """
    
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



def get_region(session):
    """ Get Region Name based on Location """

    region_id = Location()
    response = region_id.read(session)

    return response

def get_remote_nws(session, site_id):
    """ Test if a site exists"""

    remote_networks = RemoteNetwork(
    folder = "Remote Networks",
    name = site_id

    )
    response = remote_networks.read(session)
    
    return response

def get_spn_location(session, location):
    """ Get SPN based on Location """

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
        return None

