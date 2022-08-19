#! /usr/bin/env python
"""
Module to add visual description to switches
"""

from graphviz import Digraph
import re

def gen_graph(name, source_list, filename):
    """
    Generate Graph
    """
    ### VARIABLES ###
    ### IMAGES LOCATION RELATIVE TO DOT FILE ###
    IMAGES_LOCATION = "./../../../../../network_automation/topology_builder/graphviz/"
    dot = Digraph(name, format="png")
    core_dot = Digraph('coregraph')
    core_dot.graph_attr.update(rank='min')
    dot.attr("edge", arrowhead="none")
    dot.format = "png"
    dot.graph_attr["splines"] = "ortho"

    ### GENERATE EDGE RELATIONSHIPS ###
    for edges in source_list:
        for node in edges:
            host_type = re.findall(r"^\w+-([a-z]+|[A-Z]+)", node)
            if host_type and host_type[0] == "cs":
                core_dot.node(node, image=f'{IMAGES_LOCATION}images/l3_sw.png', shape="box")
            elif host_type and host_type[0] == "as":
                dot.node(node, image=f'{IMAGES_LOCATION}images/access_sw.png', shape="box")
            elif host_type and host_type[0] == "wlc":
                dot.node(node, image=f'{IMAGES_LOCATION}images/wlc.png', shape="box")
            elif host_type and host_type[0] == "ds":
                dot.node(node, image=f'{IMAGES_LOCATION}images/dist_sw.png', shape="box")
            elif host_type and host_type[0] == "ap":
                dot.node(node, image=f'{IMAGES_LOCATION}images/accesspoint.png', shape="box")
            elif host_type and host_type[0] == "uc":
                dot.node(node, image=f'{IMAGES_LOCATION}images/unityserver.png', shape="box")
            elif host_type and host_type[0] == "edgertr":
                dot.node(node, image=f'{IMAGES_LOCATION}images/router.png', shape="box")
            elif host_type and host_type[0] == "ron":
                dot.node(node, image=f'{IMAGES_LOCATION}images/router.png', shape="box")
            elif host_type and host_type[0] == "rtr":
                dot.node(node, image=f'{IMAGES_LOCATION}images/router.png', shape="box")
            elif host_type and host_type[0] == "rcrtr":
                dot.node(node, image=f'{IMAGES_LOCATION}images/router.png', shape="box")
            elif not host_type and node.startswith("SEP"):
                dot.node(node, image=f'{IMAGES_LOCATION}images/phone.png', shape="box")
            elif not host_type and node.startswith("sep"):
                dot.node(node, image=f'{IMAGES_LOCATION}images/phone.png', shape="box")
            elif host_type and host_type[0] == "esx":
                dot.node(node, image=f'{IMAGES_LOCATION}images/server.png', shape="box")
            elif host_type and host_type[0] == "isepsn":
                dot.node(node, image=f'{IMAGES_LOCATION}images/nac.png', shape="box")
            else:
                dot.node(node, shape="box")
        dot.subgraph(core_dot)
        dot.edge(edges[0],edges[1])
    dot.render(filename=filename, format="png")
