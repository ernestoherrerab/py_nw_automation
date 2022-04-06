#! /usr/bin/env python
"""
Creates the Blueprint for the secondary app
"""
import sys

sys.dont_write_bytecode = True
from flask import Blueprint

topology_builder = Blueprint("topology_builder", __name__)
