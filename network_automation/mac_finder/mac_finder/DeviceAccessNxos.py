#! /usr/bin/env python
"""
Define Child Access Device Class For NXOS Devices
"""
from scrapli.driver.core import NXOSDriver
from network_automation.mac_finder.mac_finder.Device import Device

class DeviceAccessNxos(Device):
    def get_data(self):
        """ Send commands and structure them in a dictionary
        """
        commands = ["show mac address-table", "show cdp neighbors detail", "show port-channel summary"]
        command_dict = {}
        device = Device.set_transport(self, self.host, self.username, self.password)

        with NXOSDriver(**device) as connection:
            response = connection.send_commands(commands)

        for output, command in zip(response, commands):
            command_dict[command.replace(" ","_")] = output.genie_parse_output()
        
        return command_dict 
        
    def mac_to_if(self,mac_add, vlan, output_dict):
        """ Get interface from MAC Address if it is the host port
            otherwise generate a new connection to the next switch 
        """
        vlan_num = vlan.replace("Vlan", "")
        for _, v in output_dict["show_mac_address-table"]["mac_table"]["vlans"][vlan_num]["mac_addresses"][mac_add]["interfaces"].items():
            interface = v["interface"]
        ### FIND THE PORTCHANNEL MEMBERS ###
        if "Port-channel" in interface:
            interface = output_dict["show_port_channel_summary"]["interfaces"][interface]["port_channel"]['port_channel_member_intfs']
        else:
            interface = [interface]
        #### CHECK THE CDP NEIGHBOR ###
        for neighbor_if in output_dict["show_cdp_neighbors_detail"]["index"].values():
            if interface[0] == neighbor_if["local_interface"]:
                neighbor_name = neighbor_if["device_id"]
                neighbor_name = neighbor_name.split(".")
                neighbor_name = neighbor_name[0]
                if neighbor_if["management_addresses"] != {}:
                    neighbor_ip = list(neighbor_if["management_addresses"].keys())
                    neighbor_ip = neighbor_ip[0]
                    neighbor_nos = neighbor_if["software_version"]
                    return neighbor_ip, neighbor_nos, neighbor_name
                elif neighbor_if["entry_addresses"] != {}:
                    neighbor_ip = list(neighbor_if["entry_addresses"].keys())
                    neighbor_ip = neighbor_ip[0]
                    neighbor_nos = neighbor_if["software_version"]
                    return neighbor_ip, neighbor_nos, neighbor_name
        neighbor_nos= None
        neighbor_name= None
        return interface[0], False, neighbor_name