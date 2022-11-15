#! /usr/bin/env python
"""
Delete and Configure AAA standard configurations
"""
import logging
from pathlib import Path
from nornir_scrapli.tasks import send_configs_from_file
from yaml import dump, load
from yaml.loader import FullLoader
from nornir import InitNornir
from nornir.core.filter import F

### LOGGING SETUP ###
LOG_FILE = Path("logs/standards_ops.log")
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler(LOG_FILE)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


def aaa_send_config(task, dry_run=True):
    """ Nornir send config task

    Args:
    file (str): Commands file path
    """

    dev_file = task.host.hostname
    staging_dir = Path(f'network_automation/standards_ops/staging/{dev_file}') 
    staging_dir = str(staging_dir)
    logger.info(f'Nornir: Sending config changes')
    results = task.run(task=send_configs_from_file, file=staging_dir, dry_run=dry_run)
    logger.info(f'Nornir: Config resulted in {results}')
    
def build_staging_file(site_code: str, host: str, gold_file: str):
    """Build the configuration staging file
    
    Args: 
    site_code (str): From user input
    platform (str): Device platform
    gold_file (str): Golden Config File Name

    Returns:
    Build staging file
    """

    ### VARS ###
    AAA_GOLD_CONFIG = Path(f'network_automation/standards_ops/aaa/configs/')
    AUDITS_DIR = Path(f'file_display/public/documentation/{site_code}/audits/')
    STAGING_DIR = Path(f'network_automation/standards_ops/staging/')
    special_lines = ["console_0", "line_vty_0_15"]

    with open(AAA_GOLD_CONFIG / gold_file, "r+") as gold:
        gold_config = gold.read()
        logger.info(f'Nornir: Reading Gold Config for {host}')
    with open(AUDITS_DIR / Path(f'{host}/aaa.yml')) as f:
        host_aaa = load(f, Loader=FullLoader)
        logger.info(f'Nornir: Loaded AAA device configuration')
    for key, value in host_aaa[host].items():
        with open(STAGING_DIR /  host, "a+") as stage:
            if key not in special_lines:
                for line in value:
                    stage.write(f"no {line}\n")
            else:
                stage.write(f'\n{key.replace("_", " ")}\n')
                for line in value:
                    stage.write(f"no {line}\n")
        logger.info(f'Nornir: Staged configuration to delete')
    with open(STAGING_DIR / host , "a+") as add_gold:
        add_gold.write(f'\n{gold_config}')
        logger.info(f'Nornir: Staged configuration to configure')

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

def replace_aaa(username: str, password: str, site_code: str):
    """Delete and configure AAA

    Args:
    username (str): From user input
    password (str): From user input
    task_name (task): Name of Nornir task to run
    
    """
    ### INITIALIZE NORNIR ###
    dry_run = True
    failed_hosts = []
    nr = InitNornir(
        config_file="network_automation/standards_ops/config/config.yml"
    )
    nr.inventory.defaults.username = username
    nr.inventory.defaults.password = password
    logger.info("Nornir: Session Initiated")

    ### RUN NORNIR TASK ###
    ws2960s_devs = nr.filter(F(groups__contains="ws_c2960s"))
    logger.info(f'Nornir: Grouped 2960S devs')
    ws_c3560x_devs = nr.filter(F(groups__contains="ws_c3560x"))
    logger.info(f'Nornir: Grouped 3560x devs')
    ws2960s_hosts = ws2960s_devs.inventory.hosts
    ws_c3560x_hosts = ws_c3560x_devs.inventory.hosts
   
    ### BUILD 2960S CONFIGURATION FILE ###
    for ws2960_host in ws2960s_hosts.keys():
        ws2960s_gold_file = "ws_2960s.txt"
        build_staging_file(site_code, ws2960_host, ws2960s_gold_file)
    
    ### APPLY CHANGES TO 2960S ###
    ws2960s_results = ws2960s_devs.run(aaa_send_config)

    ### BUILD 3560X CONFIGURATION FILE ###
    for ws_c3560x_host in ws_c3560x_hosts.keys():
        ws_c3560x_gold_file = "ws_c3560x.txt"
        build_staging_file(site_code, ws_c3560x_host, ws_c3560x_gold_file)

    ### APPLY CHANGES TO 3560X ###
    ws3560x_results = ws_c3560x_devs.run(aaa_send_config)
    
    ### HANDLE RESLTS 3560X ###
    for key in ws3560x_results.keys():
        if not ws3560x_results[key][0].failed:
            dry_run = False
        else:
            failed_hosts.append(key)
            del_files()
            print(failed_hosts)
            logger.error(f'Nornir: Hosts Failed {failed_hosts}')
            print("Line 133")
            return False
    
    ### HANDLE RESLTS 2960S ###
    for key in ws2960s_results.keys():
        if not ws2960s_results[key][0].failed:
            dry_run = False
        else:
            failed_hosts.append(key)
            del_files()
            logger.error(f'Nornir: Hosts Failed {failed_hosts}')
            print("Line 141")
            return False
    print(f'Failed Hosts: {failed_hosts}')
    if not dry_run:
        ws3560x_results = ws_c3560x_devs.run(aaa_send_config, dry_run=False)
        ws2960s_results = ws2960s_devs.run(aaa_send_config, dry_run=False)
        del_files()
        logger.info(f'Nornir: AAA configurations Applied')
        print("Line 149")
        return True