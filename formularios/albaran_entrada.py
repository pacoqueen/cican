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

    Ventana de albaranes de entrada por recogida de material en obra.

'''

import gtk
from seeker import VentanaGenerica
from framework import pclases
from formularios.graficas import charting

class VentanaAlbaranesEntrada(VentanaGenerica):
    def __init__(self, objeto = None, usuario = None, run = True):
        """
        Constructor. objeto puede ser un objeto de pclases con el que
        comenzar la ventana (en lugar del primero de la tabla, que es
        el que se muestra por defecto).
        """
        __clase = pclases.AlbaranEntrada
        self._objetoreciencreado = None
        if objeto and isinstance(objeto, __clase):
            VentanaGenerica.__init__(self, objeto = objeto, usuario = usuario, 
                                     run = False, 
                                     ventana_marco = "albaran_entrada.glade")
        elif objeto:
            VentanaGenerica.__init__(self, objeto = objeto, usuario = usuario, 
                                     clase = __clase, run = False,
                                     ventana_marco = "albaran_entrada.glade")
        else:
            VentanaGenerica.__init__(self, clase = __clase, 
                                     usuario = usuario, run = False,
                                     ventana_marco = "albaran_entrada.glade")
        if run:
            gtk.main()

    def nuevo(self, *args, **kw):
        # Primero creo el nuevo objeto
        super(VentanaAlbaranesEntrada, self).nuevo(*args, **kw)
        # Y ahora intento actualizar el número de albarán
        numalbaran = pclases.AlbaranEntrada.get_siguiente_numalbaran_str()
        if not pclases.AlbaranEntrada.selectBy(numalbaran=numalbaran).count():
            self.objeto.numalbaran = numalbaran
            self.actualizar_ventana()
    
def main():
    from formularios.options_ventana import parse_options
    params, opt_params = parse_options()
    VentanaAlbaranesEntrada(*params, **opt_params)

if __name__ == "__main__":
    main()

