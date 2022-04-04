#! /usr/bin/env python
"""
Define Access Device Class"""

import re
from DeviceCore import DeviceCore
from DeviceAccess import DeviceAccess
from DeviceAccessNxos import DeviceAccessNxos

def main():

    ### TMP VARIABLES ###
    find_ip = ""
    hostname = ""
    host_type = re.findall(r'^\w+-([a-z]+|[A-Z]+)', hostname)
    host_type = host_type[0].lower()
    host_ip = ""
    username = ""
    password = ""
    loop_break = True
    nos_type = ''
    mac_address =  ""
    vlan = ""


    if host_type == "cs":
        core_dev = DeviceCore(host_ip, username, password)
        core_output = core_dev.get_data()
        arp_output = core_dev.arp_to_mac(core_output, find_ip)
        mac_if = core_dev.mac_to_if(arp_output[0], arp_output[1], core_output)
        if mac_if[1] == False:
            print(f"The MAC is found on interface {mac_if[0]} on switch {hostname}")
        else:
            pass
    elif host_type == "as" and nos_type =="nxos":
        access_dev = DeviceAccessNxos(host_ip, username, password)
        access_output = access_dev.get_data()
        mac_if = access_dev.mac_to_if(mac_address, vlan, access_output)
    elif host_type == "as" and nos_type == "ios":
        access_dev = DeviceAccess(host_ip, username, password)
        access_output = access_dev.get_data()
        mac_if = access_dev.mac_to_if(mac_address, vlan, access_output)
        print(mac_if)
        

if __name__ == '__main__':
    main()
