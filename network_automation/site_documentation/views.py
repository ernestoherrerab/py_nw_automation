#! /usr/bin/env python
"""
Creates the views (routes) for the secondary app
"""
from pathlib import Path
from flask import render_template
from network_automation.site_documentation import site_documentation
import network_automation.site_documentation.get_documentation as get_docs

### VARIABLES ###
template_dir = "site_documentation"

### VIEW TO CREATE DATA ###
@site_documentation.route("/home")
def home():
    """ Get Site Documentation """
    site_data_list = get_docs.get_documentation()
    return render_template(
        f"{template_dir}/home.html", site_data_list=site_data_list
    )