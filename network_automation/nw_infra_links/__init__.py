#! /usr/bin/env python
"""
Creates the Blueprint for the secondary app
"""
import sys
sys.dont_write_bytecode = True
from flask import Blueprint

nw_infra_links = Blueprint(
    "nw_infra_links", 
    __name__
    )