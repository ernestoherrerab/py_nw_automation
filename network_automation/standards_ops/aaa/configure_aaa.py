#! /usr/bin/env python
"""
Delete and Configure AAA standard configurations
"""
import logging
from pathlib import Path
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


def delete_and_apply(task):
    task.run

def replace_aaa(username: str, password: str, input_list: list):
    """Delete and configure AAA

    Args:
    username (str): From user input
    password (str): From user input
    task_name (task): Name of Nornir task to run
    
    """
    ### VARS ###
    
    ### INITIALIZE NORNIR ###
    nr = InitNornir(
        config_file="network_automation/standards_ops/config/config.yml"
    )
    nr.inventory.defaults.username = username
    nr.inventory.defaults.password = password
    logger.info("Nornir: Session Initiated")

    ### RUN NORNIR TASK ###
    #results = nr.run(task=task_name)
    #logger.info(f'Nornir: Run Task {task_name}')
    ws2960_devs = nr.filter(F(groups__contains="ws_c2960s"))
    ws_c3560x_devs = nr.filter(F(groups__contains="ws_c3560x"))
    ws2960_hosts = ws2960_devs.inventory.hosts
    ws_c3560x_hosts = ws_c3560x_devs.inventory.hosts
    

