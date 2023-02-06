#! /usr/bin/env python
"""
Delete and Configure AAA standard configurations
"""
from jinja2 import Environment, FileSystemLoader
import logging
from pathlib import Path
from nornir import InitNornir
from nornir.core.filter import F
from nornir_scrapli.tasks import send_configs

### LOGGING SETUP ###
LOG_FILE = Path("logs/standards_ops.log")
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler(LOG_FILE)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

def ib_helper_send_config(task, dry_run=True):
    """ Nornir send config task

    Args:
    file (str): Commands file path
    """

    dev_file = task.host
    staging_dir = Path(f'network_automation/standards_ops/staging/{dev_file}') 
    
    ### CONVERT FILE TO LIST OF COMMANDS ###
    with open(staging_dir, "r+") as f:
        data = f.read()
        commands = data.split('\n')
    logger.info(f'Nornir: Sending config changes')
    
    task.run(task=send_configs, configs=commands, dry_run=dry_run)
    
def build_staging_file(dhcp_data: dict, host: str):
    """Build the configuration staging file
    
    Args: 
    dhcp_data (dict): From user input
    platform (str): Device platform
    gold_file (str): Golden Config File Name

    Returns:
    Build staging file
    """

    ### VARS ###
    INFOBLOX_HELPER_GOLD_CONFIG = Path(f'network_automation/standards_ops/infoblox_helper/templates/')
    STAGING_DIR = Path(f'network_automation/standards_ops/staging/')
    
    ### WORK WITH JINJA2 TEMPLATES ###
    ### INPUT VARIABLES ORIGINATE FROM USER INPUT ###
    env = Environment(loader=FileSystemLoader(INFOBLOX_HELPER_GOLD_CONFIG), trim_blocks=True, lstrip_blocks=True)
    ib_helper_template = env.get_template("ib_helper.j2")
    ib_helper_config = ib_helper_template.render(if_list = dhcp_data[host]) 
    
    
    with open(STAGING_DIR / host , "a+") as add_gold:
        add_gold.write(f'\n{ib_helper_config}')
        logger.info(f'Nornir: Staged configuration to configure')
    #### REMOVE SPACES ###
    with open(STAGING_DIR / host) as filehandle:
        lines = filehandle.readlines()
    with open(STAGING_DIR / host, 'w') as filehandle:
        lines = filter(str.strip, lines)
        filehandle.writelines(lines)  

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

def add_helper_op(nr, dhcp_data: dict):
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
        build_staging_file(dhcp_data, platform_host)   
    
    ### APPLY CHANGES TO PLATFORM ###
    print("Apply Changes")
    platform_results = nr.run(ib_helper_send_config)

    ### HANDLE RESULTS FOR PLATFORM ###
    for key in platform_results.keys():
        if not platform_results[key][0].failed:
            dry_run = False
        else:
            failed_hosts.append(key)
            del_files()
            print(f'{key} Failed')
            logger.error(f'Nornir: Hosts Failed {failed_hosts}')
            results_set.add(False)
    print(f'Failed Hosts: {failed_hosts}')

    if not dry_run:
        platform_results = nr.run(ib_helper_send_config, dry_run=False)
        del_files()
        logger.info(f'Nornir: IP Helper Address configurations Applied')
        results_set.add(True)

    return results_set, failed_hosts


def add_helper(username: str, password: str, dhcp_data: dict):
    """Delete and configure NTP

    Args:
    username (str): From user input
    password (str): From user input
        
    """   

    ### INITIALIZE NORNIR ###

    nr = InitNornir(
        config_file="network_automation/standards_ops/config/config.yml"
    )
    nr.inventory.defaults.username = username
    nr.inventory.defaults.password = password
    platform_devs = nr.filter(F(groups__contains="ios_devices"))
    logger.info("Nornir: Session Initiated")

    results = add_helper_op(platform_devs, dhcp_data)

    return results