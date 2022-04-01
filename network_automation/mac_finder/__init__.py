#! /usr/bin/env python
"""
Creates the Blueprint for the secondary app
"""
import sys
sys.dont_write_bytecode = True
from flask import Blueprint

mac_finder = Blueprint(
    "mac_finder", 
    __name__
    )