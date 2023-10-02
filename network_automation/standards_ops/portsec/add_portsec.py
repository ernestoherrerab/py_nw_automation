#! /usr/bin/env python
"""
Apply NTP standard configurations
"""
from jinja2 import Environment, FileSystemLoader
import logging
from pathlib import Path
from rich import print as pprint
from nornir import InitNornir
from nornir.core.filter import F
from nornir_scrapli.tasks import send_configs
from nornir_utils.plugins.functions import print_result
from network_automation.libs import ipfabric_api as ipfabric
from network_automation.standards_ops import build_inventory as inventory

### LOGGING SETUP ###
LOG_FILE = Path("logs/standards_ops.log")
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler(LOG_FILE)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


def format_ipf_data(site_inventory: list) -> dict:
    """Formats site inventory data into a dictionary of switch ports grouped by hostname and VLAN.

    Args:
        site_inventory (list): A list of dictionaries containing site inventory data.

    Returns:
        dict: A dictionary where keys are hostnames, values are dictionaries with VLANs as keys
        and lists of switch ports as values.
    """

    ### VARS ###
    switchport_dict = {}

    ### BUILD SWITCHPORT FILTER ###
    switch_list = [{"hostname": ["eq", device["hostname"]]} for device in site_inventory if device["devType"] == "switch" or device["devType"] == "l3switch"]
    switchport_filter = {"and": [{"or": switch_list}, {"or": [{"mode": ["notlike", "trunk"]}]}]}

    ### GENERATE IPFABRIC SESSION ###
    print("Authenticating to IPFabric...")
    ipf_session = ipfabric.auth()
    logger.info("IPFabric: Authenticated")
    
    ### GET SWITCHPORT LIST ###
    switchport_list = ipfabric.get_switchports(ipf_session, switchport_filter)

    for host in switchport_list:
        hostname = host["hostname"]
        vlan = host["accVlan"]
        port = host["intName"]

        if hostname not in switchport_dict:
            switchport_dict[hostname] = {"ports" : [(port,vlan)]} 
        elif hostname in switchport_dict:
            switchport_dict[hostname]["ports"].append((port,vlan))

    return switchport_dict

def build_staging_file(switchport_data: dict, host: str):
    """Build the configuration staging file
    
    Args: 
    dhcp_data (dict): From user input
    platform (str): Device platform
    gold_file (str): Golden Config File Name

    Returns:
    Build staging file
    """

    ### VARS ###
    ACCESS_SWITCHPORT_GOLD_CONFIG = Path(f'network_automation/standards_ops/portsec/templates/')
    STAGING_DIR = Path(f'network_automation/standards_ops/staging/')
    
    ### WORK WITH JINJA2 TEMPLATES ###
    ### INPUT VARIABLES ORIGINATE FROM USER INPUT ###
    env = Environment(loader=FileSystemLoader(ACCESS_SWITCHPORT_GOLD_CONFIG), trim_blocks=True, lstrip_blocks=True)
    portsec_template = env.get_template("portsec.j2")
    portsec_config = portsec_template.render(port_dict = switchport_data[host])   
        
    with open(STAGING_DIR / host , "a+") as add_gold:
        add_gold.write(f'\n{portsec_config}')
        logger.info(f'Nornir: Staged configuration to configure')
#    #### REMOVE SPACES ###
    with open(STAGING_DIR / host) as filehandle:
        lines = filehandle.readlines()
    with open(STAGING_DIR / host, 'w') as filehandle:
        lines = filter(str.strip, lines)
        filehandle.writelines(lines)  

def portsec_send_config(task, dry_run=True):
    """ Nornir send config task

    Args:
    file (str): Commands file path
    """
    ### VARS ###
    dev_file = task.host
    staging_dir = Path(f'network_automation/standards_ops/staging/{dev_file}') 
    
    ### CONVERT FILE TO LIST OF COMMANDS ###
    with open(staging_dir, "r+") as f:
        data = f.read()
        commands = data.split('\n')
    logger.info(f'Nornir: Sending config changes')
    
    ### SEND CONFIG ###
    task.run(task=send_configs, configs=commands, dry_run=dry_run)

def del_files():
    """ Delete staging files 
    """
    
    staging_dir = Path("network_automation/standards_ops/staging/")
    try:
        for host_file in staging_dir.iterdir():
            try:
                Path.unlink(host_file)
            except Exception as e:
                print(e)
    except IOError as e:
        print(e)

def access_switchport_op(nr, switchport_data: dict):
    """Run Nornir Tasks
    
    Args:
    nr (object): Nornir Object
    dhcp_data: From user input

    """
    ### VARS ### 
    failed_hosts = []
    dry_run = True
    results_set = set()
    
    ### BUILD PLATFORM CONFIGURATION FILE ###
    platform_hosts = nr.inventory.hosts 
    print(platform_hosts)   
        
    for platform_host in platform_hosts.keys():
        build_staging_file(switchport_data, platform_host)   
    
    ### APPLY CHANGES TO PLATFORM ###
    print("Apply Changes")
    platform_results = nr.run(portsec_send_config)
    print_result(platform_results)
    
    ### HANDLE RESULTS FOR PLATFORM ###
#    for key in platform_results.keys():
#        print(key)
#        if not platform_results[key][0].failed:
#            dry_run = False
#        else:
#            failed_hosts.append(key)
#            del_files()
#            print(f'{key} Failed')
#            logger.error(f'Nornir: Hosts Failed {failed_hosts}')
#            results_set.add(False)
#    print(f'Failed Hosts: {failed_hosts}')
#
#    if not dry_run:
#        platform_results = nr.run(ib_helper_send_config, dry_run=False)
#        del_files()
#        logger.info(f'Nornir: IP Helper Address configurations Applied')
#        results_set.add(True)
#
#    return results_set, failed_hosts

def apply_portsec(site_code: str, username: str, password: str):
    """Build the inventory 

    Args:
    site_code (str) : From user input
    username (str) : From user input
    password (str) : From user input
    """
    ### VARS ###
    INV_DIR = Path("network_automation/standards_ops/inventory/hosts.yml")
    site_code = site_code.lower()
    NORNIR_CONFIG_FILE = Path("network_automation/standards_ops/config/config.yml")

    ### BUILD INVENTORY AND GET SITE INVENTORY ###
    site_inventory = inventory.build_inventory(site_code)

    ### FORMAT SWITCH & SWITCHPORT DATA FOR NORNIR ###
    switchport_data = format_ipf_data(site_inventory)
    
    ### INITIALIZE NORNIR ###
    nr = InitNornir(config_file = NORNIR_CONFIG_FILE)
    nr.inventory.defaults.username = username
    nr.inventory.defaults.password = password
    platform_devs = nr.filter(F(groups__contains="ios_devices"))
    logger.info("Nornir: Session Initiated")

    results = access_switchport_op(platform_devs, switchport_data)

