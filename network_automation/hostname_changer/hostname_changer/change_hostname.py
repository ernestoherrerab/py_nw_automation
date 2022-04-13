#! /usr/bin/env python
"""
Script to graph cdp neighborships.
"""
import re
import sys
import urllib3
from decouple import config
from pathlib import Path
import ipaddress
from nornir import InitNornir
from nornir_scrapli.tasks import send_commands, send_config
from yaml import dump, load, SafeDumper
from yaml.loader import FullLoader
from tqdm import tqdm
import network_automation.hostname_changer.hostname_changer.api_calls as api
from network_automation.hostname_changer.hostname_changer.DeviceIos import DeviceIos
from network_automation.hostname_changer.hostname_changer.DeviceNxos import DeviceNxos

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
        config_file="network_automation/hostname_changer/hostname_changer/config/config.yml"
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

def load_hostnames():
    """
    Task to change hostnames via Nornir/Scrapli
    """
    ### VARIABLES ###
    inv_path_file = (
        Path("network_automation/hostname_changer/hostname_changer/inventory/") / "hosts.yml"
        )
    as_count = 1
    ap_count = 1
    dev_pairs = []

    ### LOAD INVENTORY FILE ###
    with open(inv_path_file) as f:
        inv_hosts = load(f, Loader=FullLoader)

     ### CAPTURE HOSTNAME INFO ###
    for hostname, parameters in inv_hosts.copy().items():
        host_site_id = re.findall(r"^(\w+)-", hostname)
        ip_address = parameters["hostname"]
        if host_site_id:
            host_site_id = host_site_id[0].lower()
            site_for_file = host_site_id
            host_type = re.findall(r"^\w+-([a-z]+|[A-Z]+)", hostname)
            if host_type:
                host_type = host_type[0].lower()
            host_num = re.findall(r"^\w+-(?:[a-z]+|[A-Z]+)(\d+)", hostname)
            if host_num:
                host_num = host_num[0]
            host_optional = re.findall(r"^\w+-(?:[a-z]+|[A-Z]+)\d+-(\w+)", hostname)
        elif hostname.startswith("sep"):
            inv_hosts.pop(hostname)

        ### EVALUATE DEVICES NAMING AND RECORD OLD AND NEW HOSTNAMES ###
        if host_type == "as" or host_type == "swn" and as_count < 10:
            new_host_type = "as0" + str(as_count)
            as_count += 1
            if host_optional:
                new_hostname = f"{host_site_id}-{new_host_type}-{host_optional[0]}"
                sw_pair = [hostname, new_hostname, ip_address]
                dev_pairs.append(sw_pair)
                inv_hosts[hostname]["new_hostname"] = new_hostname
            else:
                new_hostname = f"{host_site_id}-{new_host_type}"
                sw_pair = [hostname, new_hostname, ip_address]
                dev_pairs.append(sw_pair)
                inv_hosts[hostname]["new_hostname"] = new_hostname
        elif host_type == "as" or host_type == "swn" and as_count > 10:
            new_host_type = "as" + str(as_count)
            as_count += 1
            if host_optional:
                new_hostname = f"{host_site_id}-{new_host_type}-{host_optional[0]}"
                sw_pair = [hostname, new_hostname, ip_address]
                dev_pairs.append(sw_pair)
                inv_hosts[hostname]["new_hostname"] = new_hostname
            else:
                new_hostname = f"{host_site_id}-{new_host_type}"
                sw_pair = [hostname, new_hostname, ip_address]
                dev_pairs.append(sw_pair)
                inv_hosts[hostname]["new_hostname"] = new_hostname

        elif host_type == "ap" and ap_count < 10:       
            new_host_type = "ap0" + str(ap_count)
            inv_hosts[hostname]["groups"] = ["ap_devices"]
            ap_count += 1
            if host_optional:
                new_hostname = f"{host_site_id}-{new_host_type}-{host_optional[0]}"
                ap_pair = [hostname, new_hostname, ip_address]
                dev_pairs.append(ap_pair)
                inv_hosts[hostname]["new_hostname"] = new_hostname
            else:
                new_hostname = f"{host_site_id}-{new_host_type}"
                ap_pair = [hostname, new_hostname, ip_address]
                dev_pairs.append(ap_pair)
                inv_hosts[hostname]["new_hostname"] = new_hostname
        elif host_type == "ap" and ap_count > 10:       
            new_host_type = "ap" + str(ap_count)
            inv_hosts[hostname]["groups"] = ["ap_devices"]
            ap_count += 1
            if host_optional:
                new_hostname = f"{host_site_id}-{new_host_type}-{host_optional[0]}"
                ap_pair = [hostname, new_hostname, ip_address]
                dev_pairs.append(ap_pair)
                inv_hosts[hostname]["new_hostname"] = new_hostname
            else:
                new_hostname = f"{host_site_id}-{new_host_type}"
                ap_pair = [hostname, new_hostname, ip_address]
                dev_pairs.append(ap_pair)
                inv_hosts[hostname]["new_hostname"] = new_hostname

    build_file(f"{site_for_file}.txt", str(dev_pairs))

    return dev_pairs, inv_hosts, site_for_file

def del_files():
    """CLEANS UP HOSTS FILES"""

    host_file = Path("network_automation/hostname_changer/hostname_changer/inventory/hosts.yml")
    if host_file.exists():
        Path.unlink(host_file)

def build_file(filename, content):
    file_dir = Path("network_automation/hostname_changer/hostname_changer/host_references")
    file_path =file_dir / filename
    with open(file_path, "w+") as f:
        f.write(content)

def build_inventory(username, password):
    """Rebuild inventory file from CDP output on core switches"""

    ### PROGRAM VARIABLES ###
    DOMAIN_NAME_1 = config("DOMAIN_NAME_1")
    DOMAIN_NAME_2 = config("DOMAIN_NAME_2")
    input_dict = {}
    output_dict = {}
    inv_path_file = (
        Path("network_automation/hostname_changer/hostname_changer/inventory/") / "hosts.yml"
   )
    levels = 1

    while levels < 3:
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
    return site_id
    
def change_hostname(username, password):
    """ RENAME DEVICES FROM PARSED CDP DATA """
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    ### VARIABLES ###
    URL = config("PRIME_URL_VAR")
    prime_aps_list = []
    prime_put_aps = {}
    prime_put_aps["unifiedApDetailsDTO"] = {}
    put_results = set()
    PRIME_USERNAME = config("PRIME_USERNAME")
    PRIME_PASSWORD = config("PRIME_PASSWORD")

    ### BUILD THE INVENTORY ###
    build_inventory(username, password)

    ### INITIALIZE NORNIR AND GET CDP DATA ###
    dev_pairs, results, site_id = load_hostnames()

    ### GET APS FROM CISCO PRIME ###
    ap_get_call = api.get_operations("AccessPoints?.full=true&.maxResults=900&.firstResult=0", URL, "ehb", "s^J*3HeuE6smqg")
    for aps in ap_get_call["queryResponse"]["entity"]:
        if aps["accessPointsDTO"]["name"].startswith(site_id) or aps["accessPointsDTO"]["name"].startswith(site_id.upper()):
            old_ap_name = aps["accessPointsDTO"]["name"]
            ap_id = aps["accessPointsDTO"]["@id"]
            prime_aps = [old_ap_name, ap_id]
            prime_aps_list.append(prime_aps)

    ### RENAME HOSTS ###
    for device, parameters in results.items():
        if "new_hostname" in parameters:
            if parameters["groups"] == ["ios_devices"]:
                host_ip = parameters["hostname"]
                ios_dev = DeviceIos(host_ip, username, password)
                #ios_dev.set_hostname(parameters["new_hostname"])
            elif parameters["groups"] == ["nxos_devices"]:
                host_ip = parameters["hostname"]
                nxos_dev = DeviceNxos(host_ip, username, password)
                #nxos_dev.set_hostname(parameters["new_hostname"])
            elif parameters["groups"] == ["ap_devices"]:
                host_ip = parameters["hostname"]
                for prime_ap in prime_aps_list:
                    if device in prime_ap[0]:
                        prime_ap[0] = parameters["new_hostname"]
    for ap in prime_aps_list:
        prime_put_aps["unifiedApDetailsDTO"]["accessPointId"] = int(ap[1])
        prime_put_aps["unifiedApDetailsDTO"]["name"] = ap[0]
        print(f"Renaming {ap[0]}")
        put_result = api.put_operations("apService/accessPoint", prime_put_aps, URL, PRIME_USERNAME, PRIME_PASSWORD)
        put_results.add(put_result)
    return dev_pairs, put_results