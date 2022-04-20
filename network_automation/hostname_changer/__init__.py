#! /usr/bin/env python
"""
Creates the Blueprint for the secondary app
"""

from flask import Blueprint

hostname_changer = Blueprint("hostname_changer", __name__)
