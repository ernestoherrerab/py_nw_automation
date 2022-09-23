#! /usr/bin/env python
"""
Module to group the CRUD operations for API calls
"""

from json import loads
from httpx import get, post, Response

def get_operations(ops_type: str, url_var: str, headers: str) -> Response:
    """API GET operations """

    url = f"{url_var}/{ops_type}"
    ops_get = get(url, headers=headers,verify=False, timeout=10.0)
    if ops_get.status_code == 200:
        ops_data = loads(ops_get.text)
        return ops_data
    elif ops_get.status_code == 401:
        print("Authentication Issue. Login again.")
        ops_get.close()
        return ops_get.status_code
    elif ops_get.status_code == 403:
        print("Insufficient permissions to access this resource.")
        ops_get.close()
        return ops_get.status_code
    elif ops_get.status_code == 500:
        print("Unexpected server side error.")
        ops_get.close()
        return ops_get.status_code
    else:
        print("GET Request Failed...Unknown why")
        ops_get.close()
        return ops_get.status_code
    
def post_operations(ops_type: str, url_var: str, payload: dict, headers: dict) -> Response:
    """ API POST operations """

    url = f"{url_var}/{ops_type}"
    ops_post = post(url, headers=headers, json=payload, verify=False)
    if ops_post.status_code == 200:
        print("POST Request Successful!")
        ops_data = loads(ops_post.text)
        return ops_data       
    elif ops_post.status_code == 400:
        print("JSON error. Check the JSON format.")
        return ops_post.status_code
    elif ops_post.status_code == 401:
        print("Token error. Login again.")
        return ops_post.status_code
    elif ops_post.status_code == 403:
        print("Insufficient permissions to access this resource.")
        return ops_post.status_code
    elif ops_post.status_code == 409:
        print("The submitted resource conflicts with another.")
        return ops_post.status_code
    elif ops_post.status_code == 422:
        print('Request validation error. Check "errors" array for details.')
        return ops_post.status_code
    elif ops_post.status_code == 500:
        print("Unexpected server side error.")
        return ops_post.status_code
    else:
        print("POST Request Failed")
        return ops_post.status_code
    