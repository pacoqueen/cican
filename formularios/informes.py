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
Created on 18/05/2010

@author: bogado

    Ventana de informes de ensayos.

'''

import gtk, os, sys
if (os.path.realpath(os.path.curdir).split(os.path.sep)[-1] == 
    os.path.dirname(os.path.abspath(__file__)).split(os.path.sep)[-1]):
    os.chdir("..")
sys.path.append(".")
from formularios.ventana_generica import VentanaGenerica
from framework import pclases
from formularios.graficas import charting
from formularios.adjuntos import add_boton_adjuntos

class VentanaInformes(VentanaGenerica):
    def __init__(self, objeto = None, usuario = None, run = True):
        """
        Constructor. objeto puede ser un objeto de pclases con el que
        comenzar la ventana (en lugar del primero de la tabla, que es
        el que se muestra por defecto).
        """
        if pclases.DEBUG: 
            print "objeto", objeto
            print "usuario", usuario
            print "run", run
        self._objetoreciencreado = None
        if objeto and isinstance(objeto, pclases.Informe):
            VentanaGenerica.__init__(self, objeto = objeto, usuario = usuario, 
                                     run = False)
        elif objeto:
            VentanaGenerica.__init__(self, objeto = objeto, usuario = usuario, 
                                     clase = pclases.Informe, run = False)
        else:
            VentanaGenerica.__init__(self, clase = pclases.Informe, 
                                     usuario = usuario, run = False)
        add_boton_adjuntos(self.wids['botonera'], lambda: self.objeto)
        # Elementos que me interesa deshabilitar:
        for nombrecampo in ("lineaDeVentaID", ):
            w = self.widgets_campos[nombrecampo]
            for c in w.parent.parent.parent.get_children():
                c.set_property("visible", False)
        self.wids['totalizador_resultados'].set_property("visible", False)
        self.wids['container_adjuntos'].set_property("visible", False)
        # Widgets no editables de campos calculados:
        self.add_campo_calculado("get_str_muestras", 
                                 etiqueta = "Códigos de muestra", 
                                 nombre = "muestras", 
                                 campo = "codigo")
        if run:
            gtk.main()
    
    def actualizar_ventana(self, *args, **kw):
        """
        "Wrap" para el rellenar_widgets.
        """
        super(VentanaInformes, self).actualizar_ventana(*args, **kw)


def main():
    """
    Parsea las opciones y abre la ventana en un nuevo proceso.
    """
    from formularios.options_ventana import parse_options
    params, opt_params = parse_options()
    VentanaInformes(*params, **opt_params)


if __name__ == "__main__":
    main()

