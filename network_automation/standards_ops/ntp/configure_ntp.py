#! /usr/bin/env python
"""
Delete and Configure AAA standard configurations
"""
from jinja2 import Environment, FileSystemLoader
import logging
from pathlib import Path
from yaml import load
from yaml.loader import FullLoader
from nornir import InitNornir
from nornir_scrapli.tasks import send_configs

### LOGGING SETUP ###
LOG_FILE = Path("logs/standards_ops.log")
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler(LOG_FILE)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


def ntp_send_config(task, dry_run=True):
    """ Nornir send config task

    Args:
    file (str): Commands file path
    """
    dev_file = task.host.hostname
    staging_dir = Path(f'network_automation/standards_ops/staging/{dev_file}') 
    
    ### CONVERT FILE TO LIST OF COMMANDS ###
    with open(staging_dir, "r+") as f:
        data = f.read()
        commands = data.split('\n')
    logger.info(f'Nornir: Sending config changes')
    task.run(task=send_configs, configs=commands, dry_run=dry_run)
    
def build_staging_file(ntp_dict: dict, host: str, gold_file: str):
    """Build the configuration staging file
    
    Args: 
    ntp_dict (dict): From user input
    platform (str): Device platform
    gold_file (str): Golden Config File Name

    Returns:
    Build staging file
    """

    ### VARS ###
    site_code = ntp_dict["site_code"]
    NTP_GOLD_CONFIG = Path(f'network_automation/standards_ops/ntp/templates/')
    AUDITS_DIR = Path(f'file_display/public/documentation/{site_code}/audits/')
    STAGING_DIR = Path(f'network_automation/standards_ops/staging/')
    
    ### WORK WITH JINJA2 TEMPLATES ###
    ### INPUT VARIABLES ORIGINATE FROM THE USER INPUT ###
    env = Environment(loader=FileSystemLoader(NTP_GOLD_CONFIG), trim_blocks=True, lstrip_blocks=True)
    ntp_template = env.get_template("ntp.j2")
    ntp_config = ntp_template.render(ntp_dict)
    
    with open(AUDITS_DIR / Path(f'{host}/ntp.yml')) as f:
        host_ntp = load(f, Loader=FullLoader)
        logger.info(f'Nornir: Loaded NTP device configuration')
    for _, value in host_ntp[host].items():
        with open(STAGING_DIR /  host, "a+") as stage:
            for line in value:
                stage.write(f"no {line}\n")
        logger.info(f'Nornir: Staged configuration to delete')
    with open(STAGING_DIR / host , "a+") as add_gold:
        add_gold.write(f'\n{ntp_config}')
        logger.info(f'Nornir: Staged configuration to configure')
    ### REMOVE SPACES ###
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

def ntp_operation(nr, ntp_dict: dict):
    """Run Nornir Tasks
    
    Args:
    nr (object): Nornir Object
    ntp_dict: From user input

    """

    ### VARS ### 
    failed_hosts = []
    dry_run = True
    results_set = set()

    ### BUILD PLATFORM CONFIGURATION FILE ###
    platform_hosts = nr.inventory.hosts
        
    for platform_host in platform_hosts.keys():
        platform_gold_file = "ntp.j2"
        build_staging_file(ntp_dict, platform_host, platform_gold_file)   
    
       ### APPLY CHANGES TO PLATFORM ###
    print("Apply Changes")
    platform_results = nr.run(ntp_send_config)

    ### HANDLE RESULTS FOR PLATFORM ###
    for key in platform_results.keys():
        if not platform_results[key][0].failed:
            dry_run = False
        else:
            failed_hosts.append(key)
            del_files()
            print(f'{key} Failed')
            logger.error(f'Nornir: Hosts Failed {failed_hosts}')
            results_set.add(True)
    print(f'Failed Hosts: {failed_hosts}')
    if not dry_run:
        platform_results = nr.run(ntp_send_config, dry_run=False)
        del_files()
        logger.info(f'Nornir: NTP configurations Applied')
        results_set.add(True)

    return results_set, failed_hosts


def replace_ntp(username: str, password: str, ntp_dict: dict):
    """Delete and configure NTP

    Args:
    username (str): From user input
    password (str): From user input
    ntp_dict (dict): From user input
    
    """   

    ### INITIALIZE NORNIR ###
    nr = InitNornir(
        config_file="network_automation/standards_ops/config/config.yml"
    )
    nr.inventory.defaults.username = username
    nr.inventory.defaults.password = password
    logger.info("Nornir: Session Initiated")

    results = ntp_operation(nr, ntp_dict)

    return results