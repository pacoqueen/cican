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
## peticiones.py - Solicitudes de recogida de material.
###################################################################

# TODO: USABILIDAD: Lo suyo sería que en la lista de contactos solo se vieran los contactos del cliente (todos si todavía no ha seleccionado ninguno) y que a la hora de crear uno nuevo, ya lo hiciera relacionándolo directamente con el cliente. Y que al seleccionar un contacto, si no hay cliente, ponga el cliente que le corresponda a la solicitud de recogida.


import gtk, os, sys
if os.path.realpath(os.path.curdir).split(os.path.sep)[-1] == "formularios":
    os.chdir("..")
sys.path.append(".")
from framework import pclases
from formularios.ventana_generica import VentanaGenerica
import gobject
import utils
import os
from framework.configuracion import ConfigConexion
from utils.ui import escalar_a
from reports.pedido import go_from_peticion as pedido
from utils.informes import abrir_pdf
from formularios.ventana_generica import actualizar_fecha 

class Peticiones(VentanaGenerica): 
    def __init__(self, objeto = None, usuario = None, run = True):
        """
        Constructor. objeto puede ser un objeto de pclases con el que
        comenzar la ventana (en lugar del primero de la tabla, que es
        el que se muestra por defecto).
        """
        __clase = pclases.Peticion
        VentanaGenerica.__init__(self, objeto = objeto, 
                                 usuario = usuario, 
                                 clase = __clase, run = False, 
                                 ventana_marco = 'peticiones.glade')
        connections = {}
        self.add_connections(connections)
        # Quito totales de ensayos:
        self.usuario = self.get_usuario()
        self.wids['totalizador_ensayos'].set_property("visible", False)
        if not self.usuario or self.usuario.nivel == 0:
            self.wids['usuarioID'].set_property("sensitive", True)
        else:
            self.wids['usuarioID'].set_property("sensitive", False)
        self.wids['e_fechaSolicitud'].connect("focus-out-event", 
            actualizar_fecha, None, self, 
            "fechaSolicitud")
        self.wids['b_buscar_fechaSolicitud'].connect("clicked", 
            lambda boton: self.wids['e_fechaSolicitud'].set_text(
                utils.fecha.str_fecha(
                    utils.ui.mostrar_calendario(
                        self.wids['e_fechaSolicitud'].get_text())
            )))
        if run:
            gtk.main()

    def nuevo(self, boton):
        VentanaGenerica.nuevo(self, boton)
        try:
            utils.ui.combo_set_from_db(self.wids['usuarioID'], self.usuario.id)
            self.objeto.usuario = self.usuario
        except AttributeError:
            utils.ui.combo_set_from_db(self.wids['usuarioID'], -1)
            self.objeto.usuario = None
        self.objeto.sync()
    
    def rellenar_widgets(self):
        # Experimentos con gaseosa:
        for wname in ("b_undo_fechaSolicitud", "b_save_fechaSolicitud"):
            # El de save ni siquiera tiene padre, y el de undo sale donde 
            # no debe.
            self.wids[wname].set_property("visible", False)
        pixbuf_logo = gtk.gdk.pixbuf_new_from_file(
            os.path.join('imagenes', ConfigConexion().get_logo()))
        pixbuf_logo = escalar_a(100, 75, pixbuf_logo)
        self.wids['logo'].set_from_pixbuf(pixbuf_logo)
        self.wids['e_id'].set_text(self.objeto and str(self.objeto.id) or "")
        VentanaGenerica.rellenar_widgets(self)

    def imprimir(self, boton):
        abrir_pdf(pedido(self.objeto))


def main():
    from formularios.options_ventana import parse_options
    params, opt_params = parse_options()
    ventana = Peticiones(*params, **opt_params) 
    
if __name__ == "__main__":
    main()

