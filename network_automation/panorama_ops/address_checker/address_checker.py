import requests
from decouple import config
requests.packages.urllib3.disable_warnings()
def panorama_address_check(input_address_group):
    Panorama_API_KEY=config("Panorama_API_KEY")
    headers = { 'X-PAN-KEY' : Panorama_API_KEY}
    responseAddressGroups_json = requests.get(config("PA_URL")+"Objects/AddressGroups?location=shared",headers=headers,verify='network_automation/panorama_ops/pa-mgmt-dk-flsmidth-net-chain.pem').json()
    responseAddresses_json = requests.get(config("PA_URL")+"Objects/Addresses?location=shared",headers=headers,verify='network_automation/panorama_ops/pa-mgmt-dk-flsmidth-net-chain.pem').json()
    def find_member_names(address_group_name,responseAG_json):
        for entry in responseAG_json['result']['entry']:
            if entry['@name']==address_group_name.strip() :
                return entry['static']['member']

    def findObjIPNetmask(memberName,responseA_json):
        for entry in responseA_json['result']['entry']:
            if entry['@name']==memberName.strip() :
                if 'ip-netmask' in entry:
                    return (entry['@name']+' '+entry['ip-netmask'])
                elif 'ip-range' in entry:
                    return (entry['@name']+' '+entry['ip-range'])
                elif 'ip-wildcard' in entry:
                    return (entry['@name']+' '+entry['ip-wildcard'])
                elif 'fqdn' in entry:
                    return (entry['@name']+' '+entry['ip-fqdn'])                
    def recursion(input_ag):
        output=''
        temp=find_member_names(input_ag,responseAddressGroups_json)
        if str(temp) != 'None' :
            for entry in temp:
                    ret=find_member_names(entry,responseAddressGroups_json)
                    if(str(ret)!='None'):
                        output=output+recursion(entry)  
                    else:
                        output=output+' '+findObjIPNetmask(entry,responseAddresses_json)+'\n'
            return output
    
    return recursion(input_address_group)