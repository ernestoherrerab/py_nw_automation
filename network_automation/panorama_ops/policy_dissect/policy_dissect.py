import requests
from decouple import config
requests.packages.urllib3.disable_warnings()

def policy_dissect(input_policy_name):
    Panorama_API_KEY=config("Panorama_API_KEY")
    headers = { 'X-PAN-KEY' : Panorama_API_KEY}
    responseservicesGroups_json = requests.get(config("PA_URL")+"Policies/SecurityPreRules?location=device-group&device-group=Global",headers=headers,verify='network_automation/panorama_ops/pa-mgmt-dk-flsmidth-net-chain.pem').json()
    result=responseservicesGroups_json['result']['entry']
    outputDict =	{
                "name": input_policy_name,
                "source": [] ,
                "destination": [] ,
                "application": [] ,
                "service": []
                } 
    for entry in result:
        if entry['@name']==input_policy_name:
            for member in entry['source']['member']:
                outputDict['source'].append(member)
            for member in entry['destination']['member']:
                outputDict['destination'].append(member)
            for member in entry['application']['member']:
                outputDict['application'].append(member)
            for member in entry['service']['member']:
                outputDict['service'].append(member)
    return outputDict