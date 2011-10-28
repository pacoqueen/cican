#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
# Copyright (C) 2007 Francisco José Rodríguez Bogado                          #
#                    (bogado@qinn.es)                                         #
#                                                                             #
# This file is part of Dent-Inn.                                              #
#                                                                             #
# Dent-Inn is free software; you can redistribute it and/or modify            #
# it under the terms of the GNU General Public License as published by        #
# the Free Software Foundation; either version 2 of the License, or           #
# (at your option) any later version.                                         #
#                                                                             #
# Dent-Inn is distributed in the hope that it will be useful,                 #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU General Public License for more details.                                #
#                                                                             #
# You should have received a copy of the GNU General Public License           #
# along with Dent-Inn; if not, write to the Free Software                     #
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA  #
###############################################################################

###################################################################
## trazabilidad.py - Trazabilidad GENERAL de cualquier registro.
###################################################################
## NOTAS:
##  
## ----------------------------------------------------------------
##  
###################################################################
## Changelog:
## 24 de mayo de 2006 -> Inicio
## 24 de mayo de 2006 -> It's alive!
## 9 de diciembre de 2006 -> Añadida consola.
###################################################################
## 
###################################################################

import os 
import pygtk
pygtk.require('2.0')
import gtk, gtk.glade, time 
from ventana import Ventana
from framework import pclases
import utils
import cmdgtk

class Trazabilidad(Ventana):
    """
    Ventana de trazabilidad interna de objetos.
    Acepta tanto códigos de trazabilidad como consultas a la BD de SQLObject.
    """
    def __init__(self, objeto = None, usuario = None, ventana_padre = None, locals_adicionales = {}):
        try:
            Ventana.__init__(self, 'trazabilidad.glade', objeto)
        except:     # Tal vez me estén llamando desde otro directorio
            Ventana.__init__(self, os.path.join('..', 'formularios', 'trazabilidad.glade'), objeto)
        connections = {'b_salir/clicked': self.salir,
                       'b_buscar/clicked': self.buscar}
        self.add_connections(connections)
        cols = (('ID', 'gobject.TYPE_STRING', False, False, False, None),
                ('campo', 'gobject.TYPE_STRING', False, False, False, None),
                ('valor', 'gobject.TYPE_STRING', True, False, True, self.cambiar_valor),
                ('clase', 'gobject.TYPE_STRING', False, False, False, None))
        utils.ui.preparar_treeview(self.wids['tv_datos'], cols)
        self.wids['e_num'].connect("key_press_event", self.pasar_foco)
        self.wids['tv_datos'].connect("row-expanded", self.expandir)
        self.wids['tv_datos'].connect("row-collapsed", self.cerrar)
        self.wids['e_search'].set_property("visible", False)
        import pyconsole
        vars_locales = locals()
        for k in locals_adicionales:
            vars_locales[k] = locals_adicionales[k] 
        pyconsole.attach_console(self.wids['contenedor_consola'], 
                                 banner = "Consola python de depuración GINN", 
                                 script_inicio = """import sys, os, pygtk, gtk, gtk.glade, utils
from framework import pclases
import datetime
if os.path.realpath(os.path.curdir).split(os.path.sep)[-1] == "formularios":
    os.chdir("..")
sys.path.append(".")
from formularios.ventana_generica import VentanaGenerica as Ver
dir()
#Ver(self.objeto)
""", 
                                            locals = vars_locales)
        if objeto != None:
            self.rellenar_datos(objeto)
        cmd_gtk = cmdgtk.CmdGTK()
        cmd_gtk.attach_to(self.wids['boxcmd'])
        #-----------------------------------------------------------------------------------------------#
        def comprobar_que_no_me_hace_el_gato(paned, scrolltype_or_allocation_or_requisition = None):    #
            width = self.wids['ventana'].get_size()[0]                                                  #
            MIN =  width / 2                                                                            #
            MAX = width - 100                                                                           #
            posactual = paned.get_position()                                                            #
            if posactual < MIN:                                                                         #
                paned.set_position(MIN)                                                                 #
            elif posactual > MAX:                                                                       #
                paned.set_position(MAX)                                                                 #
        #-----------------------------------------------------------------------------------------------#
        self.wids['hpaned1'].connect("size_request", comprobar_que_no_me_hace_el_gato)
        self.wids['ventana'].resize(800, 600)
        self.wids['hpaned1'].set_position(self.wids['ventana'].get_size()[0] / 2)
        self.wids['ventana'].set_position(gtk.WIN_POS_CENTER)
        gtk.main()

    def pasar_foco(self, widget, event):
        if event.keyval == 65293 or event.keyval == 65421:
            self.wids['b_buscar'].grab_focus()

    def chequear_cambios(self):
        pass

    def buscar(self, b):
        a_buscar = self.wids['e_num'].get_text()
        if "pclases." in a_buscar and ("select" in a_buscar or "get" in a_buscar):
            try:
                self.rellenar_datos(eval(a_buscar))
            except:
                utils.ui.dialogo_info(titulo = "ERROR EN CONSULTA", 
                                   texto = "La consulta:\n%s\nprovocó una excepción." % a_buscar,
                                   padre = self.wids['ventana'])
        else:
            import seeker
            buscador = seeker.Seeker()
            buscador.buscar(a_buscar)
            if buscador.resultados:
                self.rellenar_datos(buscador.resultados[0].resultado)
        

    def rellenar_datos(self, articulo):
        model = self.wids['tv_datos'].get_model()
        model.clear()
        iter = self.insertar_rama(articulo, None, model)
    
    def insertar_rama(self, objeto, padre, model):
        iter = self.insertar_nombre(objeto, padre, model)
        self.insertar_campos(objeto, iter, model)
        self.insertar_ajenos(objeto, iter, model)
        self.insertar_multiples(objeto, iter, model)
        return iter
    
    def insertar_nombre(self, objeto, padre, model, nombre_opcional = ""):
        if objeto == None:
            iter = model.append(padre, ("", 
                                        nombre_opcional, 
                                        "", 
                                        ""))
            return None
        else:
            try:
                nombretabla = objeto.sqlmeta.table
            except AttributeError: # SQLObject <= 0.6.1
                nombretabla = objeto._table
            iter = model.append(padre, (objeto.id, 
                                        nombretabla, 
                                        "", 
                                        objeto.__class__.__name__))
            return iter
         
    def insertar_campos(self, objeto, padre, model):
        """
        Inserta los campos del objeto colgando de la rama "iter".
        Siempre empieza por el ID y el nombre de la tabla del objeto y 
        a continuación sus campos.
        Devuelve el iter del objeto insertado.
        """
        if padre == None: return
        try:
            campos = [c for c in objeto._SO_columnDict 
                      if not c.upper().endswith('ID')]
        except AttributeError:  # SQLObject > 0.6.1
            campos = [c for c in objeto.sqlmeta.columns
                      if not c.upper().endswith("ID")]
        for campo in campos:
            model.append(padre, ("", campo, getattr(objeto, campo), ""))
        # return iter

    def insertar_ajenos(self, objeto, padre, model):
        """
        Inserta los nombres de las claves ajenas del objeto
        con un "child" vacío para poder mostrar el desplegable y
        rellenar los campos de la clave ajena en cuestión en caso
        de que se despliegue.
        """
        if padre == None: return
        try:
            ajenas = [c for c in objeto._SO_columnDict 
                      if c.upper().endswith('ID')]
        except AttributeError:  # SQLObject > 0.6.1
            ajenas = [c for c in objeto.sqlmeta.columns
                      if c.upper().endswith('ID')]
        for ajena in ajenas:
            reg_ajena = ajena[:-2]
            obj_d = getattr(objeto, reg_ajena)
            iter = self.insertar_nombre(obj_d, padre, model, reg_ajena)
            model.append(iter, ("", "", "", ""))

    def insertar_multiples(self, objeto, padre, model):
        """
        Inserta un campo con desplegable por cada relación a muchos 
        del objeto, y dentro de éste tantos nombres de la tabla ajena
        como tuplas relacionadas que tenga.
        Además, por cada tupla creará un "child" vacío que se susituirá 
        por los datos de este registro cuando expanda la fila.
        """
        if padre == None: return
        try:
            multiples = objeto._SO_joinList
        except AttributeError:  # SQLObject > 0.6.1
            multiples = objeto.sqlmeta.joins
        for multiple in multiples:
            lista_objs = getattr(objeto, multiple.joinMethodName)
            # print multiple.joinMethodName, lista_objs
            for obj_d in lista_objs:
                iter = self.insertar_nombre(obj_d, padre, model, multiple.otherClassName)
                model.append(iter, ("", "", "", ""))
    
    def expandir(self, tv, iter, path):
        model = tv.get_model()
        child = model[path].iterchildren().next()
        if child[0] == "" and \
           child[1] == "" and \
           child[2] == "" and \
           child[3] == "":
            model.remove(child.iter)
            id = int(model[path][0])
            clase = model[path][-1]
#            print clase, id
            try:
                objeto = eval('pclases.%s.get(%d)' % (clase, id))
            except pclases.SQLObjectNotFound:
                utils.ui.dialogo_info(titulo = "ERROR", 
                    texto = "El objeto %s con ID %d no existe." % (clase, id))
            padre = model.get_iter(path)
            try:
                objeto.sync()
            except pclases.SQLObjectNotFound:
                model[path][0] = ""
                model[path][2] = ""
                model[path][3] = ""
            self.insertar_campos(objeto, padre, model)
            self.insertar_ajenos(objeto, padre, model)
            self.insertar_multiples(objeto, padre, model)
            tv.expand_row(path, False)

    def cerrar(self, tv, iter, path):
        model = tv.get_model()
        iterador = model[path].iterchildren()
        try:
            hijo = iterador.next()
            while (1):
                model.remove(hijo.iter)
                hijo = iterador.next()
        except StopIteration:
            pass
        model.append(iter, ("", "", "", ""))

    def cambiar_valor(self, cell, path, text):
        model = self.wids['tv_datos'].get_model()
        if model[path][0] == "":
            if model[path].parent != None:
                id = model[path].parent[0]
                clase = model[path].parent[-1]
                campo = model[path][1]
                objeto = eval("pclases.%s.get(%d)" % (clase, int(id)))
                objeto.syncUpdate()
                try:
                    setattr(objeto, campo, text)
                    model[path][2] = getattr(objeto, campo)
                except:
                    utils.ui.dialogo_info(titulo = "ERROR", 
                        texto = "Valor incorrecto para este campo.")


if __name__ == '__main__':
    t = Trazabilidad()
