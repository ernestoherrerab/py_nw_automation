#! /usr/bin/env python
"""
Script to find MAC addresses"""
import sys
sys.dont_write_bytecode = True
import re
from network_automation.mac_finder.mac_finder.DeviceCore import DeviceCore
from network_automation.mac_finder.mac_finder.DeviceAccess import DeviceAccess
from network_automation.mac_finder.mac_finder.DeviceAccessNxos import DeviceAccessNxos

def find_mac(hostname, host_ip, find_ip, username, password):
    """
    Searches for a MAC address based on a given IP.
    """
    ### VARIABLES ###
    host_type = re.findall(r'^\w+-([a-z]+|[A-Z]+)', hostname)
    host_type = host_type[0].lower()
    loop_break = True
 
    while loop_break == True:
        if host_type == "cs":
            core_dev = DeviceCore(host_ip, username, password)
            core_output = core_dev.get_data()
            mac_add, vlan = core_dev.arp_to_mac(core_output, find_ip)
            neighbor_ip, nos_type, neighbor_name = core_dev.mac_to_if(mac_add, vlan, core_output) 
            if neighbor_name == None:
                result = f"The MAC is found on interface {neighbor_ip} on switch {hostname}"
                print(f"The MAC is found on interface {neighbor_ip} on switch {hostname}")
                loop_break = False
                return result
            else:
                host_ip = neighbor_ip
                hostname = neighbor_name
                host_type = re.findall(r'^\w+-([a-z]+|[A-Z]+)', hostname)
                host_type = host_type[0].lower()
                if "NX-OS" in nos_type:
                    nos_type = "nxos"
                    print(f"Neighbor: {hostname}, NOS: {nos_type} is type: {host_type}")
                else:
                    nos_type = "ios"  
                    print(f"Neighbor: {hostname}, NOS: {nos_type} is type: {host_type}")
        elif nos_type =="nxos":
            access_dev = DeviceAccessNxos(host_ip, username, password)
            access_output = access_dev.get_data()
            neighbor_ip, nos_type, neighbor_name = access_dev.mac_to_if(mac_add, vlan, access_output)
            if neighbor_name == None:
                result = f"The MAC is found on interface {neighbor_ip} on switch {hostname}"
                print(f"The MAC is found on interface {neighbor_ip} on switch {hostname}")
                loop_break = False
                return result
            else:
                host_ip = neighbor_ip
                hostname = neighbor_name
                host_type = re.findall(r'^\w+-([a-z]+|[A-Z]+)', hostname)
                host_type = host_type[0].lower()
                if "NX-OS" in nos_type:
                    nos_type = "nxos"
                    print(f"Neighbor: {hostname}, NOS: {nos_type} is type: {host_type}")
                else:
                    nos_type = "ios"  
                    print(f"Neighbor: {hostname}, NOS: {nos_type} is type: {host_type}")
        elif nos_type == "ios":
            access_dev = DeviceAccess(host_ip, username, password)
            access_output = access_dev.get_data()
            neighbor_ip, nos_type, neighbor_name = access_dev.mac_to_if(mac_add, vlan, access_output)
            if neighbor_name == None:
                result = f"The MAC is found on interface {neighbor_ip} on switch {hostname}"
                print(f"The MAC is found on interface {neighbor_ip} on switch {hostname}")
                loop_break = False
                return result
            else:
                host_ip = neighbor_ip
                hostname = neighbor_name
                host_type = re.findall(r'^\w+-([a-z]+|[A-Z]+)', hostname)
                host_type = host_type[0].lower()
                if "NX-OS" in nos_type:
                    nos_type = "nxos"
                    print(f"Neighbor: {hostname}, NOS: {nos_type} is type: {host_type}")
                else:
                    nos_type = "ios"  
                    print(f"Neighbor: {hostname}, NOS: {nos_type} is type: {host_type}")