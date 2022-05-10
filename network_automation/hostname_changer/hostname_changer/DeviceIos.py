#! /usr/bin/env python
"""
Define Child Core Device Class For IOS Devices
"""
from scrapli.driver.core import IOSXEDriver
from scrapli.exceptions import ScrapliConnectionError
from scrapli.exceptions import ScrapliAuthenticationFailed
from network_automation.hostname_changer.hostname_changer.Device import Device


class DeviceIos(Device):
    def set_hostname(self, hostname):
        """Send commands and structure them in a dictionary"""
        self.hostname = hostname
        command = f"hostname {hostname}"
        device = Device.set_transport(self, self.host, self.username, self.password)

        try:
            with IOSXEDriver(**device) as connection:
                print(f"The new hostname is {command}")
                response = connection.send_config(command)
            return response.result

        except ScrapliConnectionError as e:
            print(f"Failed to Login: {e}")

        except ScrapliAuthenticationFailed as e:
            print(f"Authentication Failed: {e}")


