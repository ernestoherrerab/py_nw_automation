#! /usr/bin/env python
"""
Define Child Core Device Class For IOS Devices
"""
from scrapli.exceptions import ScrapliAuthenticationFailed
from scrapli.driver.core import IOSXEDriver
from network_automation.hostname_changer.hostname_changer.Device import Device


class DeviceIos(Device):
    def set_hostname(self, hostname):
        """Send commands and structure them in a dictionary"""
        self.hostname = hostname
        command = f"hostname {hostname}"
        device = Device.set_transport(self, self.host, self.username, self.password)

        with IOSXEDriver(**device) as connection:
            response = connection.send_config(command)

        print(response.result)
        return response.result
