#! /usr/bin/env python
"""
Script to discover neighbors and get running config
"""

import re
import sys
from decouple import config
from pathlib import Path
import ipaddress
from nornir import InitNornir
from nornir.core.filter import F
from nornir_napalm.plugins.tasks import napalm_get
from nornir_scrapli.tasks import send_commands
from nornir_utils.plugins.tasks.files import write_file
from yaml import dump, load, SafeDumper
from yaml.loader import FullLoader
from tqdm import tqdm

sys.dont_write_bytecode = True
dev_auth_fail_list = set()

class NoAliasDumper(SafeDumper):
    """USED FOR ERROR HANDLING AND FORMATTING"""

    def ignore_aliases(self, data):
        return True

    def increase_indent(self, flow=False, indentless=False):
        return super(NoAliasDumper, self).increase_indent(flow, False)

def init_nornir(username, password, task_name, site_id=""):
    """INITIALIZES NORNIR SESSIONS"""

    nr = InitNornir(
        config_file="network_automation/audit_manager/audit_manager/config/config.yml"
    )
    nr.inventory.defaults.username = username
    nr.inventory.defaults.password = password
    managed_devs = nr.filter(F(groups__contains="ios_devices") | F(groups__contains="nxos_devices"))

    with tqdm(total=len(managed_devs.inventory.hosts)) as progress_bar:
        results = managed_devs.run(task=task_name, progress_bar=progress_bar, site_id=site_id)
        
    hosts_failed = list(results.failed_hosts.keys())
    if hosts_failed != []:
        auth_fail_list = list(results.failed_hosts.keys())
        for dev in auth_fail_list:
            dev_auth_fail_list.add(dev)
        print(f"Authentication Failed: {auth_fail_list}")
        print(
            f"{len(list(results.failed_hosts.keys()))}/{len(managed_devs.inventory.hosts)} devices failed authentication..."
        )
    return managed_devs, results, dev_auth_fail_list

def get_cdp_data_task(task, progress_bar, site_id):
    """
    Task to send commands to Devices via Nornir/Scrapli
    """

    commands = ["show cdp neighbors detail"]
    data_results = task.run(task=send_commands, commands=commands)
    progress_bar.update()
    for data_result in data_results:
        for data, command in zip(data_result.scrapli_response, commands):
            task.host[command.replace(" ", "_")] = data.genie_parse_output()

def get_napalm_config(get_napalm_task, progress_bar, site_id=""):
    """Retrieve device running configuration and create a file """

    ### GET RUNNING CONFIGURATION ###
    site_path = Path(f"documentation/{site_id}/run_config/")
    napalm_getters = ['config']
    hostname = get_napalm_task.host.hostname
    dev_dir = site_path / hostname
    napalm_run = get_napalm_task.run(task=napalm_get, getters=[napalm_getters[0]])
    progress_bar.update()
    print(hostname  + ': Retrieving Running configuration...' + str(dev_dir))
    get_napalm_task.run(task=write_file, content=napalm_run.result['config']['running'],
                            filename="" + str(dev_dir))

def build_inventory(username, password, depth_levels):
    """Rebuild inventory file from CDP output on core switches"""

    ### PROGRAM VARIABLES ###
    DOMAIN_NAME_1 = config("DOMAIN_NAME_1")
    DOMAIN_NAME_2 = config("DOMAIN_NAME_2")
    input_dict = {}
    output_dict = {}
    inv_path_file = (
        Path("network_automation/audit_manager/audit_manager/inventory/") / "hosts.yml"
   )
    levels = 1

    while levels < depth_levels:
        ### INITIALIZE NORNIR ###
        """
        Fetch sent command data, format results, and put them in a dictionary variable
        """
        print("Initializing connections to devices...")
        nr, results, _ = init_nornir(username, password, get_cdp_data_task)

        ### REBUILD INVENTORY FILE BASED ON THE NEIGHBOR OUTPUT ###
        print(f"Rebuilding Inventory num: {levels}")
        for result in results.keys():
            host = str(nr.inventory.hosts[result])
            if levels == 1:
                site_id = host.split("-")
                site_id = site_id[0]
            input_dict[host] = {}
            input_dict[host] = dict(nr.inventory.hosts[result])
            try:
                if input_dict[host] != {}:
                    for index in input_dict[host]["show_cdp_neighbors_detail"][
                        "index"
                    ]:
                        device_id = (
                            input_dict[host]["show_cdp_neighbors_detail"]["index"][
                                index
                            ]["device_id"]
                            .lower()
                            .replace(DOMAIN_NAME_1, "")
                            .replace(DOMAIN_NAME_2, "")
                            .split("(")
                        )
                        device_id = device_id[0]
                        if "management_addresses" != {}:
                            device_ip = list(
                                input_dict[host]["show_cdp_neighbors_detail"]["index"][
                                    index
                                ]["management_addresses"].keys()
                            )
                        if (
                            "entry_addresses"
                            in input_dict[host]["show_cdp_neighbors_detail"]["index"][
                                index
                            ]
                        ):
                            device_ip = list(
                                input_dict[host]["show_cdp_neighbors_detail"]["index"][
                                    index
                                ]["entry_addresses"].keys()
                            )
                        if (
                            "interface_addresses"
                            in input_dict[host]["show_cdp_neighbors_detail"]["index"][
                                index
                            ]
                        ):
                            device_ip = list(
                                input_dict[host]["show_cdp_neighbors_detail"]["index"][
                                    index
                                ]["interface_addresses"].keys()
                            )
                        if device_ip:
                            device_ip = device_ip[0]
                        output_dict[device_id] = {}
                        output_dict[device_id]["hostname"] = device_ip
                        if (
                            "NX-OS"
                            in input_dict[host]["show_cdp_neighbors_detail"]["index"][
                                index
                            ]["software_version"]
                        ):
                            output_dict[device_id]["groups"] = ["nxos_devices"]
                        elif (
                            input_dict[host]["show_cdp_neighbors_detail"]["index"][
                                index
                            ]["capabilities"] == "Trans-Bridge Source-Route-Bridge IGMP"
                            or
                            input_dict[host]["show_cdp_neighbors_detail"]["index"][
                                index
                            ]["capabilities"] == "Trans-Bridge"

                        ):
                            output_dict[device_id]["groups"] = ["ap_devices"]
                        elif (
                            "IOS"
                            in input_dict[host]["show_cdp_neighbors_detail"]["index"][
                                index
                            ]["software_version"]
                        ):
                            output_dict[device_id]["groups"] = ["ios_devices"]
                        else:
                            output_dict[device_id]["groups"] = ["unmanaged_devices"]
            except TypeError as e:
                print(e)

        for key, _ in output_dict.copy().items():
            if output_dict[key]["hostname"] != []:
                ip_address = ipaddress.IPv4Address(output_dict[key]["hostname"])
                if ip_address.is_global:
                    output_dict.pop(key, None)
            else:
                output_dict.pop(key, None)

        ### BUILDING INVENTORY FILE ###
        with open(inv_path_file) as f:
            inv_dict = load(f, Loader=FullLoader)
        inv_tmp = {**output_dict, **inv_dict}
        yaml_inv = dump(inv_tmp, default_flow_style=False)
        with open(inv_path_file, "w+") as open_file:
            open_file.write("\n" + yaml_inv)
        levels += 1    
    return site_id

def get_config(username, password, depth_levels=3):

    ### VARIABLES ###
    host_list = []

    ### BUILD THE INVENTORY ###
    site_id = build_inventory(username, password, depth_levels)
    #site_id = "mad"
    site_path = Path(f"documentation/{site_id}/run_config/")
       
    ### INITIALIZE NORNIR ###
    ### GET RUNNING CONFIGURATION ###
    print("Initializing connections to devices...")
    init_nornir(username, password, get_napalm_config, site_id)

    """ Parse Running Configuration Outputs into Dictionaries """
    ### GET RUNNING CONFIGURATIONS PER HOST AND TRANSFER TO AN OBJECT ###
    for hostname_dir in site_path.iterdir():
        host_tuple = ()
        hostname = str(hostname_dir).replace(str(site_path), "")
        host_tuple = (hostname.replace("/", ""), hostname_dir)
        host_list.append(host_tuple)
    
    return host_list

