#! /usr/bin/env python
"""
Script to add MAC addres to correct identity group
"""
from decouple import config
import logging
from pathlib import Path
import os
import sys
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
from time import time, strftime, gmtime
import urllib3
from netaddr import EUI
from IseApi import Ise

def is_valid_mac_address(mac_address: str) -> str:
    """
    Check if a given string is a valid MAC address.

    Args:
        mac_address (str): The string to be checked as a MAC address.

    Returns:
        EUI or False: If the input is a valid MAC address, returns the EUI (Extended Unique Identifier) object representing the MAC address. 
        If the input is not a valid MAC address, returns False.
    """

    try:
        mac = EUI(mac_address)
        return mac
    except:
        return False

def main():
    """
    Main function to retrieve and process MAC address information from ISE.

    This function establishes an ISE session, retrieves active sessions, filters
    guest MAC addresses, retrieves MAC address information, and updates the 
    endpoint group for unknown MAC addresses.
    """
    
    ### LOGGING SETUP ###
    LOG_FILE = Path("logs/ise_ops.log")
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    file_handler = logging.FileHandler(LOG_FILE)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)  

    ### DISABLE WARNINGS ###
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    ### VARS ###
    ISE_URL = config("ISE_URL_VAR")
    ISE_URL_MONITORING = ISE_URL.replace(":9060","")
    ISE_AUTHENTICATION = config("ISE_AUTHENTICATION")
    ISE_GUEST_ENDPOINT_GROUP_ID = config("ISE_GUEST_ENDPOINT_GROUP_ID")
    mac_data = []
    

    ### INITIALIZE API OBJECT AND GET THE ACTIVE SESSIONS LIST ###
    start_time = time()
    ise_xml = Ise(ISE_AUTHENTICATION, "xml")
    logger.info(f'ISE Session Established.')
    active_list = ise_xml.get_operations("admin/API/mnt/Session/ActiveList", ISE_URL_MONITORING)
    logger.info(f'Active Sessions Retrieved.')

    ### FILTER GUEST MACS ### 
    guest_endpoint_list = [session["user_name"] for session in active_list["activeList"]["activeSession"] if "framed_ip_address" in session and "192.168" in session["framed_ip_address"] and is_valid_mac_address(session["user_name"])]
    logger.info(f'Active sessions filtered by guest networks')

    ### GET MAC ADDRESS INFORMATION FROM FILTERED MACS ###
    for mac in guest_endpoint_list:
        result = ise_xml.get_operations(f'admin/API/mnt/Session/MACAddress/{mac}', ISE_URL_MONITORING)
        mac_data.append(result["sessionParameters"])
    logger.info(f'Retrieved MAC address information for filtered active sessions.')

    macs_unknown = [mac["user_name"] for mac in mac_data if "endpoint_policy" in mac and "user_name" in mac and mac["endpoint_policy"] == "Unknown"]
    logger.info(f'MAC addresses filtered that belong to the "Unknown" Endpoint Group')

    ### INITIALIZE API OBJECT AND GET THE ACTIVE SESSIONS LIST ###
    ise_json = Ise(ISE_AUTHENTICATION)
    logger.info(f'New ISE Session Established.')

    ### ADD MAC ADDRESSES TO GUEST ENDPOINT GROUP ###
    for mac in macs_unknown:
        user_id = ise_json.get_operations(f'ers/config/endpoint/name/{mac}', ISE_URL)
        logger.info(f'Retrieved endpoint id for {mac}')
        payload = {"ERSEndPoint": {"name": mac, "mac": mac, "staticGroupAssignment": "true", "groupId": ISE_GUEST_ENDPOINT_GROUP_ID}}
        result = ise_json.put_operations(f'ers/config/endpoint/{user_id["ERSEndPoint"]["id"]}', ISE_URL, payload)
        if result == 200:
            logger.info(f'Updated FLS-Guest-Endpoint-PoC with {mac}')
        else:
            logger.error(f'Updating FLS-Guest-Endpoint-PoC with {mac} FAILED!')            
    
    end_time = time()
    execution_time = start_time - end_time
    print(f'The script took {execution_time} seconds to run')
    print(f'The script took {strftime("%H:%M:%S", gmtime(execution_time))} seconds to run')
    logger.info(f'The script took {execution_time} seconds to run')
    logger.info(f'The script took {strftime("%H:%M:%S", gmtime(execution_time))} seconds to run')

if __name__ == '__main__' :
    """
    The main execution block of the script.

    This block is executed only if the script is run directly (not imported as a module).
    It calls the main() function to start the process of retrieving and processing MAC address information from ISE.
    """
    main()