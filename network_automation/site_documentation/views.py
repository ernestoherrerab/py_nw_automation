#! /usr/bin/env python
"""
Creates the views (routes) for the secondary app
"""
from pathlib import Path
from flask import render_template, jsonify, request
from network_automation.site_documentation import site_documentation
import network_automation.site_documentation.get_documentation as get_docs

### VARIABLES ###
template_dir = "site_documentation"

### VIEW TO CREATE DATA ###
@site_documentation.route("/home", methods = ['GET'])
def home():
    """ Get Site Documentation """
    site_data_list = get_docs.get_documentation()
    if(request.method == 'GET'):
  
        site_data = site_data_list
        response = jsonify({'data': site_data})
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response

@site_documentation.app_template_filter('is_dict')
def is_dict(value):
    return isinstance(value, dict)
