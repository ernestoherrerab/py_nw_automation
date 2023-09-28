#! /usr/bin/env python
"""
IPFabric API Functions
"""
from decouple import config 
from ipfabric import IPFClient


def auth(snapshot="$last") -> IPFClient:
    """Authentication Function
    Args:
    snapshot (str): snapshot id
    Options: "$last", "$prev", "$lastLocked" or UUID

    Returns: 
    ipf (IPFClient obj): Session object
    """

    IPFABRIC_URL = config("IPFABRIC_URL")
    IPFABRIC_TOKEN = config("IPFABRIC_TOKEN")
    ipf = IPFClient(IPFABRIC_URL, snapshot_id=snapshot, token=IPFABRIC_TOKEN, verify=False, timeout=15)
    
    return ipf 

def get_eol_data(ipf: IPFClient, filter_dict={}) -> list:
    """Get device interfaces data 

    Args:
    ipf (IPFClient obj): From Authentication
    filter_dict (dict): Dictionary to Filter Data  

    Returns:
    if_data (list): List of dictionaries of inventory data  
    """  
    columns_list = ["hostname", "siteName", "pid", "platform","sn", "vendor", "model", "endSale", "endMaintenance", "endSupport", "dscr", "replacement"]

    eol_data = ipf.inventory.eol_details.all(columns=columns_list, filters=filter_dict)
    
    return eol_data

def get_dhcp_relay_ifs(ipf: IPFClient, filter_dict={}) -> list:
    """Get device DHCP Relay data

    Args:
    ipf (IPFClient obj): From Authentication
    filter_dict (dict): Dictionary to Filter Data 

    Returns:
    subnets_data (list): List of dictionaries of DHCP Relays data 
    """

    
    dhcp_relay_ifs = ipf.technology.dhcp.relay_interfaces.all(filters=filter_dict)
    
    return dhcp_relay_ifs

def get_ntp_summary(ipf: IPFClient, filter_dict:dict={}) -> list:
    """Get device DHCP Relay data

    Args:
    ipf (IPFClient obj): From Authentication
    filter_dict (dict): Dictionary to Filter Data 

    Returns:
    ntp_sources (list): List of dictionaries of NTP Sources data 
    """

    
    ntp_sources = ipf.technology.management.ntp_summary.all(filters=filter_dict)
    
    return ntp_sources

def get_if_data(ipf: IPFClient, filter_dict:dict={}) -> list:
    """Get device interfaces data 

    Args:
    ipf (IPFClient obj): From Authentication
    filter_dict (dict): Dictionary to Filter Data  

    Returns:
    if_data (list): List of dictionaries of interface data  
    """    
    if_data = ipf.inventory.interfaces.all(filters=filter_dict)

    return if_data

def get_inv_data(ipf: IPFClient, filter_dict={}) -> list:
    """Get device interfaces data 

    Args:
    ipf (IPFClient obj): From Authentication
    filter_dict (dict): Dictionary to Filter Data  

    Returns:
    if_data (list): List of dictionaries of inventory data  
    """  
    columns_list = ["hostname", "siteName", "snHw", "loginIp", "vendor", "model", "image", "devType", "family"]
    inv_data = ipf.inventory.devices.all(columns=columns_list, filters=filter_dict)
    
    return inv_data

def get_mgmt_ips(ipf: IPFClient, filter_dict={}) -> list:
    """Get device management IP

    Args:
    ipf (IPFClient obj): From Authentication
    filter_dict (dict): Dictionary to Filter Data 

    Returns:
    mgmt_data (tuple): Tuple of device and IP 
    """
    mgmt_data = ipf.inventory.devices.all(filters=filter_dict)

    return mgmt_data

def get_snapshot_diff(ipf: IPFClient, snapshot: str) -> list:
    """Get snapshot differential

    Args:
    ipf (IPFClient obj): From Authentication
    filter_dict (dict): Dictionary to Filter Data 

    Returns:
    diff_data (list): List of Dictionaries 
    """

def get_stack_members(ipf: IPFClient, filter_dict={}) -> list:
    """Get switch stack members

    Args:
    ipf (IPFClient obj): From Authentication
    filter_dict (dict): Dictionary to Filter Data 

    Returns:
    stack_members (list): List of dictionaries
    
    """
    
    stack_members_data = ipf.technology.platforms.stacks_members.all(filters=filter_dict)
    
    return stack_members_data
    
def get_subnets_data(ipf: IPFClient, filter_dict:dict={}) -> list:
    """Get device interfaces data

    Args:
    ipf (IPFClient obj): From Authentication
    filter_dict (dict): Dictionary to Filter Data 

    Returns:
    subnets_data (list): List of dictionaries of routes data 
    """
    subnets_data = ipf.technology.routing.routes_ipv4.all(filters=filter_dict)
    
    return subnets_data