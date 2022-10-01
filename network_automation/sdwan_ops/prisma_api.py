#! /usr/bin/env python
"""
Prisma Access API Functions
"""
from decouple import config
from json import dumps, loads
from panapi import PanApiSession
from panapi.config.network import RemoteNetwork, BandwidthAllocation, IPSecTunnel, IKEGateway, Location

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

def create_remote_nw(session, site_id, spn_location, tunnel_names, region_id):
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
    subnets = ["172.16.0.0/24"]    
    )
    remote_network.create(session)
    print(f'Remote Network Creation for {site_id} resulted in {session.response.status_code}')
    response_code = session.response.status_code

    return response_code
    
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

