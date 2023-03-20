#! /usr/bin/env python
"""
Get Data From IPFabric to produce a lifecycle report per site
"""
import csv
import datetime
import logging
import pandas 
from pathlib import Path
import re
import network_automation.ipfabric_api as ipfabric

### LOGGING SETUP ###
LOG_FILE = Path("logs/standards_ops.log")
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler(LOG_FILE)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

def build_xlsx(data, filename):
    """ Get data from IP Fabric and transform it to CSV

    Args:
    data (list): List of Dictionaries
    
    Returns
    Writes a CSV File
    """

    csv_location = Path(f"network_automation/lifecycle/archive")
    Path(csv_location).mkdir(exist_ok=True)
    keys = data[0].keys()

    with open(csv_location / (filename + ".csv"), 'w', newline='') as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(data)

    read_file = pandas.read_csv(csv_location / (filename + ".csv"))
    read_file.to_excel(csv_location / (filename + ".xlsx"), index = None, header=True)

def compare(latest: list, baseline: list):
    diff_list = []
    for i in latest + baseline:
        if i not in latest:
            i["status"] = "missing"
            diff_list.append(i)
        elif i not in baseline:
            i["status"] = "new discovery"
            diff_list.append(i)

    return diff_list


def build_lifecycle_report(xlsx, snapshot="$last"):
    """ Get Inventory and EoL Data from IP Fabric and Produce a report

    Args:
    file (str): Commands file path
    build (bool): If an excel needs to be build
    """

    ### GENERATE IPFABRIC SESSION ###
    print("Authenticating to IPFabric...")
    ipf_session = ipfabric.auth(snapshot=snapshot)
    logger.info("IPFabric: Authenticated")

    ### GET INVENTORY DATA ###
    inv_devs = ipfabric.get_inv_data(ipf_session)
    logger.info("IPFabric: Retrieved Inventory")

    ### GET STACK MEMBERS DATA ###
    stack_filter = {"and": [{"memberSn": ["empty", False]},{"or": [{"role": ["eq","member"]},{"role": ["eq","standby"]}]}]}
    stack_members = ipfabric.get_stack_members(ipf_session, stack_filter)
    for stack_member in stack_members:
        stack_member["snHw"] = stack_member.pop("memberSn")
    
    ### ADD STACK MEMBERS AND INVENTORY DEVS ###
    all_devs = inv_devs + stack_members

    ### FORMAT INVENTORY DATA ###
    device_serials = list({serial["snHw"] for serial in all_devs})
    dev_filter = list(map(lambda x: {"sn": ["like", x]}, device_serials))
    logger.info("IPFabric: Built Filter by PID SN")
    
    ### GET EOL DATA ###    
    eol_data = ipfabric.get_eol_data(ipf_session, {"and": [{"dscr": ["notlike","Stack"]},{"or": dev_filter}]})
        
    ### FORMAT DATES AND GROUP DEVICE TYPES ###
    for item in eol_data:
        if item["endSale"] != None:
            end_sale_date = datetime.datetime.fromtimestamp(item["endSale"]/1000)
            item["endSale"] = end_sale_date.strftime('%d/%m/%Y')
        if item["endMaintenance"] != None:
            end_maintenance_date = datetime.datetime.fromtimestamp(item["endMaintenance"]/1000)
            item["endMaintenance"] = end_maintenance_date.strftime('%d/%m/%Y')
        if item["endSupport"] != None:
            end_support_date = datetime.datetime.fromtimestamp(item["endSupport"]/1000)
            item["endSupport"] = end_support_date.strftime('%d/%m/%Y')
        if re.search(r'\w+-(as|AS|sw|SW)\S+', item["hostname"]) != None and "WISM" not in item["pid"]:
            item["type"] = "Access Switch"
            if "24" in item["pid"]:
                item["juniper_replacement"] = "EX4100-F-24P"
            elif "48" in item["pid"]:
                item["juniper_replacement"] = "EX4100-F-48P"
            else:
                item["juniper_replacement"] = "not applicable"
        elif re.search(r'\w+-(as|AS|sw|SW)\S+', item["hostname"]) != None and "WISM" in item["pid"]:
            item["type"] = "WISM Module"
            item["juniper_replacement"] = "unknown"
        elif re.search(r'\w+-(ds|cs)\S+', item["hostname"]) != None:
            item["type"] = "Core Switch"
            item["juniper_replacement"] = "EX4650-48Y-AFI"
        elif re.search(r'\w+-(wc|wlc|WC|WLC)\S+', item["hostname"]) != None:
            item["type"] = "Wireless Controller"
            item["juniper_replacement"] = 'not applicable'
        elif re.search(r'\w+-(r0|rtr|ron|rcrtr)\S+', item["hostname"]) != None:
            item["type"] = "Router"
            item["juniper_replacement"] = 'not applicable'
        elif re.search(r'\w+-(ap|AP)\S+', item["hostname"]) != None or re.search(r'(AP\d+)\S+', item["hostname"]) != None:
            item["type"] = "Access point"
            item["juniper_replacement"] = "AP32-WW"
        elif re.search(r'\w+-(fw)\S+', item["hostname"]) != None:
            item["type"] = "Firewall"
            item["juniper_replacement"] = 'not applicable'
        else:
            item["type"] = "Unknown"
            item["juniper_replacement"] = 'not applicable'


    ### BUILD EXCEL FILE ###
    if xlsx:
        build_xlsx(eol_data, 'eol_summary')
    else:
        return eol_data

def build_lifecycle_diff():
    """ Get Inventory and EoL Data from IP Fabric and Produce a report

    Args:
    file (str): Commands file path
    """

    ### GET SNAPSHOT DIFFERENTIAL ###
    baseline = build_lifecycle_report(False, "$lastLocked")
    latest = build_lifecycle_report(False)
    difference = compare(latest, baseline)
    build_xlsx(difference, "differential")

    