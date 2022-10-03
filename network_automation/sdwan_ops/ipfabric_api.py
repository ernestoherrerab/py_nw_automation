#! /usr/bin/env python
"""
IPFabric API Functions
"""
from decouple import config 
from ipfabric import IPFClient


def auth():
    """ Authentication Function"""

    IPFABRIC_URL = config("IPFABRIC_URL")
    IPFABRIC_TOKEN = config("IPFABRIC_TOKEN")
    ipf = IPFClient(IPFABRIC_URL, token=IPFABRIC_TOKEN, verify=False)
    
    return ipf 

def get_if_data(ipf, filter_dict):
    """ Get device interfaces data """
    
    if_data = ipf.inventory.interfaces.all(filters=filter_dict)

    return if_data

def get_subnets_data(ipf, filter_dict):
    """ Get device interfaces data"""
    
    subnets_data = ipf.technology.routing.routes_ipv4.all(filters=filter_dict)
    
    return subnets_data
    