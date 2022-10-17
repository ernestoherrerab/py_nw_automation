#! /usr/bin/env python
"""
IPFabric API Functions
"""
from decouple import config 
from ipfabric import IPFClient


def auth() -> IPFClient:
    """Authentication Function

    Returns: 
    ipf (IPFClient obj): Session object
    """

    IPFABRIC_URL = config("IPFABRIC_URL")
    IPFABRIC_TOKEN = config("IPFABRIC_TOKEN")
    ipf = IPFClient(IPFABRIC_URL, token=IPFABRIC_TOKEN, verify=False)
    
    return ipf 

def get_if_data(ipf: IPFClient, filter_dict: dict) -> list:
    """Get device interfaces data 

    Args:
    ipf (IPFClient obj): From Authentication
    filter_dict (dict): Dictionary to Filter Data  

    Returns:
    if_data (list): List of dictionaries of interface data  
    """    
    if_data = ipf.inventory.interfaces.all(filters=filter_dict)

    return if_data

def get_subnets_data(ipf: IPFClient, filter_dict: dict) -> list:
    """Get device interfaces data

    Args:
    ipf (IPFClient obj): From Authentication
    filter_dict (dict): Dictionary to Filter Data 

    Returns:
    subnets_data (list): List of dictionaries of routes data 
    """
    subnets_data = ipf.technology.routing.routes_ipv4.all(filters=filter_dict)
    
    return subnets_data