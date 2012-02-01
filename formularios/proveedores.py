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
Created on 30/01/2012 

@author: bogado

    Ventana CRUD de proveedores.

'''

import gtk, os, sys
if os.path.realpath(os.path.curdir).split(os.path.sep)[-1] == "formularios":
    os.chdir("..")
sys.path.append(".")
from formularios.ventana_generica import VentanaGenerica
from framework import pclases
from formularios.graficas import charting

class Proveedores(VentanaGenerica):
    def __init__(self, objeto = None, usuario = None, run = True):
        """
        Constructor. objeto puede ser un objeto de pclases con el que
        comenzar la ventana (en lugar del primero de la tabla, que es
        el que se muestra por defecto).
        """
        self.nombre_fichero_ventana = os.path.split(__file__)[-1]
        self.__clase = pclases.Proveedor
        self._objetoreciencreado = None
        if objeto and isinstance(objeto, self.__clase):
            VentanaGenerica.__init__(self, objeto = objeto, usuario = usuario, 
                                     run = False)
        elif objeto:
            VentanaGenerica.__init__(self, objeto = objeto, usuario = usuario, 
                                     clase = self.__clase, run = False)
        else:
            VentanaGenerica.__init__(self, clase = self.__clase, 
                                     usuario = usuario, run = False)
        if run:
            gtk.main()
    
def main():
    from formularios.options_ventana import parse_options
    params, opt_params = parse_options()
    ventana = Proveedores(*params, **opt_params)

if __name__ == "__main__":
    main()

