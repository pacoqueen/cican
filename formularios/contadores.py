#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
# Copyright (C) 2005-2008  Francisco José Rodríguez Bogado,                   #
#                          Diego Muñoz Escalante.                             #
# (pacoqueen@users.sourceforge.net, escalant3@users.sourceforge.net)          #
#                                                                             #
# This file is part of GeotexInn.                                             #
#                                                                             #
# GeotexInn is free software; you can redistribute it and/or modify           #
# it under the terms of the GNU General Public License as published by        #
# the Free Software Foundation; either version 2 of the License, or           #
# (at your option) any later version.                                         #
#                                                                             #
# GeotexInn is distributed in the hope that it will be useful,                #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU General Public License for more details.                                #
#                                                                             #
# You should have received a copy of the GNU General Public License           #
# along with GeotexInn; if not, write to the Free Software                    #
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA  #
###############################################################################

###################################################################
## contadores.py -- Contadores de facturas.
###################################################################
## NOTAS:
##  
## ----------------------------------------------------------------
##  
###################################################################
## Changelog:
## 
###################################################################

import gtk
from seeker import VentanaGenerica
from framework import pclases
from ventana import Ventana
import utils

class Contadores(Ventana):
    def __init__(self, objeto = None, usuario = None):
        """
        Constructor. objeto puede ser un objeto de pclases con el que
        comenzar la ventana (en lugar del primero de la tabla, que es
        el que se muestra por defecto).
        """
        self.usuario = usuario
        Ventana.__init__(self, 'contadores.glade', objeto)
        connections = {'b_salir/clicked': self.salir,
                       'b_agregar/clicked': self.crear_nuevo_contador,
                       'b_borrar/clicked': self.eliminar_contador,
                       'b_modificar/clicked': self.modificar_contador, 
                       'b_actualizar_contador/clicked': self.cambiar_contador}
        self.add_connections(connections)
        cols = (('Prefijo', 'gobject.TYPE_STRING', False, True, False, None),
                ('Valor actual', 'gobject.TYPE_STRING', 
                    True, True, False, self.cambiar_valor_contador),
                ('Sufijo', 'gobject.TYPE_STRING', 
                    False, True, False, None),
                ('Siguiente factura', 'gobject.TYPE_STRING', 
                    False, True, False, None),
                ('Última creada', 'gobject.TYPE_STRING', 
                    False, True, False, None),
                ('Fecha última factura', 'gobject.TYPE_STRING', 
                    False, True, False, None), 
                ('Facturas de la serie', 'gobject.TYPE_INT64', 
                    False, True, False, None),
                ('Tipos de factura asignados', 'gobject.TYPE_INT64', 
                    False, True, False, None), 
                ('Idcontador', 'gobject.TYPE_INT64', 
                    False, False, False, None))
        utils.ui.preparar_listview(self.wids['tv_tipos'], cols)
        self.rellenar_widgets()
        gtk.main()

    def actualizar_ventana(self):
        self.rellenar_widgets()

    def activar_widgets(self, activar):
        pass

    def rellenar_widgets(self):
        self.wids['b_modificar'].set_sensitive(self.usuario == None 
                                               or self.usuario.nivel <= 1)
        self.rellenar_tabla()

    def cambiar_valor_contador(self, cell, path, texto):
        """
        Cambia el número del contador seleccionado.
        """
        if self.usuario != None and self.usuario.nivel > 1:
            # Sólo faltaba que cualquiera pudiera andar tocando los contadores
            utils.ui.dialogo_info(titulo = "SIN PRIVILEGIOS", 
                               texto = "No tiene permisos suficientes para "
                                       "editar los contadores.", 
                               padre = self.wids['ventana'])
        else:
            model = self.wids['tv_tipos'].get_model()
            try:
                idcont = model[path][-1]
            except IndexError, e:
                self.logger.error("contadores.py::cambiar_valor_contador ->"
                                  " %s.\npath: %s" % (e, path))
            else:
                try:
                    num = int(texto)
                except ValueError:
                    utils.ui.dialogo_info(titulo = "ERROR EN FORMATO NUMÉRICO",
                                       texto = "El texto introducido %s no es"
                                               " un número válido." % (texto), 
                                       padre = self.wids['ventana'])
                else:
                    contador = pclases.SerieNumerica.get(idcont)
                    contador.contador = num
                    self.rellenar_widgets()

    def chequear_cambios(self):
        pass

    def cambiar_contador(self, boton):
        """
        Cambia un contador por otro en todos los tipos de facturas que lo 
        tuvieran.
        """
        model, iter = self.wids['tv_tipos'].get_selection().get_selected()
        if iter != None:
            idcontador = model[iter][-1]
            viejo_contador = pclases.SerieNumerica.get(idcontador)
            contadores = [(c.id, c.get_info()) 
                          for c in pclases.SerieNumerica.select() 
                          if c != viejo_contador]
            idcontador = utils.ui.dialogo_combo(titulo = "SELECCIONE CONTADOR",
                            texto = "Seleccione el contador que sustituirá "
                                    "al actual en los tipos de factura.", 
                            ops = contadores, 
                            padre = self.wids['ventana'])
            if idcontador != None:
                nuevo_contador = pclases.SerieNumerica.get(idcontador)
                tiposFactura = viejo_contador.tiposFactura[:]
                for tipo in tiposFactura:
                    tipo.contador = nuevo_contador
        else:
            utils.ui.dialogo_info('ERROR','Seleccione contador a modificar', 
                                  padre = self.wids['ventana'])

    def rellenar_tabla(self):
        """
        Rellena el model con los contadores existentes
        """        
        contadores = pclases.SerieNumerica.select(orderBy="prefijo")
        model = self.wids['tv_tipos'].get_model()
        model.clear()
        for c in contadores:
            len_tipos_fra = len(c.tiposFactura)
            facturas = c.facturasVenta
            facturas.sort(key = lambda f: f.numfactura, reverse = True)
            fecha_ultima_factura = (facturas 
                and utils.fecha.str_fecha(facturas[0].fecha) or "-")
            model.append((c.prefijo,
                          c.contador, 
                          c.sufijo,
                          c.get_next_numfactura(commit = False), 
                          c.get_last_numfactura_creada() or "-", 
                          fecha_ultima_factura, 
                          len(facturas), 
                          len_tipos_fra, 
                          c.id))
    
    def eliminar_contador(self,widget):
        model, iter = self.wids['tv_tipos'].get_selection().get_selected()
        if iter != None:
            idtipo = model[iter][-1]
            contador = pclases.SerieNumerica.get(idtipo)
        else:        
            utils.ui.dialogo_info('ERROR','Seleccione contador a eliminar')
            return
        try:    
            contador.destroySelf()
        except:
            utils.ui.dialogo_info('ERROR',
                'No se ha podido eliminar el contador. Probablemente existan'
                ' clientes con este contador.', 
                padre = self.wids['ventana'])
        self.rellenar_tabla()
    
    def modificar_contador(self, widget):
        model, iter = self.wids['tv_tipos'].get_selection().get_selected()
        if iter != None:
            idtipo = model[iter][-1]
            contador = pclases.SerieNumerica.get(idtipo)
        else:
            utils.ui.dialogo_info('ERROR','Seleccione contador a modificar')
            return
        prefijo = utils.ui.dialogo_entrada('Introduzca el nuevo prefijo.')
        if prefijo != None:
            sufijo = utils.ui.dialogo_entrada('Introduzca el nuevo sufijo.')
            try:    
                if prefijo != None and sufijo != None:
                    contador.prefijo = prefijo
                    contador.sufijo = sufijo
            except:
                utils.ui.dialogo_info('ERROR',
                                      'No se ha podido modificar el contador.',
                                      padre = self.wids['ventana'])
            self.rellenar_tabla()
    
    def crear_nuevo_contador(self, widget):
        """
        Función callback del botón b_nuevo.
        Pide los datos básicos para crear un nuevo objeto.
        Una vez insertado en la BD hay que hacerlo activo
        en la ventana para que puedan ser editados el resto
        de campos que no se hayan pedido aquí.
        """
        prefijo = utils.ui.dialogo_entrada(
            'Introduzca el prefijo del nuevo contador', 
            padre = self.wids['ventana'])
        if prefijo != None:
            sufijo = utils.ui.dialogo_entrada(
                'Introduzca el sufijo del nuevo contador', 
                padre = self.wids['ventana'])
            if sufijo != None:
                contador = pclases.SerieNumerica(prefijo = prefijo, 
                                                 sufijo = sufijo, contador = 1)
                self.rellenar_tabla()
    
    
if __name__ == '__main__':
    try:
        t = Contadores(usuario = pclases.Usuario.get(5))
    except:
        t = Contadores()
 
