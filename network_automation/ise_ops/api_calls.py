#! /usr/bin/env python
"""
Module to group the CRUD operations for API calls
"""

from json import loads
import logging
from pathlib import Path 
from requests import delete, get, post, put, Response, RequestException

### LOGGING SETUP ###
LOG_FILE = Path("logs/ise_ops.log")
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler(LOG_FILE)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

def get_operations(ops_type: str, url_var: str, username: str, password: str) -> dict:
    """To Perform GET operations on ISE"""
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    url = f"{url_var}/ers/config/{ops_type}"
    ops_get = get(
        url, headers=headers, auth=(username, password), verify=False
    )
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

def del_operations(ops_type: str, url_var: str, username: str, password: str):
    """To Perform DEL operations on ISE"""
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    url = f"{url_var}/ers/config/{ops_type}"
    ops_del = delete(
        url, headers=headers, auth=(username, password), verify=False
    )
    if ops_del.status_code == 401:
        ops_del.close()
        logger.info(f'API Call: {ops_del.status_code} Request Failed...Unknown why')
        return ops_del.status_code
    elif ops_del.status_code == 204:
        ops_del.close()
        logger.info(f'API Call: {ops_del.status_code} MAC Deleted...')
        return ops_del.status_code

def post_operations(
    ops_type: str, operations_data: dict, url_var: str, username: str, password: str
    ):
    """To Perform POST operations on ISE"""
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    url = f"{url_var}/ers/config/{ops_type}"
    payload = operations_data
    ops_post = post(
        url, headers=headers, auth=(username, password), json=payload, verify=False
    )
    if ops_post.status_code == 201:
        print("POST Request Successful!")
        ops_post.close()
        logger.info(f'API Call: {ops_post.status_code} POST Request Successful!')
        return ops_post.status_code     
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
        ops_post.close()
        logger.error(f'API Call: {ops_post.status_code} Unexpected server side error.')
        return ops_post.status_code
    else:
        print("POST Request Failed")
        ops_post.close()
        logger.error(f'API Call: {ops_post.status_code} Request Failed...Unknown why')
        return ops_post.status_code