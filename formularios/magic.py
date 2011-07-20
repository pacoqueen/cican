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
## magic.py - Copia ventanas desde ginn cambiando todo aquello que
##            "estorba" en el nuevo menú multiproceso.
###################################################################
## Changelog:
## 16/11/2010 -> Inicio 
## 
###################################################################

import sys, os

def check_parametros():
    from optparse import OptionParser
    usage = "uso: %prog origen [destino]\nSe copiará el archivo de la ruta "\
            "origen en destino. Si no se espefica el destino, copia al "\
            "directorio de trabajo con el sufijo 'g_' delante del nombre "\
            "del fichero."
    parser = OptionParser(usage = usage, version = "%prog 1.0")
    options, args = parser.parse_args()
    if len(args) < 1:
        print usage
        sys.exit(1)
    elif len(args) > 2:
        print usage
        sys.exit(2)
    origen = args[0]
    if len(args) == 1:
        destino = "g_%s" % os.path.basename(origen)
    else:
        destino = args[1]
    return origen, destino

def leer_y_cambiar(origen):
    """
    Lo va a meter todo en memoria, pero como ningún fuente es tan grande, 
    no me preocupa quedarme sin recursos.
    """
    src = open(origen, "r")
    contenido = []
    for linea in src.readlines():
        # El pclases lo importa a tavés de ventana. So... no hace falta.
        notported = {"import pclases": 
                        "import this # TODO: import sys, os; "
                        "if os.path.basename(os.path.realpath(os.path.curdir))"
                        " == os.path.basename(os.path.dirname("
                            "os.path.realpath(__file__))): "
                        "os.chdir('..'); "
                        "if '.' not in sys.path: sys.path.insert(0, '.'); from framework import pclases", 
        # El geninformes no está portado, so... ya se hará más adelante.
                     "import geninformes": None, 
        # El utils también se ha reestructurado. Aprovecho que python ya 
        # sabe dónde está por "ventana.py"
                     "from utils import _float as float": 
                        "from utils.numero import _float as float", 
        # Como de momento no hay informes, tampoco necesito esto:
                     "from informes import abrir_pdf": None, 
        # Ventanas de progreso y actividad
                     "from ventana_progreso import": 
                        "from utils.ventana_progreso import", 
        # Los cambios de SQLObject:
                     "._SO_columns": ".sqlmeta.columnList", 
        # Otro de utils:
                     "utils.preparar_": "utils.ui.preparar_", 
        # Y más de utils:
                     "import utils": "import utils.ui, utils.fecha", 
                     "utils.parse_fecha": "utils.fecha.parse_fecha", 
                     "import pclase2tv": "from utils import pclase2tv", 
                     "utils.dialogo": "utils.ui.dialogo", 
                     "utils.rellenar_lista": "utils.ui.rellenar_lista", 
                     "utils.float2str": "utils.numero.float2str", 
                     "utils.combo_set_from_db": "utils.ui.combo_set_from_db", 
                    }
        for marron in notported:
            ugly_hack = notported[marron]
            if ugly_hack == None:
                ugly_hack = "pass # TODO: " + marron
            linea = linea.replace(marron, ugly_hack)
        contenido.append(linea)
    src.close()
    return contenido

def escribir(contenido, destino):
    try:
        dst = open(destino, "w")
    except IOError:
        sys.stderr.write("Error de entrada/salida. No se pudo abrir %s." 
                         % destino)
        sys.exit(3)
    dst.writelines(contenido)
    dst.close()

def main():
    # 0.- Chequeo parámetros. Si uno, el nombre de destino lo elijo yo.
    origen, destino = check_parametros()
    # 1.- Lee fuente y cambia lo necesario.
    contenido = leer_y_cambiar(origen)
    # 2.- Vuelca a destino.
    escribir(contenido, destino)
    
if __name__ == "__main__":
    main()

