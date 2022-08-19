#! /usr/bin/env python
"""
Creates the Blueprint for the secondary app
"""
from flask import Blueprint
from flask_cors import CORS

site_documentation = Blueprint("site_documentation", __name__)
CORS(site_documentation)

