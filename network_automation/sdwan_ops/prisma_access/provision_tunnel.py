#! /usr/bin/env python
"""
Script to Provision Prisma Access Tunnels
"""
from netaddr import IPAddress
import network_automation.sdwan_ops.ipfabric_api as ipfabric
import network_automation.sdwan_ops.prisma_api as prisma
import network_automation.sdwan_ops.sdwan_api as sdwan

def provision_tunnel(config, site_data, url_var, username, password):
    """ Main function to provision tunnels """

    site_id = site_data["site_id"].upper()
    location = site_data["location_id"]
    hostname_ip_list = set()

    ### GENERATE IPFABRIC SESSION ###
    print("Authenticating to IPFabric...")
    ipf_session = ipfabric.auth()

    ### RETRIEVE INTERFACE DATA FROM DEVICE ###
    print("Getting Public Interface Data of Site Routers...")
    filter_input = {"and": [{"hostname": ["reg",f'{site_id.lower()}-r\\d+-sdw']}]}
    dev_data = ipfabric.get_dev_data(ipf_session, filter_input)
    
    ### GET PUBLIC IPS FROM IPFABRIC DATA ###
    for interface in dev_data:
        if interface["primaryIp"] != None:
            ip =  IPAddress(interface["primaryIp"])
            if ip.is_unicast() and not ip.is_private():
                hostname_ip_list.add((interface["hostname"], interface["primaryIp"]))

    ### GENERATE PRISMA SESSION ###
    print("Authenticating to Prisma...")
    prisma_session = prisma.auth(config)

    ### CHECK IF SITE ALREADY EXISTS ###
    print("Checking if the remote network already exists in Prisma...")
    remote_network = prisma.get_remote_nws(prisma_session, site_id)

    if remote_network != None:
        print(remote_network)
        return "Site Already Exists"
    else:
        pass

    print(f'Getting SPN Location based on location entered: {location} ...')
    spn_location_dict = prisma.get_spn_location(prisma_session, location)
    if spn_location_dict == None:
        return False
    else:
        spn_location = spn_location_dict["spn_name_list"][0]

    print(f'Getting Region Name based on location entered: {location}')
    regions = prisma.get_region(prisma_session)
    for region in regions:
        if region["display"] == location:
            region_id = region["region"]

    ### CREATE IKE GATEWAY(S) ###
    print("Creating IKE Gateways in Prisma...")
    ike_gw_result, ike_gw_names = prisma.create_ike_gw(prisma_session, hostname_ip_list)
    if ike_gw_result != {201}:
        return False
    else:
        print("IKE Gateways Successfully Created!")

    ### CREATE IPSEC TUNNEL(S) ###
    print("Creating IPSEC Tunnels in Prisma...")
    ipsec_tun_result, ipsec_tun_names = prisma.create_ipsec_tunnel(prisma_session, ike_gw_names)
    if ipsec_tun_result != {201}:
        return False
    else:
        print("IPSec Tunnels Successfully Created!")
    
    ##### CREATE REMOTE NETWORK ###
    remote_network_result = prisma.create_remote_nw(prisma_session, site_id, spn_location, ipsec_tun_names, region_id)
    if remote_network_result != 201:
        return False
    else:
        print("Remote Network Successfully Created!")
        return True

#    ### VMANAGE AUTHENTICATION ###
#    auth_header = sdwan.auth(url_var, username, password)
#
#    ### VMANAGE GET DEVICE DATA ###
#    vedge_data_ops = "dataservice/system/device/vedges"
#    vedge_data = sdwan.get_dev_data(url_var, vedge_data_ops, auth_header)
#    return vedge_data

#    ### GET SPN LOCATION ###
#    location = prisma.get_spn_location(prisma_session, location)
#    ipsec_termination_node = location["spn_name_list"][0]
#
#    ### CREATE REMOTE NETWORK ###
#    tunnel_provision = prisma.create_remote_nw(prisma_session, site_id, location, ipsec_termination_node)


