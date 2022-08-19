#! /usr/bin/env python
"""
Creates the views (routes) for the secondary app
"""
from pathlib import Path
from flask import jsonify, request, send_file
from network_automation.site_documentation import site_documentation
import network_automation.site_documentation.get_documentation as get_docs

### VARIABLES ###
template_dir = "site_documentation"

### VIEW TO CREATE DATA ###
@site_documentation.route("/home", methods = ['GET'])
def home():
    """ Get Site Documentation """
    site_data = get_docs.get_documentation()
    if request.method == 'GET':
        response = jsonify({'data': site_data})
        return response

@site_documentation.route("/file_download", methods = ['GET','POST'])
def file_download():
    """ Get Site Documentation """
    if request.method == 'POST':
        for value in request.json.values():
            doc_path = value
            doc_path = Path("../documentation/" + value)
        
        return send_file(str(doc_path), as_attachment=True)

