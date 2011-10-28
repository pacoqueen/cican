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
Created on 01/06/2011 

@author: bogado

    Ventana CRUD de direcciones.

'''

import os
import gtk, os, sys
if os.path.realpath(os.path.curdir).split(os.path.sep)[-1] == "formularios":
    os.chdir("..")
sys.path.append(".")
from formularios.ventana_generica import VentanaGenerica
from framework import pclases
from formularios.graficas import charting
import utils.ui
from utils.mapa import Mapa

class Direcciones(VentanaGenerica):
    def __init__(self, objeto = None, usuario = None, run = True):
        """
        Constructor. objeto puede ser un objeto de pclases con el que
        comenzar la ventana (en lugar del primero de la tabla, que es
        el que se muestra por defecto).
        """
        self.__clase = pclases.Direccion
        self._objetoreciencreado = None
        self.mapa = Mapa()
        if objeto and isinstance(objeto, self.__clase):
            VentanaGenerica.__init__(self, objeto = objeto, usuario = usuario, 
                                     run = False, 
                                     ventana_marco = "direccion.glade")
        elif objeto:
            VentanaGenerica.__init__(self, objeto = objeto, usuario = usuario, 
                                     clase = self.__clase, run = False,
                                     ventana_marco = "direccion.glade")
        else:
            VentanaGenerica.__init__(self, clase = self.__clase, 
                                     usuario = usuario, run = False,
                                     ventana_marco = "direccion.glade")
        self.put_mapa()
        # Si elijo un código postal, quiero que la ciudad se rellene sola:
        self.wids['codigoPostalID'].connect("changed", self.rellenar_ciudad)
        self.wids['codigoPostalID'].connect("focus-out-event", 
                                            self.rellenar_ciudad)
        self.wids['b_nuevo_cp'].connect("clicked", self.nuevo_cp)
        if run:
            gtk.main()

    def put_mapa(self):
        m = self.wids['mapa_container']
        self.mapa.put_mapa(m)

    def actualizar_mapa(self, actualizar_objeto = True):
        # OJO: Por defecto SIEMPRE va a intentar conectarse a Google. En 
        # caso de trabajar sin conexión a Internet o cuando la dirección no 
        # se encuentre, esto será un coñazo. FIXME
        if not self.objeto.lat or not self.objeto.lon:
            strdireccion = self.objeto.get_direccion_buscable()
            lat, lon = self.mapa.get_latlon(strdireccion)
            if lat and lon:
                self.objeto.lat = lat
                self.objeto.lon = lon
                self.objeto.syncUpdate()
                self.rellenar_widgets()
        try:
            self.mapa.centrar_mapa(self.objeto.lat, self.objeto.lon, 
                                   #zoom = 5, 
                                   track = False, flag = True)
            #print self.mapa.zoom
        except ValueError:
            pass    # La dirección es incorrecta o no se ha encontrado.

    def actualizar_ventana(self, *args, **kw):
        VentanaGenerica.actualizar_ventana(self, *args, **kw)
        self.actualizar_mapa()

    def nuevo_cp(self, boton):
        """
        Crea un nuevo código postal tras asegurarme de que no está repetido. 
        """
        res = None
        cp = utils.ui.dialogo_entrada(titulo = "NUEVO CÓDIGO POSTAL", 
            texto = "Introduzca el código postal:", 
            valor_por_defecto = self.wids['codigoPostalID'].child.get_text(), 
            padre = self.wids['ventana'])
        if cp:
            if pclases.CodigoPostal.selectBy(cp = cp.strip()).count() == 0:
                nombre_ciudad = utils.ui.dialogo_entrada(titulo = "CIUDAD", 
                    texto = "Teclee la ciudad a la que pertenece "
                            "el código postal:", 
                    padre = self.wids['ventana'])
                ciudad = buscar_ciudad_en_bd(nombre_ciudad, 
                                             self.wids['ventana'])
                if ciudad:
                    res = pclases.CodigoPostal(cp = cp, ciudad = ciudad)
            else:
                utils.ui.dialogo_info(titulo = "CÓDIGO EXISTENTE", 
                    texto = "El código postal ya existe.", 
                    padre = self.wids['ventana'])
        if res:
            model = self.wids['codigoPostalID'].get_model()
            model.append((res.id, res.cp))
            utils.ui.combo_set_from_db(self.wids['codigoPostalID'], res.id)
        return res

    def rellenar_ciudad(self, combo, *args, **kw):
        """
        Rellena el combo de ciudad con el correspondiente al código postal.
        """
        #cpid = utils.ui.combo_get_value(combo)
        #try:
        #    cp = pclases.CodigoPostal.get(cpid)
        #except (pclases.SQLObjectNotFound, AssertionError):
        #    return  # El código postal no es de la base de datos.
        texto_cp = combo.child.get_text()
        try:
            cp = pclases.CodigoPostal.selectBy(cp = texto_cp)[0]
        except (IndexError):
            return  # El código postal no es de la base de datos.
        utils.ui.combo_set_from_db(combo, cp.id)
        try:
            utils.ui.combo_set_from_db(self.wids['ciudadID'], cp.ciudadID)
        except AttributeError:
            pass    # Algo falló en la base de datos. No ciudad o no CP.
        else:
            self.wids['paisID'].grab_focus()


def buscar_ciudad_en_bd(nombre, ventana_padre = None):
    """
    Busca la ciudad que más se parezca al nombre recibido y devuelve el objeto 
    o crea una nueva ciudad. Devuelve None si no se parece ninguna ni el 
    usuario ha decidio crearla nueva.
    """
    from utils.spelling import SpellCorrector
    nombres = " ".join([c.ciudad for c in pclases.Ciudad.select()])
    s = SpellCorrector(nombres)
    nombre_sugerido = s.correct(nombre).title()
    try:
        # Busco. Si está en la BD, pues ya está.
        ciudad = pclases.Ciudad.selectBy(ciudad = nombre_sugerido)[0]
    except IndexError:
        # Si no está, pregunto si crear nuevo.
        if utils.ui.dialogo(titulo = "¿NUEVA CIUDAD?", 
                         texto = "¿Insertar ciudad en la base de datos?", 
                         padre = ventana_padre):
            provincia = buscar_provincia_en_bd(nombre_provincia, 
                                               self.wids['ventana'])
            if provincia:
                ciudad = pclases.Ciudad(provincia = provincia, 
                                        ciudad = ciudad)
            else:
                ciudad = None
        else:
            ciudad = None
    return ciudad


def buscar_provincia_en_bd(nombre, ventana_padre = None):
    """
    Busca la provincia que más se parezca al nombre recibido y devuelve el 
    objeto o crea una nueva provincia. Devuelve None si no se parece ninguna 
    ni el usuario ha decidio crearla nueva.
    """
    from utils.spelling import SpellCorrector
    nombres = " ".join([c.provincia for c in pclases.Provincia.select()])
    s = SpellCorrector(nombres)
    nombre_sugerido = s.correct(nombre).title()
    try:
        # Busco. Si está en la BD, pues ya está.
        provincia = pclases.Provincia.selectBy(provincia = nombre_sugerido)[0]
    except IndexError:
        # Si no está, pregunto si crear nuevo.
        if utils.ui.dialogo(titulo = "¿NUEVA PROVINCIA?", 
                         texto = "¿Insertar provincia en la base de datos?", 
                         padre = ventana_padre):
            provincia = pclases.Provincia(provincia = provincia)
        else:
            provincia = None
    return provincia 


def main():
    from formularios.options_ventana import parse_options
    params, opt_params = parse_options()
    ventana = Direcciones(*params, **opt_params) 

if __name__ == "__main__":
    main()

