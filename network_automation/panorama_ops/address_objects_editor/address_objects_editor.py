#! /usr/bin/env python
"""
Edit address objects in Panorama
"""
from csv import DictReader
from decouple import config
import logging
from pathlib import Path
from panos.panorama import Panorama
from panos.objects import AddressObject

### LOGGING SETUP ###
LOG_FILE = Path("logs/panorama_ops.log")
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
        csv_data = DictReader(f)
        data = [row for row in csv_data]
    return data

def add_address_object(username, password, manual_data=None):
    """
    """

    ### VARS ###
    SRC_DIR = Path("network_automation/panorama_ops/address_objects_editor/csv_data/")
    PANORAMA_IP = config("PANORAMA_IP")

    ### EVALUATE IF DATA COMES FROM FILE OR MANUAL INPUT ###
    dir_contents = any(SRC_DIR.iterdir())
    if dir_contents:
        logger.info(f'A CSV file has been input')
        for csv_file in SRC_DIR.iterdir():
            add_obj_data = csv_to_dict(csv_file)
    elif not dir_contents:
        add_obj_data = manual_data
        logger.info(f'The manual data is {manual_data}')

    panorama = Panorama(PANORAMA_IP, username, password)

    for add_obj_dict in add_obj_data:
        address_object = AddressObject(
            add_obj_dict["obj_name"],
            add_obj_dict["obj_value"],
            add_obj_dict["obj_type"],
            add_obj_dict["obj_desc"])
        panorama.add(address_object)
        address_object.create()
        