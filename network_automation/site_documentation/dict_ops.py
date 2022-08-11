#! /usr/bin/env python
"""
Module for dictionary operations
"""
from functools import reduce
import operator
from random import randint

def getFromDict(input_dict, input_list):
    """ 
    Find value in nested dictionary using a list to iterate 
    through the input dictionary.
    In this case, the value will be the last element of the 
    file path given 
    """
    return reduce(operator.getitem, input_list, input_dict)

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
    """ Add Children key to files """
    for k,v in input_dict.copy().items():        
       if isinstance(v, dict):
           iterdict(v)
       else:
          if "children" not in input_dict:
              input_dict.pop(k, None)            
              input_dict["children"] = []
              input_dict["children"].append({"id": str(randint(1, 10000)), "name": v})
          else:
              input_dict.pop(k, None)
              input_dict["children"].append({"id": str(randint(1, 10000)), "name": v})
            
def restructure_data(input_dict):
    """Restructure Data for React"""
    output_dict = []
    for key in input_dict:
        
        if key!='children':
            id = str(randint(1, 10000))
            trans_dict = {"id": id, "name": key}
            trans_dict['children'] = restructure_data(input_dict[key])
        else:
            trans_dict = input_dict['children']
        output_dict.append(trans_dict)
    return output_dict