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

def get_dev_data(ipf, filter_dict):
    """ Get device data """
    
    dev_data = ipf.inventory.interfaces.all(filters=filter_dict)

    return dev_data