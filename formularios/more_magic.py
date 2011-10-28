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
## magic.py - Abre ventanas del modelo antiguo del lanzador de 
##            ginn desde el menú nuevo multiproceso.
###################################################################
## Changelog:
## 16/11/2010 -> Inicio 
## 
###################################################################

import os

class MoreMagic:
    """
    Clase para "envolver" el nuevo proceso e instanciar las variables 
    de objeto a mostrar y usuario.
    """
    def __init__(self, ventana, usuario = None, objeto = None):
        """
        ventana: Cadena de texto con la ruta a la ventana a abrir.
        usuario: Objeto usuario, ID de usuario o PUID del usuario.
        objeto: Objeto a mostrar, ID del objeto o PUID de pclases.
        """
        # 1.- Cambiar al directorio formularios, porque desde fuera no puedo 
        #     importar ventana (que importa pclases).
        actual = os.path.split(os.path.abspath(os.curdir))[-1]
        if actual != "formularios":
            os.chdir("formularios")
        # 2.- 


def main():
    from formularios.options_ventana import parse_options
    params, opt_params = parse_options()
    ventana = NombreVentana(*params, **opt_params) 
    
if __name__ == "__main__":
    main()

