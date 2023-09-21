#! /usr/bin/env python
"""
Define Child Access Device Class For NXOS Devices
"""
from scrapli.driver.core import NXOSDriver
from scrapli.exceptions import ScrapliConnectionError
from network_automation.libs.Device import Device


class DeviceNxos(Device):
    def set_hostname(self, hostname):
        """Send commands and structure them in a dictionary"""
        self.hostname = hostname
        command = f"hostname {hostname}"
        device = Device.set_transport(self, self.host, self.username, self.password)

        try:
            with NXOSDriver(**device) as connection:
                print(f"The new hostname is {command}")
                response = connection.send_config(command)
            return response.result
        
        except ScrapliConnectionError as e:
            print(f"Failed to Login: {e}")
