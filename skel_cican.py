#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
# Copyright (C) 2005-2010  Francisco José Rodríguez Bogado                    #
#                          <bogado@qinn.es>                                   #
#                                                                             #
# This file is part of $NAME.                                                 #
#                                                                             #
# $NAME is free software; you can redistribute it and/or modify               #
# it under the terms of the GNU General Public License as published by        #
# the Free Software Foundation; either version 2 of the License, or           #
# (at your option) any later version.                                         #
#                                                                             #
# $NAME is distributed in the hope that it will be useful,                    #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU General Public License for more details.                                #
#                                                                             #
# You should have received a copy of the GNU General Public License           #
# along with $NAME if not, write to the Free Software                         #
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA  #
###############################################################################


###################################################################
## <++>.py - <++>
###################################################################
## NOTAS:
## <++>
###################################################################
## Changelog:
## <++> -> <++> 
## 
###################################################################


import gtk, os, sys
if os.path.realpath(os.path.curdir).split(os.path.sep)[-1] == "formularios":
    os.chdir("..")
sys.path.append(".")
from formularios.ventana_generica import VentanaGenerica
from framework import pclases
import gobject
import utils

class NombreVentana(VentanaGenerica): # <++>(VentanaGenerica):
    def __init__(self, objeto = None, usuario = None, run = True):
        """
        Constructor. objeto puede ser un objeto de pclases con el que
        comenzar la ventana (en lugar del primero de la tabla, que es
        el que se muestra por defecto).
        """
        self.__clase = pclases.NombreClase # self.__clase = pclases.<++>   
        self.usuario = usuario
        VentanaGenerica.__init__(self, objeto = objeto, 
                                 usuario = self.usuario, 
                                 clase = self.__clase, run = False, 
                                 ventana_marco = '<++>.glade')
        connections = {}
        self.add_connections(connections)
        if run:
            gtk.main()


def main():
    from formularios.options_ventana import parse_options
    params, opt_params = parse_options()
    ventana = NombreVentana(*params, **opt_params) # ventana = <++>(*params, **opt_params)
    
if __name__ == "__main__":
    main()

