#! /usr/bin/env python
"""
Get Data From IPFabric to produce a lifecycle report per site
"""
import csv
import datetime
import logging
import pandas 
from pathlib import Path
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

    read_file = pandas.read_csv (csv_location / (filename + ".csv"))
    read_file.to_excel (csv_location / (filename + ".xlsx"), index = None, header=True)

def build_lifecycle_report():
    """ Get Inventory and EoL Data from IP Fabric and Produce a report

    Args:
    file (str): Commands file path
    """

    ### GENERATE IPFABRIC SESSION ###
    print("Authenticating to IPFabric...")
    ipf_session = ipfabric.auth()
    logger.info("IPFabric: Authenticated")
    all_devs = ipfabric.get_inv_data(ipf_session)
    logger.info("IPFabric: Retrieved Inventory")

    ### FORMAT INVENTORY DATA ###
    device_models = list({serial["snHw"] for serial in all_devs})
    dev_filter = list(map(lambda x: {"sn": ["like", x]}, device_models))
    logger.info("IPFabric: Built Filter by PID SN")
    
    ### GET NEEDED DATA ###    
    eol_data = ipfabric.get_eol_data(ipf_session, {"or": dev_filter})
        
    ### FORMAT DATES ###
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

    ### BUILD CSV FILE ###
    build_xlsx(eol_data, 'eol_summary')
