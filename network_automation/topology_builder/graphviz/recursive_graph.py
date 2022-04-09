#! /usr/bin/env python
"""
Script to graph cdp neighborships.
"""
import sys
from decouple import config
from pathlib import Path
import ipaddress
from nornir import InitNornir
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
    with tqdm(total=len(nr.inventory.hosts)) as progress_bar:
        results = nr.run(task=get_data_task, progress_bar=progress_bar)
    hosts_failed = list(results.failed_hosts.keys())
    if hosts_failed != []:
        auth_fail_list = list(results.failed_hosts.keys())
        for dev in auth_fail_list:
            dev_auth_fail_list.add(dev)
        print(f"Authentication Failed: {auth_fail_list}")
        print(
            f"{len(list(results.failed_hosts.keys()))}/{len(nr.inventory.hosts)} devices failed authentication..."
        )
    return nr, results, dev_auth_fail_list

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

def build_sites(results, nornir_session):
    """ Build site dictionary"""
    dict_output = {}
    for result in results.keys():
        host = str(nornir_session.inventory.hosts[result])
        site_id = host.split("-")
        site_id = site_id[0]
        dict_output[site_id] = {}
    return dict_output

def build_inventory(username, password):
    """Rebuild inventory file from CDP output on core switches"""

    ### PROGRAM VARIABLES ###
    DOMAIN_NAME_1 = config("DOMAIN_NAME_1")
    DOMAIN_NAME_2 = config("DOMAIN_NAME_2")
    output_dict = {}
    inv_path_file = (
        Path("network_automation/topology_builder/graphviz/inventory/") / "hosts.yml"
   )
    levels = 1

    while levels < 4:
        ### INITIALIZE NORNIR ###
        """
        Fetch sent command data, format results, and put them in a dictionary variable
        """
        print("Initializing connections to devices...")
        nr, results, _ = init_nornir(username, password)

        print("Parsing generated output...")
        ### CREATE SITE ID DICTIONARIES ###
        input_dict = build_sites(results, nr)

        ### REBUILD INVENTORY FILE BASED ON THE NEIGHBOR OUTPUT ###
        print(f"Rebuilding Inventory num: {levels}")
        for result in results.keys():
            host = str(nr.inventory.hosts[result])
            site_id = host.split("-")
            site_id = site_id[0]
            input_dict[site_id][host] = {}
            input_dict[site_id][host] = dict(nr.inventory.hosts[result])
            if input_dict[site_id][host] != {}:
                for index in input_dict[site_id][host]["show_cdp_neighbors_detail"][
                    "index"
                ]:
                    device_id = (
                        input_dict[site_id][host]["show_cdp_neighbors_detail"]["index"][
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
                            input_dict[site_id][host]["show_cdp_neighbors_detail"]["index"][
                                index
                            ]["management_addresses"].keys()
                        )
                    if (
                        "entry_addresses"
                        in input_dict[site_id][host]["show_cdp_neighbors_detail"]["index"][
                            index
                        ]
                    ):
                        device_ip = list(
                            input_dict[site_id][host]["show_cdp_neighbors_detail"]["index"][
                                index
                            ]["entry_addresses"].keys()
                        )
                    if (
                        "interface_addresses"
                        in input_dict[site_id][host]["show_cdp_neighbors_detail"]["index"][
                            index
                        ]
                    ):
                        device_ip = list(
                            input_dict[site_id][host]["show_cdp_neighbors_detail"]["index"][
                                index
                            ]["interface_addresses"].keys()
                        )
                    if device_ip:
                        device_ip = device_ip[0]
                    output_dict[device_id] = {}
                    output_dict[device_id]["hostname"] = device_ip
                    if (
                        "NX-OS"
                        in input_dict[site_id][host]["show_cdp_neighbors_detail"]["index"][
                            index
                        ]["software_version"]
                    ):
                        output_dict[device_id]["groups"] = ["nxos_devices"]
                    else:
                        output_dict[device_id]["groups"] = ["ios_devices"]
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
    
def graph_build(username, password):
    """ BUILD GRAPH FROM PARSED CDP DATA """

    ### FUNCTION VARIABLES ###
    diagrams_path = Path("network_automation/topology_builder/graphviz/diagrams/")
    cdp_tuples_list = []
    diagrams_file_list = []

    ### REBUILD THE INVENTORY ###
    build_inventory(username, password)

    ### INITIALIZE NORNIR AND GET CDP DATA ###
    print("Initializing connections to devices in FINAL inventory file...")
    nr, results, dev_auth_fail_list = init_nornir(username, password)

    ### PARSE DATA ###
    print("Parse data from FINAL Inventory")
    inv_dict_output = build_sites(results, nr)
    for result in results.keys():
        host = str(nr.inventory.hosts[result])
        site_id = host.split("-")
        site_id = site_id[0]
        inv_dict_output[site_id][host] = {}
        inv_dict_output[site_id][host] = dict(nr.inventory.hosts[result])

    ### CREATE TUPPLES LIST ###
    print("Generating Graph Data...")
    for site in inv_dict_output:
        cdp_tuple_list = []
        for host in inv_dict_output[site]:
            neighbor_tuple = ()
            if inv_dict_output[site][host] != {}:
                for index in inv_dict_output[site][host]["show_cdp_neighbors_detail"][
                    "index"
                ]:
                    neighbor = inv_dict_output[site][host]["show_cdp_neighbors_detail"][
                        "index"
                    ][index]["device_id"].split(".")
                    neighbor = neighbor[0]
                    hostname = host.split("(")
                    hostname = hostname[0]
                    neighbor_tuple = (hostname, neighbor)
                    cdp_tuple_list.append(neighbor_tuple)
        if cdp_tuple_list:
            cdp_tuples_list.append(cdp_tuple_list)
    
    """    
    Generate Graph
    """
    
    ### GENERATE GRAPH EDGES CDP NEIGHBORS ###
    print(f"Generating Diagrams...{diagrams_path}")
    for cdp_tuple in cdp_tuples_list:
        site_id = cdp_tuple[0][0].split("-")
        site_id = site_id[0]
        site_path = diagrams_path / f"{site_id}_site"
        diagrams_file_list.append(site_id + "_site")
        graph.gen_graph(f"{site_id}_site", cdp_tuple, site_path)
    del_files()
    return dev_auth_fail_list, diagrams_file_list


