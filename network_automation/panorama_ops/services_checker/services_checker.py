import requests
from decouple import config
requests.packages.urllib3.disable_warnings()
def panorama_services_check(input_services_group):
    Panorama_API_KEY=config("Panorama_API_KEY")
    headers = { 'X-PAN-KEY' : Panorama_API_KEY}
    responseservicesGroups_json = requests.get(config("PA_URL")+"Objects/ServiceGroups?location=shared",headers=headers,verify='network_automation/panorama_ops/pa-mgmt-dk-flsmidth-net-chain.pem').json()
    responseserviceses_json = requests.get(config("PA_URL")+"Objects/Services?location=shared",headers=headers,verify='network_automation/panorama_ops/pa-mgmt-dk-flsmidth-net-chain.pem').json()

    def find_member_names(services_group_name,responseSG_json):
        for entry in responseSG_json['result']['entry']:
            if entry['@name']==services_group_name.strip() :
                return entry['members']['member']

    def findSrvPortNum(memberName,responseS_json):
        for entry in responseS_json['result']['entry']:
            if entry['@name']==memberName.strip() :
                if 'tcp' in entry['protocol']:
                    if 'udp' not in entry['protocol']:
                        return  (entry['@name']+' tcp  '+entry['protocol']['tcp']['port'])
                    else:
                        return  (entry['@name']+' tcp  '+entry['protocol']['tcp']['port'] + ' udp '+entry['protocol']['tcp']['port'])
                elif 'udp' in entry['protocol']:
                    if 'tcp' not in entry['protocol']:
                        return  (entry['@name']+' udp '+entry['protocol']['udp']['port'])
                    else:
                        return  (entry['@name']+' tcp  '+entry['protocol']['tcp']['port'] + ' udp '+entry['protocol']['tcp']['port'])            
    def recursion(input_ag):
        output=''
        temp=find_member_names(input_ag,responseservicesGroups_json)
        for entry in temp:
            ret=find_member_names(entry,responseservicesGroups_json)
            if(str(ret)!='None'):
                output=output+recursion(entry)  
            else:
                output=output+' '+str(findSrvPortNum(entry,responseserviceses_json))+'\n'
        return output
    
    return recursion(input_services_group)

def panorama_service_check_ports(input_services_group):
    Panorama_API_KEY=config("Panorama_API_KEY")
    headers = { 'X-PAN-KEY' : Panorama_API_KEY}
    responseservicesGroups_json = requests.get(config("PA_URL")+"Objects/ServiceGroups?location=shared",headers=headers,verify='network_automation/panorama_ops/pa-mgmt-dk-flsmidth-net-chain.pem').json()
    responseserviceses_json = requests.get(config("PA_URL")+"Objects/Services?location=shared",headers=headers,verify='network_automation/panorama_ops/pa-mgmt-dk-flsmidth-net-chain.pem').json()
    
    def find_member_names(services_group_name,responseSG_json):
        
        for entry in responseSG_json['result']['entry']:
            if entry['@name']==services_group_name.strip() :
                return entry['members']['member']

    def findSrvPortNum(memberName,responseS_json):
        for entry in responseS_json['result']['entry']: 

            if entry['@name']==memberName.strip() :

                if 'tcp' in entry['protocol']:
                    if 'udp' not in entry['protocol']:
                        return  ('tcp  '+entry['protocol']['tcp']['port'])
                    else:
                        return  ('tcp  '+entry['protocol']['tcp']['port'] + 'udp '+entry['protocol']['tcp']['port'])
                elif 'udp' in entry['protocol']:
                    if 'tcp' not in entry['protocol']:
                        return  ('udp '+entry['protocol']['udp']['port'])
                    else:
                        return  ('tcp  '+entry['protocol']['tcp']['port'] + 'udp '+entry['protocol']['tcp']['port'])            
        else:
            return memberName

                    
    def recursion(input_ag):
        output=[]
        if input_ag == 'application-default':
            output.append(input_ag)
            return output
        temp=find_member_names(input_ag,responseservicesGroups_json)
        if temp is not None:
            for entry in temp:
                ret=find_member_names(entry,responseservicesGroups_json)
                if(str(ret)!='None'):
                    output.append(recursion(entry))  
                else:
                    output.append(findSrvPortNum(entry,responseserviceses_json))
        
        else:
            output.append(findSrvPortNum(input_ag,responseserviceses_json))
        return output
    if input_services_group in responseserviceses_json['result']['entry']:
        return input_services_group['result']['entry']
    
    return recursion(input_services_group)
