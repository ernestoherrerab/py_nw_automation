#! /usr/bin/env python
"""
Module to group the CRUD operations for API calls
"""

from json import loads
from httpx import get, put, Response

def get_operations(ops_type: str, url_var: str, headers: str) -> Response:
    """API GET operations """
    url = f"{url_var}/{ops_type}"
    ops_get = get(url, headers=headers,verify=False)
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
    
def put_operations(
    ops_type: str, operations_data: dict, url_var: str, username: str, password: str
    ) -> Response:
    """ API PUT operations """
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    url = f"{url_var}/webacs/api/v3/op/{ops_type}"
    payload = operations_data
    ops_put = put(
        url, headers=headers, auth=(username, password), json=payload, verify=False
    )
    if  ops_put.status_code == 200:
        print("PUT Request Successful! Feature Updated!")
        ops_put.close()
        return ops_put.status_code
    elif  ops_put.status_code == 201:
        print("PUT Request Successful! New Resource Created!")
        ops_put.close()
        return ops_put.status_code
    elif ops_put.status_code == 400:
        print("JSON error. Check the JSON format.")
        ops_put.close()
        return ops_put.status_code
    elif ops_put.status_code == 401:
        print("Authentication Error. Login again.")
        ops_put.close()
        return ops_put.status_code
    elif ops_put.status_code == 403:
        print("Insufficient permissions to access this resource.")
        ops_put.close()
        return ops_put.status_code
    elif ops_put.status_code == 409:
        print("The submitted resource conflicts with another.")
    elif ops_put.status_code == 415:
        print("Unsopported Media Type")
        ops_put.close()
        return ops_put.status_code
    elif ops_put.status_code == 422:
        print('Request validation error. Check "errors" array for details.')
        ops_put.close()
        return ops_put.status_code
    elif ops_put.status_code == 500:
        print("Unexpected server side error.")
        ops_put.close()
        return ops_put.status_code
    else:
        print("POST Request Failed...Uknown Error")
        ops_put.close()
        return ops_put.status_code