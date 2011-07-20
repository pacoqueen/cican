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
Created on 25/05/2010

@author: bogado

    Utilidades con ficheros.

'''

import os

def mover_a_tmp(ruta):
    """
    Mueve el fichero apuntado por "ruta" al directorio temporal del SO.
    """
    from tempfile import gettempdir
    import shutil
    try:
        shutil.move(ruta, gettempdir())
    except IOError:
        print "fichero::mover_a_tmp -> Fichero %s no existe." % (ruta)

def get_raiz_como_ruta_relativa(diractual = ".", limite = 3):
    """
    Devuelve la ruta relativa al directorio raíz de la aplicación partiendo 
    del directorio de trabajo actual.
    """
    #limite = 3
    while limite:
        for root, dirs, files in os.walk(diractual):
            #print limite, diractual, dirs
            if "framework" in dirs:
                return diractual
        return get_raiz_como_ruta_relativa("..", limite - 1)
    #    limite -= 1
    #    diractual = os.path.join("..", diractual)
    raise RuntimeError, "utils::get_raiz_como_ruta_relativa ->"\
                        " ¡No sé en qué directorio estoy!"
    

