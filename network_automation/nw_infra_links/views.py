#! /usr/bin/env python
"""
Creates the views (routes) for the secondary app
"""
from flask import render_template, redirect, url_for
from network_automation.nw_infra_links import nw_infra_links

### VARIABLES ###
template_dir = "nw_infra_links"

### VIEW TO CREATE DATA ###
@nw_infra_links.route("/home")
def home():
    return render_template(f"{template_dir}/home.html")

