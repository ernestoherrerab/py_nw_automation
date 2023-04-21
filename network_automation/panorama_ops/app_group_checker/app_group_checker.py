import requests
from decouple import config
requests.packages.urllib3.disable_warnings()
def panorama_app_group_check(input_app_group):
    Panorama_API_KEY=config("Panorama_API_KEY")
    headers = { 'X-PAN-KEY' : Panorama_API_KEY}
    responseAppGroups_json = requests.get(config("PA_URL")+"Objects/ApplicationGroups?location=shared",headers=headers,verify='network_automation/panorama_ops/pa-mgmt-dk-flsmidth-net-chain.pem').json()
    def find_member_names(app_group_name,responseAppGroups_json):
        if app_group_name=='any':
            return app_group_name
        for entry in responseAppGroups_json['result']['entry']:         
            if entry['@name']==app_group_name.strip() :
                return entry['members']['member']      
    def check(input_ag):
        output=[]
        temp=find_member_names(input_ag,responseAppGroups_json)
        if temp is None:
            output.append(input_ag)
        else:
            output.append(temp)
        return output
    
    return check(input_app_group)