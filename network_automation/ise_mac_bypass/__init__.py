#! /usr/bin/env python
"""
Creates the Blueprint for the secondary app
"""
import sys
sys.dont_write_bytecode = True
from flask import Blueprint

ise_mac_bypass = Blueprint(
    "ise_mac_bypass", 
    __name__
    )