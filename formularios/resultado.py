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
Created on 17/05/2010

@author: bogado

    Clase que encapsula los resultados de búsqueda de Seeker.

'''

class Resultado:
    """
    Cada uno de los resultados del buscador es un objeto "Resultado" 
    que encapsula un registro de pclases.
    """
    
    def __init__(self, resultado_pclases):
        """
        Recibe un resultado de pclases (un objeto en realidad) y 
        lo encapsula dentro de un atributo propio.
        """
        self.resultado = resultado_pclases
        self.tabla = resultado_pclases.sqlmeta.table
        self.clase = resultado_pclases.__class__.__name__

    def __repr__(self):
        info = self.resultado.get_info()
        if info == "Información no disponible.": 
            info = self.resultado.__repr__()    # OJO: Hasta que todas las clases hayan redefinido el get_info.
        return info

    def get_id(self):
        """
        Devuelve el ID del objeto encapsulado.
        """
        return self.resultado.id

    def get_class(self):
        """
        Devuelve la clase del objeto de pclases encapsulado.
        """
        return type(self.resultado)

    def get_objeto_pclases(self):
        """
        Devuelve el objeto de pclases en sí.
        """
        return self.resultado

    def get_puid(self):
        return self.resultado.get_puid()

    def get_info(self):
        return self.resultado.get_info()

    def sync(self):
        self.resultado.sync()

    id = property(get_id)
    puid = property(get_puid)
    info = property(get_info)

