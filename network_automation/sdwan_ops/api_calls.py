#! /usr/bin/env python
"""
Module to group the CRUD operations for API calls
"""

from json import loads
import logging
from pathlib import Path 
from requests import get, post, put, Response, RequestException

### LOGGING SETUP ###
LOG_FILE = Path("logs/sdwan_ops.log")
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler(LOG_FILE)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

def get_operations(ops_type: str, url_var: str, headers: str) -> Response:
    """API GET operations """
    url = f"{url_var}/{ops_type}"
    ops_get = get(url, headers=headers,verify=False, timeout=20.0)
    if ops_get.status_code == 200:
        ops_data = loads(ops_get.text)
        logger.info(f'API Call: {ops_get.status_code} {ops_data}')
        ops_get.close()
        return ops_data

    elif ops_get.status_code == 401:
        print("Authentication Issue. Login again.")
        ops_get.close()
        logger.info(f'API Call: {ops_get.status_code} Authentication Issue')
        return ops_get.status_code

    elif ops_get.status_code == 403:
        print("Insufficient permissions to access this resource.")
        ops_get.close()
        logger.info(f'API Call: {ops_get.status_code} Insufficient permissions to access this resource.')
        return ops_get.status_code

    elif ops_get.status_code == 500:
        print("Unexpected server side error.")
        ops_get.close()
        logger.info(f'API Call: {ops_get.status_code} Unexpected server side error.')
        return ops_get.status_code

    else:
        print("GET Request Failed...Unknown why")
        ops_get.close()
        logger.info(f'API Call: {ops_get.status_code} Request Failed...Unknown why')
        return ops_get.status_code
    
def post_operations(ops_type: str, url_var: str, payload: dict, headers: dict, json=True) -> Response:
    """ API POST operations """

    url = f"{url_var}/{ops_type}"
    if json:
        try:
            ops_post = post(url, headers=headers, json=payload, verify=False)
            if ops_post.status_code == 201:
                print("POST Request Successful!")
                ops_data = loads(ops_post.text)
                ops_post.close()
                logger.info(f'API Call: {ops_post.status_code} POST Request Successful! {ops_data}')
                return ops_data       
            elif ops_post.status_code == 400:
                print("JSON error. Check the JSON format.")
                ops_post.close()
                logger.error(f'API Call: {ops_post.status_code} JSON error. Check the JSON format.')
                return ops_post.status_code
            elif ops_post.status_code == 401:
                print("Token error. Login again.")
                ops_post.close()
                logger.error(f'API Call: {ops_post.status_code} Authentication error.')
                return ops_post.status_code
            elif ops_post.status_code == 403:
                print("Insufficient permissions to access this resource.")
                ops_post.close()
                logger.error(f'API Call: {ops_post.status_code} Insufficient permissions to access this resource.')
                return ops_post.status_code
            elif ops_post.status_code == 409:
                print("The submitted resource conflicts with another.")
                ops_post.close()
                logger.error(f'API Call: {ops_post.status_code} The submitted resource conflicts with another.')
                return ops_post.status_code
            elif ops_post.status_code == 422:
                print('Request validation error. Check "errors" array for details.')
                ops_post.close()
                logger.error(f'API Call: {ops_post.status_code} Request validation error. Check "errors" array for details.')
                return ops_post.status_code
            elif ops_post.status_code == 500:
                print("Unexpected server side error.")
                ops_data = loads(ops_post.text)
                ops_post.close()
                logger.error(f'API Call: {ops_post.status_code} Unexpected server side error.')
                return ops_data, ops_post.status_code
            else:
                print("POST Request Failed")
                ops_post.close()
                logger.error(f'API Call: {ops_post.status_code} Request Failed...Unknown why')
                return ops_post.status_code
        except RequestException as exc:
            print(f"An error occurred while requesting {exc.request.url!r}.")

    else:
        try:
            ops_post = post(url, headers=headers, json=payload, verify=False)
            if ops_post.status_code == 201:
                print("POST Request Successful!")
                ops_data = ops_post.text
                ops_post.close()
                return ops_data       
            elif ops_post.status_code == 400:
                print("JSON error. Check the JSON format.")
                ops_post.close()
                logger.error(f'API Call: {ops_post.status_code} JSON error. Check the JSON format.')
                return ops_post.status_code
            elif ops_post.status_code == 401:
                print("Token error. Login again.")
                ops_post.close()
                logger.error(f'API Call: {ops_post.status_code} Authentication error.')
                return ops_post.status_code
            elif ops_post.status_code == 403:
                print("Insufficient permissions to access this resource.")
                ops_post.close()
                logger.error(f'API Call: {ops_post.status_code} Insufficient permissions to access this resource.')
                return ops_post.status_code
            elif ops_post.status_code == 409:
                print("The submitted resource conflicts with another.")
                ops_post.close()
                logger.error(f'API Call: {ops_post.status_code} The submitted resource conflicts with another.')
                return ops_post.status_code
            elif ops_post.status_code == 422:
                print('Request validation error. Check "errors" array for details.')
                ops_post.close()
                logger.error(f'API Call: {ops_post.status_code} Request validation error. Check "errors" array for details.')
                return ops_post.status_code
            elif ops_post.status_code == 500:
                print("Unexpected server side error.")
                ops_data = loads(ops_post.text)
                ops_post.close()
                logger.error(f'API Call: {ops_post.status_code} Unexpected server side error.')
                return ops_data, ops_post.status_code
            else:
                print("POST Request Failed")
                ops_post.close()
                logger.error(f'API Call: {ops_post.status_code} Request Failed...Unknown why')
                return ops_post.status_code
        except RequestException as exc:
            print(f"An error occurred while requesting {exc.request.url!r}.")

def put_operations(ops_type: str, url_var: str, payload: dict, headers: dict, json=True) -> Response:
    """ API PUT operations """

    url = f"{url_var}/{ops_type}"
    if json:
        try:
            ops_put = put(url, headers=headers, json=payload, verify=False)
            if ops_put.status_code == 200:
                print("PUT Request Successful!")
                ops_data = loads(ops_put.text)
                ops_put.close()
                logger.info(f'API Call: {ops_put.status_code} PUT Request Successful! {ops_data}')
                return ops_data       
            elif ops_put.status_code == 400:
                print("JSON error. Check the JSON format.")
                ops_put.close()
                logger.error(f'API Call: {ops_put.status_code} JSON error. Check the JSON format.')
                return ops_put.status_code
            elif ops_put.status_code == 401:
                print("Token error. Login again.")
                ops_put.close()
                logger.error(f'API Call: {ops_put.status_code} Authentication error.')
                return ops_put.status_code
            elif ops_put.status_code == 403:
                print("Insufficient permissions to access this resource.")
                ops_put.close()
                logger.error(f'API Call: {ops_put.status_code} Insufficient permissions to access this resource.')
                return ops_put.status_code
            elif ops_put.status_code == 409:
                print("The submitted resource conflicts with another.")
                ops_put.close()
                logger.error(f'API Call: {ops_put.status_code} The submitted resource conflicts with another.')
                return ops_put.status_code
            elif ops_put.status_code == 422:
                print('Request validation error. Check "errors" array for details.')
                ops_put.close()
                logger.error(f'API Call: {ops_put.status_code} Request validation error. Check "errors" array for details.')
                return ops_put.status_code
            elif ops_put.status_code == 500:
                print("Unexpected server side error.")
                ops_data = loads(ops_put.text)
                ops_put.close()
                logger.error(f'API Call: {ops_put.status_code} Unexpected server side error.')
                return ops_data, ops_put.status_code
            else:
                print("POST Request Failed")
                ops_put.close()
                logger.error(f'API Call: {ops_put.status_code} Request Failed...Unknown why')
                return ops_put.status_code
        except RequestException as exc:
            print(f"An error occurred while requesting {exc.request.url!r}.")

    else:
        try:
            ops_put = put(url, headers=headers, json=payload, verify=False)
            if ops_put.status_code == 201:
                print("PUT Request Successful!")
                ops_data = ops_put.text
                ops_put.close()
                return ops_data       
            elif ops_put.status_code == 400:
                print("JSON error. Check the JSON format.")
                ops_put.close()
                logger.error(f'API Call: {ops_put.status_code} JSON error. Check the JSON format.')
                return ops_put.status_code
            elif ops_put.status_code == 401:
                print("Token error. Login again.")
                ops_put.close()
                logger.error(f'API Call: {ops_put.status_code} Authentication error.')
                return ops_put.status_code
            elif ops_put.status_code == 403:
                print("Insufficient permissions to access this resource.")
                ops_put.close()
                logger.error(f'API Call: {ops_put.status_code} Insufficient permissions to access this resource.')
                return ops_put.status_code
            elif ops_put.status_code == 409:
                print("The submitted resource conflicts with another.")
                ops_put.close()
                logger.error(f'API Call: {ops_put.status_code} The submitted resource conflicts with another.')
                return ops_put.status_code
            elif ops_put.status_code == 422:
                print('Request validation error. Check "errors" array for details.')
                ops_put.close()
                logger.error(f'API Call: {ops_put.status_code} Request validation error. Check "errors" array for details.')
                return ops_put.status_code
            elif ops_put.status_code == 500:
                print("Unexpected server side error.")
                ops_data = loads(ops_put.text)
                ops_put.close()
                logger.error(f'API Call: {ops_put.status_code} Unexpected server side error.')
                return ops_data, ops_put.status_code
            else:
                print("POST Request Failed")
                ops_put.close()
                logger.error(f'API Call: {ops_put.status_code} Request Failed...Unknown why')
                return ops_put.status_code
        except RequestException as exc:
            print(f"An error occurred while requesting {exc.request.url!r}.")



    


    