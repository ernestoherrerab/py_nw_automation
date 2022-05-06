#! /usr/bin/env python
"""
Define Child WLC Device Class
"""
#import logging
from decouple import config
from scrapli.driver import GenericDriver
from network_automation.hostname_changer.hostname_changer.Device import Device

### VARIABLES FOR NON-AAA WLCS ###
WLC_LOCAL_USERNAME = config("WLC_LOCAL_USERNAME")
WLC_LOCAL_PASSWORD = config("WLC_LOCAL_PASSWORD")
UNSUPPORTED_WLCS = [config("UNSUPPORTED_WLC_1"), config("UNSUPPORTED_WLC_2")]

### ENABLE LOGGING ###
#logging.basicConfig(filename="scrapli.log", level=logging.DEBUG)
#logger = logging.getLogger("scrapli")

def wlc_on_open(cls):
    """ Function to handle WLCs login process"""

    cls.channel.write(cls.auth_username)
    cls.channel.send_return()
    cls.channel.write(cls.auth_password)
    cls.channel.send_return()

class DeviceWlc(Device):
    """ Create a WLC Object """
    def set_hostname(self, ap_list):
        """Send commands and structure them in a dictionary"""
        self.ap_list = ap_list
        commands = []
        for ap in self.ap_list:
            commands.append(f"config ap name {ap[1]} {ap[0]} ")
        device = Device.set_transport(self, self.host, self.username, self.password)
        if self.ap_list[0][2] in UNSUPPORTED_WLCS:
            device["auth_username"] = WLC_LOCAL_USERNAME 
            device["auth_password"] = WLC_LOCAL_PASSWORD
        device["auth_bypass"] = True
        device["on_open"] = wlc_on_open
        device["comms_prompt_pattern"] =  r"^.+ >$"

        ### INITIATE CONNECTION TO WLC AND SEND CONFIGURATIONS ###
        conn = GenericDriver(**device)
        conn.open()
        print(conn.get_prompt())
        conn.send_commands(commands)
        conn.close()
