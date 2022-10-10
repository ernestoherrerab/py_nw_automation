# Viptela SDK

The repository lives here: <https://github.com/CiscoDevNet/python-viptela>

In order to add the templates correctly, the payload of the "add_device_template" method in the "DeviceTemplates" class needs to be modified.
If this is not modified, then an error is raised.

Original payload is shown as:

~~~python

payload = {
    'templateName': device_template['templateName'],
    'templateDescription': device_template['templateDescription'],
    'deviceType': device_template['deviceType'],
    'factoryDefault': device_template['factoryDefault'],
    'configType': device_template['configType'],
    'featureTemplateUidRange': []
}
~~~

The error stems from the following line:

~~~python
else:
            payload['generalTemplates'] = device_template['generalTemplates']
~~~

There is no key called 'generalTemplates' on the payload dictionary.

and the change is done on the 'featureTemplateUidRange' key and instead have the following:

~~~python
        payload = {
            'templateName': device_template['templateName'],
            'templateDescription': device_template['templateDescription'],
            'deviceType': device_template['deviceType'],
            'factoryDefault': device_template['factoryDefault'],
            'configType': device_template['configType'],
            'featureTemplateUidRange': [],
            'generalTemplates': device_template['generalTemplates']
        }
~~~

***
Replaced the "attach_to_template" method in the "DeviceTemplates" class as follows:

~~~python
    def attach_to_template(self, payload, config_type):
        """Attach and device to a template

        Args:
            payload: (dict): The data to attach 
            config_type (str): Type of template i.e. device or CLI template


        Returns:
            action_id (str): Returns the action id of the attachment

        """

        if config_type == 'file':
            url = f"{self.base_url}template/device/config/attachcli"
        elif config_type == 'template':
            url = f"{self.base_url}template/device/config/attachfeature"
        else:
            raise RuntimeError('Got invalid Config Type')

        utils = Utilities(self.session, self.host, self.port)
        response = HttpMethods(self.session, url).request('POST', payload=json.dumps(payload))
        action_id = ParseMethods.parse_id(response)
        utils.waitfor_action_completion(action_id)

        return action_id
~~~
