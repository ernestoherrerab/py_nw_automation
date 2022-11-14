#! /usr/bin/env python
"""
Nornir Operations
"""
import logging
from pathlib import Path
from nornir import InitNornir
from nornir_scrapli.tasks import send_command
from nornir.core.task import AggregatedResult


### LOGGING SETUP ###
LOG_FILE = Path("logs/standards_ops.log")
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler(LOG_FILE)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

def init_nornir(username: str, password: str, task_name) -> dict:
    """INITIALIZES NORNIR SESSIONS
    
    Args:
    username (str): From user input
    password (str): From user input
    task_name (task): Name of Nornir task to run

    Returns:
    output_dict (dict): JSON structured result output of task    
    """

    ### VARS ###
    output_dict = {}

    ### INITIALIZE NORNIR ###
    nr = InitNornir(
        config_file="network_automation/standards_ops/config/config.yml"
    )
    nr.inventory.defaults.username = username
    nr.inventory.defaults.password = password
    logger.info("Nornir: Session Initiated")
    
    ### RUN NORNIR TASK ###
    results = nr.run(task=task_name)
    logger.info(f'Nornir: Run Task {task_name}')

    ### FORMAT RESULTS IN JSON ###
    for result in results.keys():
        host = str(nr.inventory.hosts[result])
        logger.info(f'Nornir: Format Result for {host}')
        host_data = dict(nr.inventory.hosts[result])
        dict_values = list(host_data.values())
        output_dict[host] = dict_values[0]
          
    hosts_failed = list(results.failed_hosts.keys())
    if hosts_failed != []:
        auth_fail_list = list(results.failed_hosts.keys())
        for dev in auth_fail_list:
            logger.error(f'Nornir: Authentication failed for {dev}')
            print(f"Authentication Failed: {dev}")

    return output_dict

def get_version_task(task) -> AggregatedResult:
    """Task to send commands to Devices via Nornir/Scrapli

    Args:
    Not needed

    Returns:
    AggregatedResult(obj): In the form of genie parse output
    """
    command = "show version"
    logger.info(f'Nornir: Sending Command {command}')
    data_results = task.run(task=send_command, command=command)
    data = data_results.scrapli_response
    task.host[task.host.hostname] = data.genie_parse_output()
    
    

