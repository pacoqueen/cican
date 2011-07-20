#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
# Copyright (C) 2010  Francisco José Rodríguez Bogado                         #
#                     <bogado@qinn.es>                                        #
#                                                                             #
# This file is part of F.P.-INN .                                             #
#                                                                             #
# F.P.-INN  is free software; you can redistribute it and/or modify           #
# it under the terms of the GNU General Public License as published by        #
# the Free Software Foundation; either version 2 of the License, or           #
# (at your option) any later version.                                         #
#                                                                             #
# F.P.-INN  is distributed in the hope that it will be useful,                #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU General Public License for more details.                                #
#                                                                             #
# You should have received a copy of the GNU General Public License           #
# along with F.P.-INN ; if not, write to the Free Software                    #
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA  #
###############################################################################


###################################################################
## fotos.py - Fotografías e imágenes.
###################################################################

import gtk, gobject, os, sys
try:
    from framework import pclases
except ImportError:
    if os.path.realpath(os.path.curdir).split(os.path.sep)[-1] == "formularios":
        os.chdir("..")
    root, dirs, files = os.walk(".").next()
    if "formularios" in dirs:
        sys.path.insert(0, ".")
    from framework import pclases
import utils

def set_foto(boton, func_empleado, wid_vista_previa, ventana_padre = None):
    """
    Adjunta una fotografía al objeto. 
    """
    print "Yeke!"
    empleado = func_empleado()
    print empleado
    if empleado:
        nomfich = utils.ui.dialogo_abrir(titulo = "BUSCAR FOTOGRAFÍA", 
                                         filtro_imagenes = True, 
                                         padre = ventana_padre)
        if nomfich != None:
            fich = open(nomfich, "rb")
            imagedata = ""
            binchunk = fich.read()
            while binchunk:
                imagedata += binchunk
                binchunk = fich.read()
            fich.close()
            imagen = pclases.Foto(empleado = empleado, 
                                  data = imagedata)
            imagen.store_from_file(nomfich)
            actualizar_vista_previa(wid_vista_previa, imagen)

def actualizar_vista_previa(wid_vista_previa, imagen):
    """
    Si se especifica la imagen, ignora la seleccionada en el iview.
    """
    try:
        pixbuf = imagen.get_pixbuf(maximo = 200)
    except AttributeError:
        pixbuf = imagen # Es el pixbuf directamente, no una instancia Foto.
    try:
        wid_vista_previa.set_from_pixbuf(pixbuf)
    except (AttributeError, TypeError): # Me han pasado el botón directamente.
        boton = wid_vista_previa
        wid_vista_previa = boton.get_image()
        if not wid_vista_previa:
            wid_vista_previa = gtk.Image()
            boton.set_image(wid_vista_previa)
        wid_vista_previa.set_from_pixbuf(pixbuf)

def actualizar_foto(wid_imagen, empleado = None):
    if empleado:
        try:
            foto = empleado.fotos[-1]
        except IndexError:
            pixbuf = pclases.Foto.get_default_pixbuf()
        else:
            pixbuf = foto.get_pixbuf()
        actualizar_vista_previa(wid_imagen, pixbuf)
    else:
        wid_imagen.set_from_stock(gtk.STOCK_NO, 200)


def add_boton_fotos(contenedor, func_get_objeto, posicion = None, 
                    args = [], kw = {}):
    """
    Añade un botón al contenedor indicado que abrirá la ventana de fotos 
    para el objeto que devuelva la ejecución de la función func_get_objeto.
    snippet:
        add_boton_fotos(self.wids['botonera'], lambda: self.objeto)
    """
    imagen = gtk.Image()
    empleado = func_get_objeto()
    actualizar_foto(imagen, empleado)
    minicontainer = gtk.VBox()
    minicontainer.pack_start(imagen, expand = False)
    boton = gtk.Button(label = "Cambiar foto")
    boton.connect("clicked", set_foto, func_get_objeto, imagen, *args, **kw)
    minicontainer.pack_start(boton, expand = False, fill = False)
    minicontainer.add(gtk.Label())
    contenedor.add(minicontainer)
    if not posicion is None:
        contenedor.reorder_child(minicontainer, posicion)
    contenedor.show_all()
    return boton, imagen


if __name__ == "__main__":
    try:
        usuario = usuario = pclases.Usuario.select(orderBy = "id")[0]
    except IndexError:
        usuario = None
    from formularios.laborantes import VentanaLaborantes
    try:
        vl = VentanaLaborantes(pclases.Empleado.select()[0], 
                               usuario = usuario, run = False)
    except IndexError:
        vl = VentanaLaborantes(pclases.Empleado(), usuario = usuario, 
                               run = False)
    gtk.main()

