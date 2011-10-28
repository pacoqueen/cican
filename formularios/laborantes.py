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
Created on 23/07/2010

@author: bogado

    Ventana de laborantes.

'''

import gtk, os, sys
if os.path.realpath(os.path.curdir).split(os.path.sep)[-1] == "formularios":
    os.chdir("..")
sys.path.append(".")
from formularios.ventana_generica import VentanaGenerica
from framework import pclases
from formularios.adjuntos import add_boton_adjuntos
from formularios.fotos import add_boton_fotos, actualizar_foto

class VentanaLaborantes(VentanaGenerica):
    def __init__(self, objeto = None, usuario = None, run = True):
        """
        Constructor. objeto puede ser un objeto de pclases con el que
        comenzar la ventana (en lugar del primero de la tabla, que es
        el que se muestra por defecto).
        """
        self._objetoreciencreado = None
        self.__clase = pclases.Empleado
        meta = self.__clase.sqlmeta
        campos = meta.columns.keys() + [j.joinMethodName for j in meta.joins]
        campos_menos_foto = campos
        campos.remove("fotos")
        campos.remove("adjuntos")   # Adjuntos lleva su propio botón.
        if objeto and isinstance(objeto, self.__clase):
            VentanaGenerica.__init__(self, objeto = objeto, usuario = usuario, 
                                     run = False, campos = campos_menos_foto,
                                     ventana_marco = "laborantes.glade")
        elif objeto:
            VentanaGenerica.__init__(self, objeto = objeto, usuario = usuario, 
                                     clase = self.__clase, run = False, 
                                     campos = campos_menos_foto,
                                     ventana_marco = "laborantes.glade")
        else:
            VentanaGenerica.__init__(self, clase = self.__clase, 
                                     usuario = usuario, run = False, 
                                     campos = campos_menos_foto,
                                     ventana_marco = "laborantes.glade")
        add_boton_adjuntos(self.wids['botonera'], lambda: self.objeto, 
                           posicion = 5)
        bfoto, ifoto = add_boton_fotos(self.wids['hbox_foto'], 
                                       lambda *a, **kw: self.objeto, 
                                       posicion = 0)
        self.wids['b_fotos'], self.wids['i_foto'] = bfoto, ifoto
        if run:
            gtk.main()

    def rellenar_widgets(self, *args, **kw):
        try:
            actualizar_foto(self.wids['i_foto'], self.objeto)
        except KeyError:    # Todavía no está.
            pass
        super(VentanaLaborantes, self).rellenar_widgets(*args, **kw)
    
def main():
    from formularios.options_ventana import parse_options
    params, opt_params = parse_options()
    VentanaLaborantes(*params, **opt_params)


if __name__ == "__main__":
    main()

