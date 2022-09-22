#! /usr/bin/env python
"""
Authentication Class for vManage
"""
import logging
from httpx import get, post

logger = logging.getLogger(__name__)

class Authentication:

    @staticmethod
    def get_jsessionid(vmanage_host, username, password):
        api = "/j_security_check"
        url = vmanage_host + api
        payload = {'j_username' : username, 'j_password' : password}

        response = post(url=url, data=payload, verify=False)
        try:
            cookies = response.headers["Set-Cookie"]
            jsessionid = cookies.split(";")
            return(jsessionid[0])
        except:
            if logger is not None:
                logger.error("No valid JSESSION ID returned\n")
            exit()

    @staticmethod
    def get_token(vmanage_host, jsessionid):
        headers = {'Cookie': jsessionid}
        api = "/dataservice/client/token"
        url = vmanage_host + api 
        response = get(url=url, headers=headers, verify=False)
        if response.status_code == 200:
            return(response.text)
        else:
            return None