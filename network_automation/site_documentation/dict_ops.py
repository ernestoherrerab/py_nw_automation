#! /usr/bin/env python
"""
Module for dictionary operations
"""
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