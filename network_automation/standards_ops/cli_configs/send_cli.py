#! /usr/bin/env python
"""
Send CLI Configurations from a file
"""
import logging
from pathlib import Path
from nornir import InitNornir
from nornir.core.filter import F
from nornir_utils.plugins.functions import print_result
from nornir_scrapli.tasks import send_configs

### LOGGING SETUP ###
LOG_FILE = Path("logs/standards_ops.log")
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler(LOG_FILE)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

def send_cli(username, password, filename):

    ### INITIALIZE NORNIR ###
    nr = InitNornir(
        config_file="network_automation/standards_ops/config/config.yml"
    )
    nr.inventory.defaults.username = username
    nr.inventory.defaults.password = password
    logger.info("Nornir: Session Initiated")

    ### VARS ### 
    failed_hosts = []
    dry_run = True
    results_set = set()

    ### CONVERT FILE TO LIST OF COMMANDS ###
    with open(filename, "r+") as f:
        data = f.read()
        commands = data.split('\n')
    
    ### FILTER HOSTS BY PLATFORM ###
    cli_devices = nr.filter(F(groups__contains="ios_devices"))
    logger.info(f'Nornir: Filtered IOS devices')

    logger.info(f'Nornir: Sending config changes')
    cli_results = cli_devices.run(task=send_configs, configs=commands, dry_run=dry_run)
    print_result(cli_results)
    
    ### HANDLE RESULTS FOR PLATFORM ###
    for key in cli_results.keys():
        if not cli_results[key][0].failed:
            dry_run = False
        else:
            failed_hosts.append(key)
            print(f'{key} hosts Failed')
            logger.error(f'Nornir: Hosts Failed {failed_hosts}')
            results_set.add(False)

    print(f'Failed Hosts: {failed_hosts}')
    
    if not dry_run:
        cli_results = cli_devices.run(task=send_configs, configs=commands, dry_run=False)
        print_result(cli_results)
        logger.info(f'Nornir: Sent configurations Applied')
        results_set.add(True)

    return results_set, failed_hosts