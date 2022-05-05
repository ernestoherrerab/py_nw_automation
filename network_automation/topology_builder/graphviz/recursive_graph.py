#! /usr/bin/env python
"""
Script to graph cdp neighborships.
"""
import sys
from decouple import config
from pathlib import Path
import ipaddress
from nornir import InitNornir
from nornir.core.filter import F
from nornir_scrapli.tasks import send_commands
from yaml import dump, load, SafeDumper
from yaml.loader import FullLoader
import network_automation.topology_builder.graphviz.graph_builder as graph
from tqdm import tqdm

sys.dont_write_bytecode = True
dev_auth_fail_list = set()

class NoAliasDumper(SafeDumper):
    """USED FOR ERROR HANDLING AND FORMATTING"""

    def ignore_aliases(self, data):
        return True

    def increase_indent(self, flow=False, indentless=False):
        return super(NoAliasDumper, self).increase_indent(flow, False)

def init_nornir(username, password):
    """INITIALIZES NORNIR SESSIONS"""

    nr = InitNornir(
        config_file="network_automation/topology_builder/graphviz/config/config.yml"
    )
    nr.inventory.defaults.username = username
    nr.inventory.defaults.password = password
    managed_devs = nr.filter(~F(groups__contains="unmanaged_devices"))
    
    with tqdm(total=len(managed_devs.inventory.hosts)) as progress_bar:
        results = managed_devs.run(task=get_data_task, progress_bar=progress_bar)

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

def get_data_task(task, progress_bar):
    """
    Task to send commands to Devices via Nornir/Scrapli
    """

    commands = ["show cdp neighbors detail"]
    data_results = task.run(task=send_commands, commands=commands)
    progress_bar.update()
    for data_result in data_results:
        for data, command in zip(data_result.scrapli_response, commands):
            task.host[command.replace(" ", "_")] = data.genie_parse_output()

def del_files():
    """CLEANS UP HOSTS FILES"""

    host_file = Path("network_automation/mac_finder/mac_finder/inventory/hosts.yml")
    if host_file.exists():
        Path.unlink(host_file)

def build_inventory(username, password, depth_levels):
    """Rebuild inventory file from CDP output on core switches"""

    ### PROGRAM VARIABLES ###
    DOMAIN_NAME_1 = config("DOMAIN_NAME_1")
    DOMAIN_NAME_2 = config("DOMAIN_NAME_2")
    input_dict = {}
    output_dict = {}
    inv_path_file = (
        Path("network_automation/topology_builder/graphviz/inventory/") / "hosts.yml"
   )
    levels = 1

    while levels < depth_levels:
        ### INITIALIZE NORNIR ###
        """
        Fetch sent command data, format results, and put them in a dictionary variable
        """
        print("Initializing connections to devices...")
        nr, results, _ = init_nornir(username, password)

        ### REBUILD INVENTORY FILE BASED ON THE NEIGHBOR OUTPUT ###
        print(f"Rebuilding Inventory num: {levels}")
        for result in results.keys():
            host = str(nr.inventory.hosts[result])
            if levels == 1:
                site_id = host.split("-")
                site_id = site_id[0]
            input_dict[host] = {}
            input_dict[host] = dict(nr.inventory.hosts[result])
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
                    ):
                        output_dict[device_id]["groups"] = ["unmanaged_devices"]
                    elif (
                        "IOS"
                        in input_dict[host]["show_cdp_neighbors_detail"]["index"][
                            index
                        ]["software_version"]
                    ):
                        output_dict[device_id]["groups"] = ["ios_devices"]
                    else:
                        output_dict[device_id]["groups"] = ["unmanaged_devices"]

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
    
def graph_build(username, password, depth_levels=3):
    """ BUILD GRAPH FROM PARSED CDP DATA """

    ### FUNCTION VARIABLES ###
    diagrams_path = Path("network_automation/topology_builder/graphviz/diagrams/")
    inv_dict_output = {}

    ### BUILD THE INVENTORY ###
    site_id = build_inventory(username, password, depth_levels)
    site_id = site_id + "_site"

    ### INITIALIZE NORNIR AND GET CDP DATA ###
    print("Initializing connections to devices in FINAL inventory file...")
    nr, results, dev_auth_fail_list = init_nornir(username, password)

    ### PARSE DATA ###
    print("Parse data from FINAL Inventory")
    for result in results.keys():
        host = str(nr.inventory.hosts[result])
        inv_dict_output[host] = {}
        inv_dict_output[host] = dict(nr.inventory.hosts[result])

    ### CREATE TUPPLES LIST ###
    print("Generating Graph Data...")    
    cdp_neigh_list = []
    for host in inv_dict_output:
        neighbor_list = []
        if inv_dict_output[host] != {}:
            for index in inv_dict_output[host]["show_cdp_neighbors_detail"][
                "index"
            ]:
                neighbor = inv_dict_output[host]["show_cdp_neighbors_detail"][
                    "index"
                ][index]["device_id"].split(".")
                neighbor = neighbor[0]
                hostname = host.split("(")
                hostname = hostname[0]
                neighbor_list = [hostname.lower(), neighbor.lower()]
                cdp_neigh_list.append(neighbor_list)

    """    
    Generate Graph
    """
    ### GENERATE GRAPH EDGES CDP NEIGHBORS ###
    site_path = diagrams_path / f"{site_id}"
    print(f"Generating Diagrams...{site_path}")
    graph.gen_graph(f"{site_id}", cdp_neigh_list, site_path)
    del_files()
    return dev_auth_fail_list, site_id


