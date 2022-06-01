#! /usr/bin/env python
"""
Creates the Blueprint for the secondary app
"""

from flask import Blueprint

audit_manager = Blueprint("audit_manager", __name__)
