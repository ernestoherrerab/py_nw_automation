#! /usr/bin/env python
"""
Delete and Configure AAA standard configurations
"""
import logging
from pathlib import Path
from nornir_scrapli.tasks import send_configs
from yaml import load
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
    
    ### CONVERT FILE TO LIST OF COMMANDS ###
    with open(staging_dir, "r+") as f:
        data = f.read()
        commands = data.split('\n')

    logger.info(f'Nornir: Sending config changes')
    task.run(task=send_configs, configs=commands, dry_run=dry_run)
    
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
    special_lines = ["line_console_0", "line_vty_0_15"]

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

def aaa_operation(nr, platforms: list, site_code: str):
    """Run Nornir Tasks
    """

    ### VARS ### 
    failed_hosts = []
    dry_run = True
    results_set = set()

    for platform in platforms:
        ### FILTER HOSTS BY PLATFORM ###
        platform_devs = nr.filter(F(groups__contains=platform))
        platform_hosts = platform_devs.inventory.hosts
        logger.info(f'Nornir: Grouped {platform} devs')

        ### BUILD PLATFORM CONFIGURATION FILE ###
        for platform_host in platform_hosts.keys():
            platform_gold_file = f'{platform}.txt'
            build_staging_file(site_code, platform_host, platform_gold_file)

       ### APPLY CHANGES TO PLATFORM ###
        print("Apply Changes")
        platform_results = platform_devs.run(aaa_send_config)

        ### HANDLE RESULTS FOR PLATFORM ###
        for key in platform_results.keys():
            if not platform_results[key][0].failed:
                dry_run = False
            else:
                failed_hosts.append(key)
                del_files()
                print(f'{platform} hosts Failed')
                logger.error(f'Nornir: {platform} Hosts Failed {failed_hosts}')
                results_set.add(False)
        print(f'Failed Hosts: {failed_hosts}')

        if not dry_run:
            platform_results = platform_devs.run(aaa_send_config, dry_run=False)
            del_files()
            logger.info(f'Nornir: AAA configurations Applied')
            results_set.add(True)

    return results_set, failed_hosts

def replace_aaa(username: str, password: str, site_code: str):
    """Delete and configure AAA

    Args:
    username (str): From user input
    password (str): From user input
    task_name (task): Name of Nornir task to run
    
    THE BELOW ARE THE SUPPORTED PLATFORMS 
    WS-C2960S, WS-C2960G, WS-C2960C, WS-C2960 (GROUPED)
    WS-C2960CPD, WS-C2960L, WS-C2960CX, WS-C2960X (GROUPED)
    WS-3750G, WS3750X (GROUPED)
    C9500, C9407R, C9410R, C9300, C9200 (GROUPED)
    WS-C3560CG & WS-C3560G, WS-C3560X, WS-C3560V2, WS-C3560E, WS-C3560 (GROUPED)
    WS-C3560CX
    WS-C4506, WS-C4510R (GROUPED)
    WS-C3650
    WS-C6509
    """
    ### VARS ###
    supported_platforms = ["ws_c2960s", "ws_c2960x", "ws_c3560x", "ws_c3750g", "c9200", "ws_c4510r", "ws_c3650",  "ws_c3560cx", "ws_c6509"]

    ### INITIALIZE NORNIR ###
    nr = InitNornir(
        config_file="network_automation/standards_ops/config/config.yml"
    )
    nr.inventory.defaults.username = username
    nr.inventory.defaults.password = password
    logger.info("Nornir: Session Initiated")

    results = aaa_operation(nr, supported_platforms, site_code)

    return results