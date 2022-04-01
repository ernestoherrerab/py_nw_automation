#! /usr/bin/env python
"""
Script to Find MAC addresses at a particular site 
"""

import sys
sys.dont_write_bytecode = True
import re
from decouple import config
from nornir import InitNornir
from nornir_scrapli.tasks import send_commands
from pathlib import Path
from tqdm import tqdm
from yaml import dump,load, SafeDumper
from yaml.loader import FullLoader
from rich import print as rprint

dev_auth_fail_list = set()
username = "adminehb"
password = "3lM@t@d104574"
ip_address = "10.45.110.19"
inv_file = Path("network_automation/mac_finder/mac_finder/inventory/hosts.yml")
DOMAIN_NAME_1 = config("DOMAIN_NAME_1")
DOMAIN_NAME_2 = config("DOMAIN_NAME_2")

class NoAliasDumper(SafeDumper):
    """ USED FOR ERROR HANDLING AND FORMATTING """
    
    def ignore_aliases(self, data):
        return True
    def increase_indent(self, flow=False, indentless=False):
        return super(NoAliasDumper, self).increase_indent(flow, False)

def del_files():
    """ CLEANS UP HOSTS FILES """

    host_file = Path("network_automation/mac_finder/mac_finder/inventory/hosts.yml")
    if host_file.exists():
        Path.unlink(host_file)

def rebuild_inventory(neighbor, neighbor_ip, neighbor_nos):
    """ Rebuild inventory file from CDP output on core switches """
    output_dict = {}
    output_dict[neighbor] = {}
    output_dict[neighbor]["hostname"] = neighbor_ip
    if "NX-OS" in neighbor_nos:
        output_dict[neighbor]["groups"] = ["nxos_devices"]
    else:
        output_dict[neighbor]["groups"] = ["ios_devices"]
    yaml_inv = dump(output_dict, default_flow_style=False)
    with open(inv_file, "w+") as open_file:
        open_file.write("\n" + yaml_inv)
    

def init_nornir(username, password):
    """ INITIALIZES NORNIR SESSIONS """

    nr = InitNornir(config_file="network_automation/mac_finder/mac_finder/config/config.yml")
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
        print(f"{len(list(results.failed_hosts.keys()))}/{len(nr.inventory.hosts)} devices failed authentication...")
    return nr, results, dev_auth_fail_list

def get_data_task(task, progress_bar):
    """
    Task to send commands to Devices via Nornir/Scrapli
    """

    commands =["show ip arp", "show mac address-table", "show cdp neighbors detail", "show etherchannel summary"]
    data_results = task.run(task=send_commands, commands=commands)
    progress_bar.update()
    for data_result in data_results:
        for data, command in zip(data_result.scrapli_response, commands):
            task.host[command.replace(" ","_")] = data.genie_parse_output()

def arp_to_mac(arp_dict):
    for key in arp_dict["show_ip_arp"]["interfaces"].keys():
        for k,_ in arp_dict["show_ip_arp"]["interfaces"][key]["ipv4"]["neighbors"].items():
            if k == ip_address:
                mac_add = arp_dict["show_ip_arp"]["interfaces"][key]["ipv4"]["neighbors"][k]["link_layer_address"]
                vlan = key
    return mac_add, vlan

def find_mac(username, password, ip_address):
    ### INITIALIZE NORNIR ###
    """
    Fetch sent command data, format results, and put them in a dictionary variable
    """
    print("Initializing connections to devices...")
    nr, results, dev_auth_fail_list = init_nornir(username, password)

    ### GET NECESSARY DATA FROM DEVICES ###
    for result in results.keys():  
        output_dict = dict(nr.inventory.hosts[result])
        hostname = str(nr.inventory.hosts[result])
        host_type = re.re.findall(r'^\w+-([a-z]+|[A-Z]+)', hostname)
        host_type = host_type[0].lower()
    
    ### GET MAC ADDRESS AND VLAN FROM ARP TABLE ###
    if host_type == "cs":
        mac_add, vlan = arp_to_mac(output_dict)
    
    ### GET INTERFACE FROM MAC ADDRESS  ###
    vlan_num = vlan.replace("Vlan", "")
    for _, v in output_dict["show_mac_address-table"]["mac_table"]["vlans"][vlan_num]["mac_addresses"][mac_add]["interfaces"].items():
        interface = v["interface"]
    
    ### FIND THE PORTCHANNEL MEMBERS ###
    if "Port-channel" in interface:
        interface = output_dict["show_etherchannel_summary"]["interfaces"][interface]["port_channel"]['port_channel_member_intfs']
    else:
        pass  
    
    #### CHECK THE CDP NEIGHBOR ###
    for neighbor_if in output_dict["show_cdp_neighbors_detail"]["index"].values():
        #print(type(neighbor), neighbor)
        if interface[0] == neighbor_if["local_interface"]:
            neighbor = neighbor_if["device_id"]
            neighbor = neighbor.split(".")
            neighbor = neighbor[0]
            if neighbor_if["management_addresses"] != {}:
                neighbor_ip = list(neighbor_if["management_addresses"].keys())
                neighbor_ip = neighbor_ip[0]
                neighbor_nos = neighbor_if["software_version"]
            elif neighbor_if["entry_addresses"] != {}:
                neighbor_ip = list(neighbor_if["entry_addresses"].keys())
                neighbor_ip = neighbor_ip[0]
                neighbor_nos = neighbor_if["software_version"]
        else:
            neighbor = False
    if not neighbor:
        print("Final Switch")
        return neighbor
    else:
        rebuild_inventory(neighbor, neighbor_ip, neighbor_nos)
            

mac_found = find_mac(username, password, ip_address)
