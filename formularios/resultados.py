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

    Ventana de resultados de ensayos.

'''

import gtk
from seeker import VentanaGenerica
from framework import pclases
from formularios.graficas import charting
from formularios.adjuntos import add_boton_adjuntos

class VentanaResultados(VentanaGenerica):
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
        if objeto and isinstance(objeto, pclases.Resultado):
            VentanaGenerica.__init__(self, objeto = objeto, usuario = usuario, 
                                     run = False)
        elif objeto:
            VentanaGenerica.__init__(self, objeto = objeto, usuario = usuario, 
                                     clase = pclases.Resultado, run = False)
        else:
            VentanaGenerica.__init__(self, clase = pclases.Resultado, 
                                     usuario = usuario, run = False)
        self._add_widget_grafico()
        add_boton_adjuntos(self.wids['botonera'], lambda: self.objeto)
        # Elementos que me interesa deshabilitar:
        self.wids['botonera_adjuntos'].set_property("visible", False)
        # Otros pequeños cambios:
        self.wids['label_relaciones'].set_text("Informes")
        if run:
            gtk.main()
    
    def _add_widget_grafico(self):
        """
        Añade un widget para mostrar un gráfico en una nueva pestaña de 
        la ventana.
        """
        try:
            wgrafica = self.wids['grafica']
        except KeyError:    # Efectivamente, no está creada.
            self.wids['grafica'] = gtk.Alignment(0.5, 0.5, 0.9, 0.9)
            self.wids['grafica'].set_property("visible", True)
            self.wids['notebook'].append_page(self.wids['grafica'], 
                                              gtk.Label("Gráfica"))
            self.grafica = charting.Chart(value_format = "%.1f",
                                          #max_bar_width = 20,
                                          #legend_width = 70,
                                          interactive = False)
            self.wids['grafica'].add(self.grafica)
            self.wids['grafica'].show_all()

    def actualizar_grafica(self, keys, data):
        """
        Actualiza (o crea) la gráfica contenida en el eventbox de la ventana.
        """
        try:
            self.grafica.plot(keys, data)
        except AttributeError: # Todavía no se ha creado el widget.
            self._add_widget_grafico()
            self.grafica.plot(keys, data)

    def actualizar_ventana(self, *args, **kw):
        """
        "Wrap" para el rellenar_widgets.
        """
        data = {}
        if self.objeto and self.objeto.muestra:
            for r in self.objeto.muestra.resultados:
                if r == self.objeto:
                    data["* %s" % r.get_info()] = r.valor
                else:
                    data[r.get_info()] = r.valor
        keys = sorted(data.keys(), key = lambda x: x[0])
        values = [data[key] for key in keys]
        self.actualizar_grafica(keys, values)
        super(VentanaResultados, self).actualizar_ventana(*args, **kw)

def main():
    """
    Parsea las opciones y abre la ventana en un nuevo proceso.
    """
    from formularios.options_ventana import parse_options
    params, opt_params = parse_options()
    VentanaResultados(*params, **opt_params)


if __name__ == "__main__":
    main()

