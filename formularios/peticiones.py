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


import gtk
from seeker import VentanaGenerica
from framework import pclases
import gobject
import utils
import os
from framework.configuracion import ConfigConexion
from utils.ui import escalar_a

class Peticiones(VentanaGenerica): 
    def __init__(self, objeto = None, usuario = None, run = True):
        """
        Constructor. objeto puede ser un objeto de pclases con el que
        comenzar la ventana (en lugar del primero de la tabla, que es
        el que se muestra por defecto).
        """
        __clase = pclases.Peticion
        self.usuario = usuario
        VentanaGenerica.__init__(self, objeto = objeto, 
                                 usuario = self.usuario, 
                                 clase = __clase, run = False, 
                                 ventana_marco = 'peticiones.glade')
        connections = {}
        self.add_connections(connections)
        # Quito totales de ensayos:
        self.wids['totalizador_ensayos'].set_property("visible", False)
        if run:
            gtk.main()
    
    def rellenar_widgets(self):
        # Experimentos con gaseosa:
        for wname in ("label5", "e_fechaSolicitud", "b_buscar_fechaSolicitud", 
                      "b_undo_fechaSolicitud", "b_save_fechaSolicitud"):
            self.wids[wname].set_property("visible", False)
        pixbuf_logo = gtk.gdk.pixbuf_new_from_file(
            os.path.join('imagenes', ConfigConexion().get_logo()))
        pixbuf_logo = escalar_a(100, 75, pixbuf_logo)
        self.wids['logo'].set_from_pixbuf(pixbuf_logo)
        self.wids['e_id'].set_text(self.objeto and str(self.objeto.id) or "")
        VentanaGenerica.rellenar_widgets(self)


def main():
    from formularios.options_ventana import parse_options
    params, opt_params = parse_options()
    ventana = Peticiones(*params, **opt_params) 
    
if __name__ == "__main__":
    main()

