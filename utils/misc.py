#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Utilidades varias.
"""

def aplanar(l):
    """
    Devuelve una lista "plana" a partir de «l».
    """
    res = []
    for item in l:
        if not hasattr(item, "__iter__"):
            res.append(item)
        else:
            res += aplanar(item)
    return res

