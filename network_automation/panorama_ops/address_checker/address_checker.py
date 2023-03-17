import requests

requests.packages.urllib3.disable_warnings()
def panorama_address_check(input_address_group):
    Panorama_API_KEY="LUFRPT1ub1lQNWM2QldiN0RUeUQzWUNQNWhqcmJQV0E9eUlNTldRNG1jQWRpMHVyQWVsRnB5ZldLL3FQdy9SNUh3L2VvV1ZPRjQyN0haOUZnaVM2NTZtTUllNSt1dWtaa2c1U1grT0VFZ01xSnczQ0VLOVFYaHc9PQ=="
    headers = { 'X-PAN-KEY' : Panorama_API_KEY}
    responseAddressGroups_json = requests.get("https://pa-mgmt.dk.flsmidth.net/restapi/v10.2/Objects/AddressGroups?location=shared",headers=headers,verify='pa-mgmt-dk-flsmidth-net-chain.pem').json()
    responseAddresses_json = requests.get("https://pa-mgmt.dk.flsmidth.net/restapi/v10.2/Objects/Addresses?location=shared",headers=headers,verify='pa-mgmt-dk-flsmidth-net-chain.pem').json()
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
        for entry in find_member_names(input_ag,responseAddressGroups_json):
                ret=find_member_names(entry,responseAddressGroups_json)
                if(str(ret)!='None'):
                    output=output+recursion(entry)  
                else:
                    output=output+' '+findObjIPNetmask(entry,responseAddresses_json)+'\n'
        return output
    
    return recursion(input_address_group)

