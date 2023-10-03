#! /usr/bin/env python
"""
Define Parent Device Class
"""

class Device:
    ### CLASS ATTRIBUTES ###
    transport_options = {
        "open_cmd": [
            "-o",
            "KexAlgorithms=+diffie-hellman-group1-sha1,diffie-hellman-group14-sha1,diffie-hellman-group-exchange-sha1",
            "-o",
            "Ciphers=+aes256-cbc",
        ]
    }

    ### OBJECT INITIALIZATION ###
    def __init__(self, host, username, password):
        self.host = host
        self.username = username
        self.password = password

    ### OBJECT TRANSPORT OPTIONS ###
    def set_transport(self):
        DEVICE = {
            "host": self.host,
            "auth_username": self.username,
            "auth_password": self.password,
            "auth_strict_key": False,
            "transport_options": self.transport_options,
        }
        return DEVICE
