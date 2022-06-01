#! /usr/bin/env python
"""
Module to display the available diagrams
"""

from pathlib import Path

def get_diagram_data():
    """ Get diagrams path information """

    src_dir = Path("documentation/diagrams/")
    diagrams_data_list = []
    for diagram_path in src_dir.iterdir():
        if diagram_path.suffix == ".png":
            diagram_dir = str(diagram_path)
            diagram_name = str(diagram_path).replace(str(src_dir) + "/", "")
            diagrams_data = (diagram_dir, diagram_name)
            diagrams_data_list.append(diagrams_data)
    
    return diagrams_data_list
