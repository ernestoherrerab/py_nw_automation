#! /usr/bin/env python
"""
Program to execute code
"""

from DeviceCore import DeviceCore
from pprint import pprint



ip_address = "10.45.110.19"

def create_devs():
    username = "adminehb"
    password = "3lM@t@d104574"
    dev_ip = "10.45.0.1"
    dev_dict = dict()

    ### CORE DEVICE ###
    dev_dict['core'] = DeviceCore(
        dev_ip,
        'ios'
    )
    dev_dict['core'].set_credentials(username, password)
    return dev_dict

def main():
    devices = create_devs()
    print(devices)
    #for _, device in devices.items():
    #    if not device.connect():
    #        print("Error Connecting!")
    #        continue
    #    facts = device.get_facts()
    #    pprint(facts)
    #    device.disconnect()

if __name__ == '__main__':
    main()
