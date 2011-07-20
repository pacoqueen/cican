#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
# Copyright (C) 2008-2010 Francisco José Rodríguez Bogado                     #
#                         <frbogado@novaweb.es>                               #
#                                                                             #
#    This program is free software: you can redistribute it and/or modify     #
#    it under the terms of the GNU General Public License as published by     #
#    the Free Software Foundation, either version 3 of the License, or        #
#    (at your option) any later version.                                      #
#                                                                             #
#    This program is distributed in the hope that it will be useful,          #
#    but WITHOUT ANY WARRANTY; without even the implied warranty of           #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the            #
#    GNU General Public License for more details.                             #
#                                                                             #
#    You should have received a copy of the GNU General Public License        #
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.    #
#                                                                             #
###############################################################################

'''
Created on 15/05/2010

@author: bogado

    Utilidades sobre cadenas de caracteres.

'''

def eliminar_dobles_espacios(cad):
    """
    Devuelve la cadena "cad" asegurando que no quedan dos espacios consecutivos 
    en ninguna posición.
    """
    if cad:
        return reduce(lambda x, y: x[-1] == " " and y == " " and x or x+y, cad)
    return cad

def unificar_textos(lista, case_sensitive = False):
    """
    Devuelve una lista de textos donde no se repite ninguno. Ignora  
    espacios al principio y al final. Por defecto es "case insensitive". 
    Los textos los devuelve tal y como estén escritos en la primera aparición 
    de ellos en lista.
    """
    if not isinstance(lista, (list, tuple)):
        raise TypeError, "lista debe ser una lista, no un %s." % (type(lista))
    res = []
    for t in lista:
        if case_sensitive:
            tmp = tuple([i.strip() for i in res])
            tmp_t = t.strip()
        else:
            tmp = tuple([i.lower().strip() for i in res])
            tmp_t = t.lower().strip()
        if tmp_t not in tmp:
            res.append(t)
    return res

def wrap(text, width):
    """
    A word-wrap function that preserves existing line breaks
    and most spaces in the text. Expects that existing line
    breaks are posix newlines (\n).
    Sacado de http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/148061
    Desconozco la licencia. Eliminar en caso de que no sea compatible con la 
    GPL cuando la averigüe.
    """
    return reduce(lambda line, word, width=width: '%s%s%s' %
                  (line,
                   ' \n'[(len(line)-line.rfind('\n')-1
                         + len(word.split('\n',1)[0]
                              ) >= width)],
                   word),
                  text.split(' ')
                 )
