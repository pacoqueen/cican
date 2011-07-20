#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
# Copyright (C) 2005-2007  Francisco José Rodríguez Bogado                    #
#                          <bogado@qinn.es>                                   #
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
## adjuntos.py - Documentos adjuntos.
###################################################################

import gtk, gobject, os
from ventana import Ventana
from framework import pclases
import utils

class Adjuntos(Ventana):
    VENTANA = os.path.join(os.path.dirname(__file__), 
                           "glades", "adjuntos.glade")
    def __init__(self, resultado, usuario = None, run = True):
        self.resultado = resultado
        Ventana.__init__(self, self.VENTANA)
        connections = {'b_drop_adjunto/clicked': self.drop_adjunto,
                       'b_add_adjunto/clicked': self.add_adjunto,
                       'b_ver_adjunto/clicked': self.ver_adjunto,
                       'b_salir/clicked': self.salir, 
                       'tg_vista/toggled': self.cambiar_vista, 
                      }
        self.add_connections(connections)
        self.inicializar_ventana()
        self.rellenar_adjuntos()
        if run:
            gtk.main()
    
    def inicializar_ventana(self):
        """
        Inicializa los controles de la ventana, estableciendo sus
        valores por defecto, deshabilitando los innecesarios,
        rellenando los combos, formateando el TreeView -si lo hay-...
        """
        # Inicialmente no se muestra NADA. Sólo se le deja al
        # usuario la opción de buscar o crear nuevo.
        self.activar_widgets(False)
        self.wids['ventana'].set_title("Documentos adjuntos - %s"
                                        % self.resultado.get_puid())
        # Inicialización del resto de widgets:
        cols = (('Nombre', 'gobject.TYPE_STRING', True, True, True, self.cambiar_nombre_adjunto), 
                ('Observaciones', 'gobject.TYPE_STRING', True, True, False, self.cambiar_observaciones_adjunto),
                ('PUID', 'gobject.TYPE_STRING', False, False, False, None))
        utils.ui.preparar_listview(self.wids['tv_adjuntos'], cols)
        self.wids['tv_adjuntos'].connect("row-activated", 
                                         abrir_adjunto_from_tv)
        # XXX: A ver si puedo hacerlo con un IconView...
        self.wids['iv_adjuntos'] = gtk.IconView(
            gtk.ListStore(gobject.TYPE_STRING,  # Nombre 
                          gtk.gdk.Pixbuf,       # Icono 
                          gobject.TYPE_STRING)) # PUID
        self.wids['iv_adjuntos'].set_text_column(0)
        self.wids['iv_adjuntos'].set_pixbuf_column(1)
        self.wids['iv_adjuntos'].connect('item-activated', 
                                         abrir_adjunto_from_iview)
        scroll = gtk.ScrolledWindow()
        scroll.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        scroll.add(self.wids['iv_adjuntos'])
        self.wids['tv_adjuntos'].parent.parent.add(scroll)
        self.wids['tv_adjuntos'].parent.parent.reorder_child(scroll, 0)
        self.wids['tv_adjuntos'].parent.parent.show_all()
        self.wids['tv_adjuntos'].parent.set_property("visible", False)

    def cambiar_vista(self, tgbutton):
        """
        Alterna entre las vistas de icono y lista ocultando la que no 
        corresponde.
        """
        iconos = not tgbutton.get_active()
        self.wids['tv_adjuntos'].parent.set_property("visible", not iconos)
        self.wids['iv_adjuntos'].parent.set_property("visible", iconos)

    def activar_widgets(self, s, chequear_permisos = True):
        """
        Activa o desactiva (sensitive=True/False) todos 
        los widgets de la ventana que dependan del 
        objeto mostrado.
        Entrada: s debe ser True o False. En todo caso
        se evaluará como boolean.
        """
        if self.resultado == None:
            s = False
        ws = self.wids.keys()
        for w in ws:
            try:
                self.wids[w].set_sensitive(s)
            except Exception, msg:
                if pclases.DEBUG:
                    print "Widget problemático:", w, "Excepción:", msg
                    #import traceback
                    #traceback.print_last()
        if chequear_permisos:
            self.check_permisos(nombre_fichero_ventana = "adjuntos.py")

    def rellenar_widgets(self):
        """
        Introduce la información de la cuenta actual
        en los widgets.
        No se chequea que sea != None, así que
        hay que tener cuidado de no llamar a 
        esta función en ese caso.
        """
        self.rellenar_adjuntos()

    def rellenar_adjuntos(self):
        """
        Introduce los adjuntos del objeto en la tabla de adjuntos.
        """
        model = self.wids['tv_adjuntos'].get_model()
        modeliview = self.wids['iv_adjuntos'].get_model()
        model.clear()
        modeliview.clear()
        if self.resultado != None:
            docs = self.resultado.adjuntos[:]
            docs.sort(lambda x, y: pclases.orden_por_campo_o_id(x, y, "id"))
            for adjunto in self.resultado.adjuntos:
                model.append((adjunto.nombre, 
                              adjunto.observaciones, 
                              adjunto.get_puid()))
                icono = utils.ui.cargar_icono_mime(adjunto.get_ruta_completa())
                modeliview.append((adjunto.nombre, 
                                   icono, 
                                   adjunto.get_puid()))

    def cambiar_nombre_adjunto(self, cell, path, texto):
        model = self.wids['tv_adjuntos'].get_model() 
        iddoc = model[path][-1]
        pclases.getObjetoPUID(iddoc).nombre = texto
        model[path][0] = pclases.getObjetoPUID(iddoc).nombre

    def cambiar_observaciones_adjunto(self, cell, path, texto):
        model = self.wids['tv_adjuntos'].get_model() 
        iddoc = model[path][-1]
        pclases.getObjetoPUID(iddoc).observaciones = texto
        model[path][1] = pclases.getObjetoPUID(iddoc).observaciones

    def add_adjunto(self, boton):
        """
        Adjunta un documento a la factura de compra.
        """
        utils.ui.dialogo_adjuntar("ADJUNTAR DOCUMENTO", 
                                  self.resultado, 
                                  self.wids['ventana'])
        self.rellenar_adjuntos()

    def drop_adjunto(self, boton):
        """
        Elimina el adjunto seleccionado.
        """
        # TODO: FIXME: No funciona en la vista de iconos.
        model, iter = self.wids['tv_adjuntos'].get_selection().get_selected()
        if iter != None and utils.ui.dialogo(titulo = "BORRAR DOCUMENTO", 
                            texto = '¿Borrar documento adjunto seleccionado?', 
                            padre = self.wids['ventana']):
            docid = model[iter][-1]
            adjunto = pclases.getObjetoPUID(docid)
            from utils import fichero
            fichero.mover_a_tmp(adjunto.get_ruta_completa())
            adjunto.destroySelf()
            self.rellenar_adjuntos()

    def ver_adjunto(self, boton):
        """
        Intenta abrir el adjunto seleccionado.
        """
        from multi_open import open as mopen
        if self.wids['tv_adjuntos'].parent.get_property("visible"):
            model,iter=self.wids['tv_adjuntos'].get_selection().get_selected()
        else:
            paths = self.wids['iv_adjuntos'].get_selected_items()
            model = self.wids['iv_adjuntos'].get_model()
            iter = paths[0]
        if iter != None:
            docid = model[iter][-1]
            adjunto = pclases.getObjetoPUID(docid)
            self.wids['ventana'].window.set_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
            while gtk.events_pending(): gtk.main_iteration(False)
            try:
                if not mopen(adjunto.get_ruta_completa()):
                    utils.dialogo_info(titulo = "NO SOPORTADO", 
                                       texto = "La aplicación no conoce cómo abrir el tipo de fichero.", 
                                       padre = self.wids['ventana'])
            except:
                utils.dialogo_info(titulo = "ERROR", 
                                   texto = "Se produjo un error al abrir el archivo.\nLa plataforma no está soportada, no se conoce el tipo de archivo o no hay un programa asociado al mismo.", 
                                   padre = self.wids['ventana'])
            import gobject
            gobject.timeout_add(2000, lambda *args, **kw: self.wids['ventana'].window.set_cursor(None))


def abrir_adjunto_from_tv(tv, path, col):   # Código para adjuntos.
    """
    Abre el adjunto con el programa asociado al mime-type del mismo.
    """
    model = tv.get_model()
    id = model[path][-1]
    adjunto = pclases.getObjetoPUID(id)
    from multi_open import open as mopen
    mopen(adjunto.get_ruta_completa())

def abrir_adjunto_from_iview(iview, path):   # Código para adjuntos.
    """
    Abre el adjunto con el programa asociado al mime-type del mismo.
    """
    model = iview.get_model()
    puid = model[path][-1]
    adjunto = pclases.getObjetoPUID(puid)
    from multi_open import open as mopen
    mopen(adjunto.get_ruta_completa())

def add_boton_adjuntos(contenedor, func_get_objeto, posicion = None):
    """
    Añade un botón al contenedor indicado que abrirá la ventana de adjuntos 
    para el objeto que devuelva la ejecución de la función func_get_objeto.
    snippet:
        add_boton_adjuntos(self.wids['botonera'], lambda: self.objeto)
    """
    boton = gtk.Button(label = "Adjuntos...")
    boton.connect("clicked", abrir_adjuntos_de, func_get_objeto)
    contenedor.add(boton)
    if not posicion is None:
        contenedor.reorder_child(boton, posicion)
    contenedor.show_all()

def abrir_adjuntos_de(boton, func_get_objeto):
    objeto = func_get_objeto()
    if objeto != None:
        ventana_adjuntos = Adjuntos(objeto)
    else:
        pass    # ¿Debería mostrar un cuadro de diálogo de error o algo?

if __name__ == "__main__":
    pclases.DEBUG = True
    try:
        p = Adjuntos(pclases.Resultado.select()[0])
    except IndexError:
        p = Adjuntos(pclases.Resultado())
    
