#! /usr/bin/env python
"""
Module to Structure a dictionary for HTML consumption
"""
from pathlib import Path, PurePath
import network_automation.site_documentation.dict_ops as dict_ops

def get_documentation():
    """ Get diagrams path information """

    src_dir = Path("file_display/public/documentation/")
    site_docs = {}
    tmp_dicts = []
    dir_contents = src_dir.glob("**/*")
    tree = [item for item in dir_contents if item.is_file()] 
    tupled_tree = [PurePath(branch).parts for branch in tree]
    
    for tuple_branch in tupled_tree:
        tmp_site_docs = tmp_dict = {}
        for dir in tuple_branch[3:len(tuple_branch)]:
            tmp_dict[dir] = {}
            tmp_dict = tmp_dict[dir]
        tmp_dicts.append(tmp_site_docs)

    for item in tmp_dicts:
        dict_ops.dict_merge(site_docs, item)

    for tuple in tupled_tree:
        tuple = list(tuple)
        tuple = tuple[3:]
        dict_ops.setInDict(site_docs, tuple, tuple[len(tuple)-1])
    dict_ops.iterdict(site_docs)
    
    final_site_docs = dict_ops.restructure_data(site_docs)

    return final_site_docs