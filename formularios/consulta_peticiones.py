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
Created on 24/02/2011 

@author: bogado

    Peticiones sin laborante asignado. Desde aquí se podrán asignar laborantes 
    para recoger las muestras e imprimir un listado de ruta de cada uno.

'''
import pygtk
pygtk.require('2.0')
import gtk
import sys, os, datetime
if os.path.realpath(os.path.curdir).split(os.path.sep)[-1] == "formularios":
    os.chdir("..")
sys.path.append(".")
from framework import pclases
from ventana_consulta import VentanaConsulta

class PeticionesSinAsignar(VentanaConsulta): 
    def __init__(self, objeto = None, usuario = None, run = True):
        """
        Constructor. objeto puede ser un objeto de pclases con el que
        comenzar la ventana (en lugar del primero de la tabla, que es
        el que se muestra por defecto).
        """
        __clase = pclases.Peticion
        self.usuario = usuario
        VentanaConsulta.__init__(self, 
                                 usuario = self.usuario, 
                                 clase = __clase, 
                                 run = False, 
                                 ventana_marco="consulta_peticiones.glade", 
                                 filtros = ["empleadoID"], 
                                 filtros_defecto = {'empleadoID': -1}, 
                                 agrupar_por = "obraID")
        self.wids['ventana'].set_title('Peticiones de recogida')
        if run:
            gtk.main()
    
def main():
    from formularios.options_ventana import parse_options
    params, opt_params = parse_options()
    ventana = PeticionesSinAsignar(*params, **opt_params) 

if __name__ == "__main__":
    main()

