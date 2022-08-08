#! /usr/bin/env python
"""
Module to Structure a dictionary for HTML consumption
"""

from pathlib import Path, PurePath
from random import randint
from signal import siginterrupt
from typing_extensions import final
import network_automation.site_documentation.dict_ops as dict_ops

def get_documentation():
    """ Get diagrams path information """

    src_dir = Path("documentation/")
    site_docs = {}
    tmp_dicts = []
    dir_contents = src_dir.glob("**/*")
    tree = [item for item in dir_contents if item.is_file()]     
    tupled_tree = [PurePath(branch).parts for branch in tree]

    for tuple_branch in tupled_tree:
        tmp_site_docs = tmp_dict = {}
        for dir in tuple_branch[1:len(tuple_branch)]:
            tmp_dict[dir] = {}
            tmp_dict = tmp_dict[dir]
        tmp_dicts.append(tmp_site_docs)

    for item in tmp_dicts:
        dict_ops.dict_merge(site_docs, item)

    for tuple in tupled_tree:
        tuple = list(tuple)
        tuple.pop(0)
        dict_ops.setInDict(site_docs, tuple, tuple[len(tuple)-1])
    dict_ops.iterdict(site_docs)

    print(site_docs)
    return site_docs