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
Created on 24/02/2011 

@author: bogado

    Peticiones sin laborante asignado. Desde aquí se podrán asignar laborantes 
    para recoger las muestras e imprimir un listado de ruta de cada uno.

'''
import pygtk
pygtk.require('2.0')
import gtk
import sys, os, datetime
if os.path.realpath(os.path.curdir).split(os.path.sep)[-1] == "formularios":
    os.chdir("..")
sys.path.append(".")
from framework import pclases
from ventana_consulta import VentanaConsulta
from ventana_generica import _abrir_en_ventana_nueva as abrir, GALACTUS
import utils, utils.mapa

class PeticionesSinAsignar(VentanaConsulta): 
    def __init__(self, objeto = None, usuario = None, run = True, 
                 fecha = datetime.date.today()):
        """
        Constructor. objeto puede ser un objeto de pclases con el que
        comenzar la ventana (en lugar del primero de la tabla, que es
        el que se muestra por defecto).
        """
        __clase = pclases.Peticion
        self.__usuario = usuario
        if objeto:
            fecha = self.objeto.fechaRecogida
        VentanaConsulta.__init__(self, 
                                 usuario = usuario, 
                                 clase = __clase, 
                                 run = False, 
                                 ventana_marco="peticiones_sin_asignar.glade")
        self.build_tabla_laborantes()
        self.build_tabla_peticiones_sin_asignar()
        self.build_tabla_peticiones_asignadas()
        self.wids['b_asignar'].connect("clicked", self.asignar)
        self.actualizar_ventana()
        self.wids['calendario'].connect('day-selected',self.actualizar_ventana)
        self.wids['calendario'].select_month(fecha.month - 1, fecha.year)
        self.wids['calendario'].select_day(fecha.day)
        self.mapa = utils.mapa.Mapa()
        self.mapa.put_mapa(self.wids["vpaned1"])
        sel = self.wids['tv_sin_asignar'].get_selection()
        sel.connect("changed", self.actualizar_mapa)
        sel = self.wids['tv_asignadas'].get_selection()
        sel.connect("changed", self.actualizar_mapa, False)
        if run:
            gtk.main()

    def actualizar_mapa(self, sel, track = True, flag = True):
        model, paths = sel.get_selected_rows()
        for path in paths:
            puid = model[path][-1]
            obra = pclases.getObjetoPUID(puid)
            d = obra.direccion 
            try:
                self.mapa.centrar_mapa(d.lat, d.lon, zoom = 12, track = track, 
                                       flag = flag)
            except AttributeError:
                pass    # La obra no tiene dirección asignada en su ficha.

    def build_tabla_laborantes(self):
        cols = (("Nombre", "gobject.TYPE_STRING", False, True, True, None), 
                ("Recogidas asignadas", 
                    "gobject.TYPE_STRING", False, True, False, None), 
                ("PUID", "gobject.TYPE_STRING", False, False, False, None))
        utils.ui.preparar_treeview(self.wids['tv_laborantes'], cols)
        self.wids['tv_laborantes'].connect("row-activated", 
            self._abrir_en_ventana_nueva, self.__usuario, GALACTUS, None, 
            pclases.Empleado)

    def build_tabla_peticiones_asignadas(self):
        cols = (("Obra", "gobject.TYPE_STRING", False, True, True, None), 
                ("Dirección", "gobject.TYPE_STRING", False, True, False, None),
                ("Material", "gobject.TYPE_STRING", False, True, False, None), 
                ("PUID", "gobject.TYPE_STRING", False, False, False, None))
        utils.ui.preparar_listview(self.wids['tv_sin_asignar'], cols, 
                                   multi = True)
        self.wids['tv_sin_asignar'].connect("row-activated", 
            self._abrir_en_ventana_nueva, self.__usuario, GALACTUS, None, 
            pclases.Peticion)

    def build_tabla_peticiones_sin_asignar(self):
        cols = (("Obra", "gobject.TYPE_STRING", False, True, True, None), 
                ("Dirección", "gobject.TYPE_STRING", False, True, False, None),
                ("Material", "gobject.TYPE_STRING", False, True, False, None), 
                ("Laborante", "gobject.TYPE_STRING", False, True, False, None), 
                ("PUID", "gobject.TYPE_STRING", False, False, False, None))
        utils.ui.preparar_listview(self.wids['tv_asignadas'], cols)
        self.wids['tv_asignadas'].connect("row-activated", 
            self._abrir_en_ventana_nueva, self.__usuario, GALACTUS, None, 
            pclases.Peticion)

    def _abrir_en_ventana_nueva(self, *args, **kw):
        abrir(*args, **kw)
        self.actualizar_ventana()
    
    def rellenar_widgets(self):
        self.rellenar_tabla_laborantes()
        self.rellenar_tablas_peticiones()

    def rellenar_tabla_laborantes(self):
        model = self.wids['tv_laborantes'].get_model()
        model.clear()
        padres = {}
        for e in pclases.Empleado.buscar_laborantes():
            padres[e] = model.append(None, (e.get_info(), 
                                            "", 
                                            e.get_puid()))
        fecha_seleccionada = self.get_fecha_seleccionada() 
        for p in pclases.Peticion.selectBy(fechaRecogida = fecha_seleccionada):
            laborante = p.empleado
            try:
                padre = padres[laborante]
            except KeyError:
                # El laborante ya no lo es, así que no lo listo.
                pass
            else:
                model.append(padre, ("", p.get_info(), p.get_puid()))
                try:
                    model[padre][1] = utils.numero.float2str(
                        utils.numero._float(model[padre][1]) + 1, precision=0)
                except (TypeError, ValueError):
                    model[padre][1] = "1"

    def get_fecha_seleccionada(self):
        """
        Devuelve la fecha del gtk.Calendar pero como un datetime.
        """
        y, m, d = self.wids['calendario'].get_date()
        fecha = datetime.date(y, m+1, d)    # Mes empieza en 0 en gtk.Calendar
        return fecha

    def rellenar_tablas_peticiones(self):
        fecha_seleccionada = self.get_fecha_seleccionada() 
        self.wids['tv_sin_asignar'].get_model().clear()
        self.wids['tv_asignadas'].get_model().clear()
        for p in pclases.Peticion.selectBy(fechaRecogida = fecha_seleccionada):
            fila = ((p.obra and p.obra.get_info() or "", 
                     p.direccion and p.direccion.get_direccion_completa() 
                        or "", 
                     p.material and p.material.get_info() or ""))
            if not p.empleado:   # No asignada
                model = self.wids['tv_sin_asignar'].get_model()
            else:
                model = self.wids['tv_asignadas'].get_model()
                fila += (p.empleado.get_nombre_completo(), )
            fila += (p.get_puid(), )
            model.append(fila)
    
    def asignar(self, boton):
        model, iter = self.wids['tv_laborantes'].get_selection().get_selected()
        if not iter:
            utils.ui.dialogo_info(titulo = "SELECCIONE UN LABORANTE", 
                texto = "Debe seleccionar un laborante al que asignar las "
                        "peticiones de recogida de material.", 
                padre = self.wids['ventana'])
        else:
            empleado = pclases.getObjetoPUID(model[iter][-1])
            sel = self.wids['tv_sin_asignar'].get_selection()  
            sel.selected_foreach(self.asiganda, empleado)
            self.actualizar_ventana()
    
    def asiganda(self, treemodel, path, iter, laborante):
        p = pclases.getObjetoPUID(treemodel[iter][-1])
        p.empleado = laborante
        p.sync()

    def imprimir(self, boton):
        """

        Imprime una hoja de ruta por cada laborante. Si se ha seleccionado 
        alguno, entonces solo imprime su hoja de ruta.
        """
        model, iter = self.wids['tv_laborantes'].get_selection().get_selected()
        if not iter:    # Imprimir para todos:
            laborantes = []
            for fila in model:
                puid = fila[-1]
                laborante = pclases.getObjetoPUID(puid)
                laborantes.append(laborante)
        else:
            puid = model[iter][-1]
            laborante = pclases.getObjetoPUID(puid)
            laborantes = [laborante]
        dia = self.get_fecha_seleccionada()
        for laborante in laborantes:
            abrir_hoja_de_ruta(laborante, dia)


def abrir_hoja_de_ruta(laborante, dia):
    """
    Genera y abre un PDF con la hoja de ruta del laborante para el día 
    recibido.
    """
    from reports import hoja_de_ruta
    from utils.informes import abrir_pdf 
    peticiones = laborante.get_peticiones(dia)
    pdf_hoja_ruta = hoja_de_ruta.hoja_ruta(laborante, peticiones)
    abrir_pdf(pdf_hoja_ruta)

def main():
    from formularios.options_ventana import parse_options
    params, opt_params = parse_options()
    ventana = PeticionesSinAsignar(*params, **opt_params) 

if __name__ == "__main__":
    main()

