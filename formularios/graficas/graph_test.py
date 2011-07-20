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

    Un par de pruebas con las gráficas de hamster-applet.

'''
import gtk
import charting


class BasicWindow:
    """
     # PyUML: Do not remove this line! # XMI_ID:_XW0G0u5DEd-QvZvwvxUy6Q
    """
    def __init__(self):
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_size_request(600, 500)
        window.connect("delete_event", lambda *args: gtk.main_quit())
        contenedor = gtk.VBox()
        ## Gráfica de barras horizontales
        claves = ["uno", "dos", "tres", "¡catorce!"]
        valores = [1, 2, 3, 14]
        self.grafica1 = charting.add_grafica_barras_horizontales(contenedor, 
                                                                 claves, 
                                                                 valores)
        ## Gráfica de rangos horizontales
        import random
        valores = []
        for clave in claves:
            rango_clave = []
            for i in xrange(random.randrange(1, 3)):
                rango = [random.random(), random.random()]
                rango.sort()
                rango = tuple([v * 60 * 24 for v in rango])
                rango_clave.append(rango)
            valores.append(rango_clave)
        self.grafica2 = charting.add_grafica_rangos(contenedor, claves, valores)
        ## Gráfica de barras verticales
        montones = ["x", "y", "z"]
        colores = dict([(stack, None) for stack in montones])
        valores = [[random.randint(0, 10) for j in range(len(montones))] 
                     for i in range(len(claves))]
        self.grafica3 = charting.add_grafica_barras_verticales(contenedor, 
                                        claves, valores, montones,  colores, 
                                        ver_botones_colores = True)
        ## Gráfica "simple"
        data = iter([["Beatrix Kiddo", 1], 
                     ["Bill", 1], 
                     ["Budd", 1], 
                     ["Elle Driver", 0], 
                     ["Vernita Green", 0], 
                     ["O-Ren Ishii", 0]])
        claves = []
        valores = []
        for c, v in data:
            claves.append(c)
            valores.append(v)
        self.grafica4 = charting.add_grafica_simple(contenedor, claves, 
                                                    valores)
        ## 
        window.add(contenedor)
        window.show_all()


def main():
    BasicWindow()
    gtk.main()


if __name__ == "__main__":
    main()
