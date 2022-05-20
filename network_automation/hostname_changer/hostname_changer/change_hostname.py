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
from nornir.core.filter import F
from nornir_scrapli.tasks import send_commands
from yaml import dump, load, SafeDumper
from yaml.loader import FullLoader
from tqdm import tqdm
import network_automation.hostname_changer.hostname_changer.api_calls as api
from network_automation.hostname_changer.hostname_changer.DeviceIos import DeviceIos
from network_automation.hostname_changer.hostname_changer.DeviceNxos import DeviceNxos
from network_automation.hostname_changer.hostname_changer.DeviceWlc import DeviceWlc

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
    managed_devs = nr.filter(F(groups__contains="ios_devices") | F(groups__contains="nxos_devices"))

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

def load_hostnames(site_id):
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
        if host_site_id:
            ip_address = parameters["hostname"]
            if host_site_id:
                host_site_id = host_site_id[0].lower()
                host_type = re.findall(r"^\w+-([a-z]+|[A-Z]+)", hostname)
                if host_type:
                    host_type = host_type[0].lower()
                host_num = re.findall(r"^\w+-(?:[a-z]+|[A-Z]+)(\d+)", hostname)
                if host_num:
                    host_num = int(host_num[0])
                host_optional = re.findall(r"^\w+-(?:[a-z]+|[A-Z]+)\d+-(\w+)", hostname)
        else:
            host_type = ""
            
        ### EVALUATE DEVICES NAMING AND RECORD OLD AND NEW HOSTNAMES ###
        ### EVALUATE ACCESS SWITCHES ###
        if host_type == "as" or host_type == "swn" or host_type == "switch":
            if as_count < 10:    
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
            elif as_count >= 10:
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
        ### EVALUATE APS ###
        elif host_type == "ap":    
            inv_hosts[hostname]["groups"] = ["ap_devices"] 
            if host_num < 10:
                new_host_type = "ap0" + str(host_num)
            else:
                new_host_type = "ap" + str(host_num)            
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
            print(f"The current AP is {hostname} and the new name is {new_hostname}")
        elif host_type == "apn" and ap_count < 10:   
            inv_hosts[hostname]["groups"] = ["ap_devices"] 
            new_host_type = "ap0" + str(ap_count)
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
        elif host_type == "apn" and ap_count >= 10:   
            inv_hosts[hostname]["groups"] = ["ap_devices"] 
            new_host_type = "ap" + str(ap_count)
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

        ### EVALUATE DEVICES WITH SITE_ID-OPTIONAL-DEVICE_TYPE FORMAT ###
        else:
            host_type = re.findall(r"^\w+-\w+-([a-z]+|[A-Z]+)", hostname)
            host_num = re.findall(r"^\w+-\w+-\w+(\d+)", hostname)
            host_optional = re.findall(r"^\w+-(\w+)", hostname)
            if host_type:
                host_type = host_type[0].lower()
            if host_num:
                host_num = int(host_num[0])
                if host_type == "as" or host_type == "swn" or host_type == "switch":
                    if as_count < 10:
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
                    elif as_count >= 10:
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

    build_file(f"{site_id}.txt", str(dev_pairs))

    return dev_pairs, inv_hosts

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

def build_inventory(username, password, depth_levels):
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
    
def change_hostname(username, password, depth_levels=3):
    """ RENAME DEVICES FROM PARSED CDP DATA """
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    ### VARIABLES ###
    URL = config("PRIME_URL_VAR")
    prime_aps_list = []
    prime_put_aps = {}
    prime_put_aps["unifiedApDetailsDTO"] = {}
    not_in_prime = False

    ### BUILD THE INVENTORY ###
    site_id = build_inventory(username, password, depth_levels)

    ### INITIALIZE NORNIR AND GET CDP DATA ###
    dev_pairs, results = load_hostnames(site_id)

    ### GET APS FROM CISCO PRIME ###
    ap_get_call = api.get_operations("AccessPoints?.full=true&.maxResults=900&.firstResult=0", URL, username, password)
    for aps in ap_get_call["queryResponse"]["entity"]:
        if aps["accessPointsDTO"]["name"].startswith(site_id + "-") or aps["accessPointsDTO"]["name"].startswith(site_id.upper() +"-"):
            old_ap_name = aps["accessPointsDTO"]["name"]
            ap_id = aps["accessPointsDTO"]["@id"]
            if "controllerIpAddress" in aps["accessPointsDTO"]:
                wlc_ip = aps["accessPointsDTO"]['controllerIpAddress']
                prime_aps = [old_ap_name, ap_id, wlc_ip]
                prime_aps_list.append(prime_aps)
                print(f"The WLC IP is {wlc_ip}")

    print(f"The initial Prime AP List is: {prime_aps_list}")

    ### RENAME HOSTS ###
    for device, parameters in results.items():
        if "new_hostname" in parameters:
            print(f'The device IP is: {parameters["hostname"]}')
            if parameters["groups"] == ["ios_devices"]:
                host_ip = parameters["hostname"]
                ios_dev = DeviceIos(host_ip, username, password)
                ios_dev.set_hostname(parameters["new_hostname"])
            elif parameters["groups"] == ["nxos_devices"]:
                host_ip = parameters["hostname"]
                nxos_dev = DeviceNxos(host_ip, username, password)
                nxos_dev.set_hostname(parameters["new_hostname"])
            elif parameters["groups"] == ["ap_devices"]:
                try:
                    wlc_ip = prime_aps_list[0][2]
                    print(wlc_ip)
                    for prime_ap in prime_aps_list:
                        old_ap_name = prime_ap[0].lower()
                        print(f"The device var is: {device} and the old ap var is: {old_ap_name}")
                        if device == old_ap_name:
                            prime_ap[1] = parameters["new_hostname"]
                            print(f"The current AP name is {prime_ap[0]} and it will change to {prime_ap[1]}")
                except IndexError as e:
                    print(f"APs not Found in Prime...: {e}")
                    not_in_prime = True

    if not_in_prime:
        print(f"APs cannot be updated programmatically")
        for dev in dev_pairs.copy():
            host_type = host_type = re.findall(r"^\w+-([a-z]+|[A-Z]+)", dev[0])
            host_type = host_type[0]
            if "ap" in host_type:
                dev_pairs.remove(dev)
    else:
        print(f"The Prime AP List to be implemented is: {prime_aps_list}")
        print(not_in_prime)
        wlc_dev = DeviceWlc(wlc_ip, username, password)
        wlc_dev.set_hostname(prime_aps_list)

    return dev_pairs, site_id
