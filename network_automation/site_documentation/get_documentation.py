#! /usr/bin/env python
"""
Module to display the available diagrams
"""

from pathlib import Path, PurePath
from functools import reduce
import operator

def getFromDict(input_dict, input_list):
    """ 
    Find value in nested dictionary using a list to iterate 
    through the input dictionary.
    In this case, the value will be the last element of the 
    file path given 
    """
    return reduce(operator.getitem, input_list, input_dict)

def find_key(input_dict, value):
    for k,v in input_dict.items():
        if isinstance(v, dict):
            p = find_key(v, value)
            if p:
                return [k] + p
        elif v == value:
            return [k]

def setInDict(input_dict, input_list, value):
    """
    Gives a given value to the dictionary key found upon the
    iteration of the input dictionary.
    """
    getFromDict(input_dict, input_list[:-1])[input_list[-1]] = value

def dict_merge(dct, merge_dct):
    """ Merge nested dictionaries """

    for k, _ in merge_dct.items():
        if k in dct: 
            dict_merge(dct[k], merge_dct[k])
        else:
            dct[k] = merge_dct[k]

def iterdict(input_dict):
  for k,v in input_dict.copy().items():        
     if isinstance(v, dict):
         iterdict(v)
     else:
        if "files" not in input_dict:
            input_dict.pop(k, None)            
            input_dict["files"] = []
            input_dict["files"].append(v)
        else:
            input_dict.pop(k, None)
            input_dict["files"].append(v)
         


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
        dict_merge(site_docs, item)

    for tuple in tupled_tree:
        tuple = list(tuple)
        tuple.pop(0)
        setInDict(site_docs, tuple, tuple[len(tuple)-1])
        
    iterdict(site_docs)
    print(site_docs)