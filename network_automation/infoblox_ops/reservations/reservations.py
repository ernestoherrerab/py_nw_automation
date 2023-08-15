#! /usr/bin/env python
"""
Script to add Reservations To Infoblox
"""
import csv
from decouple import config
import logging
from pathlib import Path
import urllib3
from network_automation.InfobloxApi import Infoblox

### LOGGING SETUP ###
LOG_FILE = Path("logs/infoblox_ops.log")
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler(LOG_FILE)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


def csv_to_dict(filename: str) -> dict:
    """
    Function to Convert CSV Data to YAML
    """
    with open(filename) as f:
        csv_data = csv.DictReader(f)
        data = [row for row in csv_data]
    return data

def add_reservation(filename) -> list:
    """Provision SDWAN Tunnels IPs

    Args:
    num_nws (list): Number of required networks
    site_data (dict): Frontend input data

    Returns 
    tunnel_ips_list (list): List of IP addresses to use for the SDWAN tunnels
    """
    ### DISABLE WARNINGS ###
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    ### VARS ###
    INFOBLOX_URL = config("INFOBLOX_URL")
    INFOBLOX_AUTHENTICATION = config("INFOBLOX_AUTHENTICATION")
    post_results = set()
    
    ### TRANSFORM CSV DATA TO DICT ###
    reservations_data = csv_to_dict(filename)
    print(reservations_data)

    #### INITIALIZE API OBJECT ###
    ib = Infoblox(INFOBLOX_AUTHENTICATION)
    
    #### CREATE RESERVATIONS ###
    new_reservation_params = {"_return_fields": "ipv4addr,mac", "_return_as_object": "1"}
    reservation_payload_list = list(map(lambda x: {"name": x["Name"], "comment": x["Comment"], "ipv4addr": x["IPAddress"], "mac": x["MACAddress"]}, reservations_data))
    print(reservation_payload_list)

    print("Adding Fixed Addresses to IPAM")
    for reservation_payload in reservation_payload_list:
        _, new_reservation = ib.post_operations("fixedaddress", INFOBLOX_URL, reservation_payload, params=new_reservation_params)
        post_results.add(new_reservation)
        logger.info(f'Infoblox: The result of adding a new fixed address was {new_reservation}')
        print(f'Infoblox: The result of adding a new fixed address was {new_reservation}')

    if post_results == {201}:
        return True, post_results
    else:
        return False, post_results