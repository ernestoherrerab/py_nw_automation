#! /usr/bin/env python
"""
Nautobot API Functions
"""
from decouple import config 
import logging
from pathlib import Path
from pynautobot import api
import json

### LOGGING SETUP ###
LOG_FILE = Path("logs/nautobot_ops.log")
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler(LOG_FILE)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

def auth() -> api:
    """Authentication Function
    Args:

    Returns: 
    api (api obj): Session object
    """

    NATUTOBOT_URL = config("NAUTOBOT_URL")
    NAUTOBOT_TOKEN = config("NAUTOBOT_TOKEN")
    nautobot = api(url=NATUTOBOT_URL, token=NAUTOBOT_TOKEN)
    
    return nautobot

def get_devices(nautobot: api, **kwargs):
    """ Get all Devices
    """
    if not kwargs:
        devices_data = nautobot.dcim.devices.all()
    else:
        devices_data = nautobot.dcim.devices.get(**kwargs)
    
    return devices_data

def get_sites(nautobot: api, **kwargs):
    """ Get all Devices
    """
    if not kwargs:
        sites_data = nautobot.dcim.sites.all()
    else:
        sites_data = nautobot.dcim.sites.get(**kwargs)

    return sites_data