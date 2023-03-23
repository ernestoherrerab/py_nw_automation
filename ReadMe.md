
# Network Automation Frontend

## Here you will find different network applications

- Network Infrastructure Links - Is just a collection of links used by the team.

- Site Documentation - This a repository of all site files collected through the different apps, and are available for download.

- Standards Ops  
  1. Audit Manager - Used to create configurations as code.
  2. Apply AAA - Used to standardize AAA configs.
  3. Apply NTP - Used to standardize NTP configs.
  4. Add Infoblox Relay - Used to add the Infoblox Helper Address

- Hostname Changer - Used to update hostnames for network devices (switches and APs) (Dephased).

- ISE MAC Bypass: adds MAC addresses to a bypass list for guest users in ISE.

- MAC Finder: Helps you find a MAC address at a site.

- SDWAN Ops: Contains different tasks to automate the SDWAN environment:

  1. SDWAN hostname update hostname (deprecated)
  2. Orchestration of Prisma Access and SDWAN Routers IPSec tunnels provisioning.

- Panorama Ops: Contains different tasks to automate the Panorama operations:
  1. Address checker to quickly get all the dependencies from Address Group

- Topology Builder: by entering either a YML host file or a specific Core Switch info, topology diagrams are generated automatically which can then be downloaded.

An environment file called ".env" should also exist in the same directory where the script exists. This file contains environmental variables.

Panorama Ops require cert chain to secure communication. It should be included in /network_automation/panorama_ops/ directory as it is used by api scrpits

You can find an example in a file named "env_example".

### Network Infrastructure Links

To edit the links page:

1. Add the URL to the ".env" file following the naming standard shown in the "env_example" file.

2. Go to the network_automation/templates/nw_infra_links/home.html and add the links using the variable name defined in the ".env" file. You can view the other links to see how to write the variable.

3. Go to the network_automation/nw_infra_links/views.py file and add the URL at the *VARIABLES* section at the bottom. Make sure you put the "config()" command arround it.

4. In the same location: network_automation/nw_infra_links/views.py add the variable you created on 3 to the def home() funnction at the end, you will need to add a comma after the last value before your entry. Always follow the standards.

### Site Documentation

This is a link to a React App that does a GET request to receive the current documentation of the sites which is stored in the file_display/src/documentation directory and presents it as an explorer application that can help navigate to the files that need to be downloaded.

The documentation file structure is generated by the site_documentation app in Flask which pulls the directory tree as JSON and then pulled by the React App by the use of a GET operation.

### Audit Manager

Enter the Core Switch of a site (the core hostname needs to be manually updated) and the configurations of the devices will be retrieved and the configuration will be put in YML.

Currently Supported:

- AAA
- Legacy ACLs
- Base Config
- BGP
- Interfaces
- NTP
- Prefix Lists
- Route Maps
- SNMP
- Static Routing
- STP
- SVIs
- VLANs
- VRFs

### Hostname Changer

Enter the Core Switch of a site (the core hostname needs to be manually updated) and switches and accesspoints will be renamed to follow the naming standard.

### Lifecycle Manager

Used to get a report of all network devices and their EoL information

### ISE MAC Bypass

There are two ways to enter data:  

1. CSV file (recommended for bulk imports). You can find an example on network_automation/ise_mac_bypass/example.csv

2. By adding MAC addresses and Device type manually. The format must follow the text field format shown.

### MAC Finder

You need to enter three parameters:

1. Core Switch hostname, must be using the standard naming convention of site-**cs**01-xxx

2. The core switch IP address if there is no DNS record, otherwise the DNS record may be used.

3. The IP address whose MAC address you want to find.

### Topology Builder

You can enter data in two ways:

1. Uploading a YAML file following the format shown on the network_automation/topology_builder/graphviz/hosts_example.yml . Not recommended at the moment.

2. Entering 3 parameters manually:

    1. Core Switch hostname, must be using the standard naming convention of site-**cs**01-xxx.

    2. The core switch IP address if there is no DNS record, otherwise the DNS record may be used.

    3. Select if it is a nxos or an IOS device.

### SDWAN Ops Prisma Access Tunnels Provisioning

1. Enter the vManage credentials

2. Enter input data: Site code, Region and Location as specified in the provided link.

### Panorama Ops 

1. Enter Address Group Name
2. All dependent addresses will be displayed in text window

## Documentation

You can find the documentation for the devbox, web server, and changes to the sdks, and execution under the "documentation/" directory.

## Future upgrades

- Tacacs Authentication Error Handling (bug).

- MAC Finder:
  - If MAC does not exists (error handling bug).
  - If MAC is behind an AP (error handling bug).

- Topology Builder:
  - YAML File upload: Does not have much benefit since we lack an inventory SoT (feature upgrade).
  - Resulting Diagrams: They do not look very pretty (feature upgrade).
