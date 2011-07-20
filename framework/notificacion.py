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
Created on 15/05/2010

@author: bogado

    Notificador de cambios remotos.


 Changelog:
  14 de diciembre de 2005 -> Fork del notificador. Lo saco de 
                             utils.py para hacer una clase 
                             independiente.
  3 de enero de 2005 -> Ahora el notificador también se encarga
                        de controlar el hilo de persistencia del
                        objeto relacionado.

-------------------------- CLASE NOTIFICACIÓN ------------------------------
 La idea es:
 Tener una clase notificación, que sea un wrapper para una función de 
 actualización, que será la que se dispare cuando se produzca una 
 notificación en un objeto persistente.
 Mediante set_ y run_, cuando se produzca una notificación en uno de 
 mis objetos de pclases, se ejecutará (run_) la función que desde el 
 formulario (en la inicialización de la ventana) se ha definido (set_).
 DONE: Estaría bien implementar un singleton para asegurarme que sólo hay un
 notificador activo en la interfaz (que se correspondería con el objeto
 mostrado en ese momento). -> No se puede hacer. Hay ventanas multiobjeto 
 que necesitan un notificador por cada objeto en ventana. Ver por ejemplo 
 «productos_especiales.py»
'''

class Notificacion:
    """
     # PyUML: Do not remove this line! # XMI_ID:_XUfLkO5DEd-QvZvwvxUy6Q
    """
    def __init__(self, obj):
        """
        obj es el objeto al que se asocia el notificador.
        """
        self.__func = lambda : None
        self.observador = obj
        self.__DEBUG = False

    def set_func(self, f):
        self.__func = f
  
    def activar(self, f):
        self.set_func(f)
        if self.__DEBUG:
            print " --- Notificación activada ---"
  
    def desactivar(self):
        self.__func = lambda : None
        if self.__DEBUG:
            print " --- Notificación desactivada ---"
    
    def run(self, *args, **kwargs):
        if self.__DEBUG:
            print "EJECUTO", self.__func
        try:
            self.__func(*args, **kwargs)
        except (AttributeError, KeyError), msg:
            # La ventana se ha cerrado y el objeto sigue en memoria. No tiene 
            # importancia.
            if self.__DEBUG:
                print "notificacion::run -> Ventana cerrada. Ignorando "\
                      "notificación. Mensaje de la excepción: %s" % (msg)

