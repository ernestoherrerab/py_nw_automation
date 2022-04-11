#! /usr/bin/env python
"""
Module to add visual description to switches
"""

from graphviz import Digraph
from pathlib import Path
import re

def host_list(hosts):
    host_list = []
    for result_host in hosts.keys():
        host_list.append(result_host)
    return host_list


def gen_graph(name, source_list, filename):
    """
    Generate Graph
    """
    
    dot = Digraph(name, format="png")
    dot.attr("node", shape="box")
    #dot.attr("node", image="./images/l3_sw.png")
    dot.attr("edge", arrowhead="none")
    dot.format = "png"
    dot.graph_attr["splines"] = "ortho"
    
    ### GENERATE EDGE RELATIONSHIPS ###
    for edges in source_list:
        for node in edges:
            host_type = re.findall(r"^\w+-([a-z]+|[A-Z]+)", node)
            if host_type and host_type[0] == "cs":
                dot.attr("node", image="./images/l3_sw.png")
            elif host_type and host_type[0] == "as":
                dot.attr("node", image="./images/access_sw.png")
            elif host_type and host_type[0] == "wlc":
                dot.attr("node", image="./images/wlc.png")    
            elif host_type and host_type[0] == "ds":
                dot.attr("node", image="./images/dist_sw.png")   
            elif host_type and host_type[0] == "ap":
                dot.attr("node", image="./images/accesspoint.png")   
            else:
                dot.attr("node", image="./images/nx_sw.png")    
        dot.edge(edges[0],edges[1])
    dot.render(filename=filename, format="png")