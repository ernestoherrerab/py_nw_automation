#! /usr/bin/env python
"""
Module to group the CRUD operations for API calls
"""

from json import loads
from requests import get, post, Response, RequestException

def get_operations(ops_type: str, url_var: str, headers: str) -> Response:
    """API GET operations """
    url = f"{url_var}/{ops_type}"
    ops_get = get(url, headers=headers,verify=False, timeout=20.0)
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
    
def post_operations(ops_type: str, url_var: str, payload: dict, headers: dict, json=True) -> Response:
    """ API POST operations """

    url = f"{url_var}/{ops_type}"
    if json:
        try:
            ops_post = post(url, headers=headers, json=payload, verify=False)
            if ops_post.status_code == 200:
                print("POST Request Successful!")
                ops_data = loads(ops_post.text)
                ops_post.close()
                return ops_data       
            elif ops_post.status_code == 400:
                print("JSON error. Check the JSON format.")
                ops_post.close()
                return ops_post.status_code
            elif ops_post.status_code == 401:
                print("Token error. Login again.")
                ops_post.close()
                return ops_post.status_code
            elif ops_post.status_code == 403:
                print("Insufficient permissions to access this resource.")
                ops_post.close()
                return ops_post.status_code
            elif ops_post.status_code == 409:
                print("The submitted resource conflicts with another.")
                ops_post.close()
                return ops_post.status_code
            elif ops_post.status_code == 422:
                print('Request validation error. Check "errors" array for details.')
                ops_post.close()
                return ops_post.status_code
            elif ops_post.status_code == 500:
                print("Unexpected server side error.")
                ops_data = loads(ops_post.text)
                ops_post.close()
                return ops_data, ops_post.status_code
            else:
                print("POST Request Failed")
                ops_post.close()
                return ops_post.status_code
        except RequestException as exc:
            print(f"An error occurred while requesting {exc.request.url!r}.")

    else:
        try:
            ops_post = post(url, headers=headers, json=payload, verify=False)
            if ops_post.status_code == 200:
                print("POST Request Successful!")
                ops_data = ops_post.text
                ops_post.close()
                return ops_data       
            elif ops_post.status_code == 400:
                print("JSON error. Check the JSON format.")
                ops_post.close()
                return ops_post.status_code
            elif ops_post.status_code == 401:
                print("Token error. Login again.")
                ops_post.close()
                return ops_post.status_code
            elif ops_post.status_code == 403:
                print("Insufficient permissions to access this resource.")
                ops_post.close()
                return ops_post.status_code
            elif ops_post.status_code == 409:
                print("The submitted resource conflicts with another.")
                ops_post.close()
                return ops_post.status_code
            elif ops_post.status_code == 422:
                print('Request validation error. Check "errors" array for details.')
                ops_post.close()
                return ops_post.status_code
            elif ops_post.status_code == 500:
                print("Unexpected server side error.")
                ops_data = loads(ops_post.text)
                ops_post.close()
                return ops_data, ops_post.status_code
            else:
                print("POST Request Failed")
                ops_post.close()
                return ops_post.status_code
        except RequestException as exc:
            print(f"An error occurred while requesting {exc.request.url!r}.")



    