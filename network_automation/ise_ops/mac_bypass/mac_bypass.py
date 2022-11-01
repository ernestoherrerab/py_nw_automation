#! /usr/bin/env python
"""
Script to add MAC addresses to the ISE 
Guest MAB ID Group
"""
import sys
import csv
from decouple import config
import logging
from math import ceil
from pathlib import Path
import urllib3
import network_automation.ise_ops.api_calls as api

sys.dont_write_bytecode = True

### LOGGING SETUP ###
LOG_FILE = Path("logs/ise_ops.log")
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

def del_files():
    """ Delete CSV Files """
    csv_directory = Path("network_automation/ise_ops/mac_bypass/csv_data/")
    try:
        for hostname_file in csv_directory.iterdir():
            try:
                Path.unlink(hostname_file)
            except Exception as e:
                print(e)
    except IOError as e:
        print(e)

def mac_bypass(username, password, manual_data=None):
    """ Main Function"""
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    ### VARIABLES ###
    src_dir = Path("network_automation/ise_ops/mac_bypass/csv_data/")
    URL = config("ISE_URL_VAR")
    GUEST_MAB_ID = config("ISE_GUEST_MAB_ID")
    mac_list = []
    endpoint_list = []
    post_results = set()
    headers = {"Content-Type": "application/json", "Accept": "application/json"}

    ### EVALUATE IF DATA COMES FROM FILE OR MANUAL INPUT ###
    dir_contents = any(src_dir.iterdir())
    if dir_contents:
        logger.info(f'A CSV file has been input')
        for csv_file in src_dir.iterdir():
            mac_data = csv_to_dict(csv_file)
    elif not dir_contents:
        mac_data = manual_data
        logger.info(f'The manual data is {manual_data}')

    ### CONVERT CSV TO DICTIONARY ###
    for mac in mac_data:
        endpoint_data = {}
        endpoint_data["ERSEndPoint"] = {}
        mac_list.append(mac["mac_address"].upper())
        endpoint_data["ERSEndPoint"]["name"] = mac["mac_address"].upper()
        endpoint_data["ERSEndPoint"]["mac"] = mac["mac_address"].upper()
        endpoint_data["ERSEndPoint"]["staticGroupAssignment"] = "true"
        endpoint_data["ERSEndPoint"]["groupId"] = GUEST_MAB_ID
        logger.info(f'CSV Data transformed to {endpoint_data}')
 
        if mac["dev_type"] != "":
            print("Searching Device Type Profile ID...")
            logger.info(f'The Profile ID has been set to {mac["dev_type"]}')
            endpoint_data["ERSEndPoint"]["staticProfileAssignment"] = "true"
            profile_name = mac["dev_type"]
            profiles_data = api.get_operations(
                f"profilerprofile?filter=name.EQ.{profile_name}",
                URL,
                username,
                password,
            )
            logger.info(f'The profile data fetched: {profiles_data}')
            if profiles_data == 401:
                logger.error(f'The Profile data fetch failed.')
                del_files()
                return profiles_data

            for profile in profiles_data["SearchResult"]["resources"]:
                endpoint_data["ERSEndPoint"]["profileId"] = profile["id"]
                logger.info(f'The Profile ID is {profile["id"]}')
        endpoint_list.append(endpoint_data)

    ### GET ALL MACS IN THE GUEST-MAB GROUP TO REMOVE ALREADY EXISTING ENTRIES ###
    guest_mab = api.get_operations(
        f'endpoint?filter=groupId.EQ.{GUEST_MAB_ID}&size=100&page=1', URL, username, password
    )
    logger.info(f'Getting the first page of MACs in Guest MAB to check if entry exists')
    total_entries = guest_mab["SearchResult"]["total"]
    if total_entries > 100:
        pages = ceil(total_entries / 20) 
        for i in range(2, pages + 1):    
            sec_guest_mab = api.get_operations(
                f'endpoint?filter=groupId.EQ.{GUEST_MAB_ID}&page={i}', URL, username, password
            )
            guest_mab["SearchResult"]["resources"].extend(sec_guest_mab["SearchResult"]["resources"])
    if guest_mab == 401:
        del_files()
        return guest_mab
    guest_mab_members = guest_mab["SearchResult"]["resources"]
    for guest_mac in guest_mab_members:
        if guest_mac["name"].upper() in mac_list:
            logger.info(f'{guest_mac["name"]} exists already')
            print(f'{guest_mac["name"]} exists already...removing...')
            guest_mac_id = guest_mac["id"]
            api.del_operations(f"endpoint/{guest_mac_id}", URL, username, password)
            logger.info(f'Removing {guest_mac["name"]} to recreate')

    ### ADD ENDPOINTS  ###
    for endpoint in endpoint_list:
        mac_address = endpoint["ERSEndPoint"]["mac"]
        print(f'Adding MAC address {mac_address} to the Guest-MAB endpoint group')
        logger.info(f'Adding MAC address {mac_address} to the Guest-MAB endpoint group')
        post_result = api.post_operations("endpoint", endpoint, URL, username, password)    
        logger.info(f'The POST operation for {mac_address} resulted in {post_result}')  
        post_results.add(post_result)
    del_files()
    return post_results

def del_endpoints(username, password, manual_data=None):
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    ### VARIABLES ###
    src_dir = Path("network_automation/ise_mac_bypass/mac_bypass/csv_data/")
    URL = config("ISE_URL_VAR")
    GUEST_MAB_ID = config("ISE_GUEST_MAB_ID")
    mac_list = []
    del_results = set()

    ### EVALUATE IF DATA COMES FROM FILE OR MANUAL INPUT ###
    dir_contents = any(src_dir.iterdir())
    if dir_contents:
        for csv_file in src_dir.iterdir():
            filename = csv_file
            mac_data = csv_to_dict(filename)
            for mac_add in mac_data:
                mac = mac_add["MAC Address"]
                mac_list.append(mac)
    elif not dir_contents:
        mac_list = manual_data

    ### EVALUATE IF INPUT DATA EXISTS AND DELETE IT ###
    guest_mab = api.get_operations(
        f"endpoint?filter=groupId.EQ.{GUEST_MAB_ID}", URL, username, password
    )
    if guest_mab == 401:
        del_files()
        return guest_mab
    guest_mab_members = guest_mab["SearchResult"]["resources"]
    for guest_mac in guest_mab_members:
        if guest_mac["name"] in mac_list:
            print(f'{guest_mac["name"]} does exist...deleting...')
            guest_mac_id = guest_mac["id"]
            del_result = api.del_operations(
                f"endpoint/{guest_mac_id}", URL, username, password
            )
            del_results.add(del_result)
    del_files()
    return del_results
