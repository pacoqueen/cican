#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
# Copyright (C) 2005-2008  Francisco José Rodríguez Bogado,                   #
#                          Diego Muñoz Escalante.                             #
#                          (bogado@qinn.es, escalant3@users.sourceforge.net)  #
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
## ventana_progreso.py - Clase que implementa una ventana de 
##                       progreso actualizable con prioridad alta.
###################################################################
## NOTAS:
##  
###################################################################
## Changelog:
## 1 de febrero de 2006 -> Inicio
## 1 de febrero de 2006 -> 99% funcional 
## 1 de julio de 2006 -> Incorporada ventana de actividad.
###################################################################

import pygtk
pygtk.require('2.0')
import gtk, gtk.glade, gobject 

class VentanaProgreso:
    """ 
    Muestra una ventana de progreso actualizable con prioridad alta.
    Ejemplo de uso:
    i = 0.0
    tot = len(pascual)
    from ventana_progreso import VentanaProgreso
    vpro = VentanaProgreso()
    vpro.mostrar()
    for tal in pascual:
        # Hacer lo que sea con tal.
        vpro.set_valor(i/tot, 'Procesando %d...' % tal)
        i += 1
    vpro.ocultar()
    """
    def __init__(self, padre = None):
        self.__texto = ''
        self.__valor = 0.0
        self._ventana = gtk.Window()
        self._ventana.set_title('POR FAVOR, ESPERE')
        self._ventana.set_modal(True)
        self._ventana.set_transient_for(padre)
        self._ventana.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
        self.__pbar = gtk.ProgressBar()
        self._ventana.add(self.__pbar)
        self.__pbar.show()
        self._ventana.resize(300, 40)
        self.__visible = False
        self.__seguir_actualizando = True
        self.tiempo = 100
        self.__tag = gobject.timeout_add(self.tiempo, self.actualizar, 
                                         priority = gobject.PRIORITY_HIGH)
        self._ventana.connect('delete_event', lambda w, e: True)

    def __del__(self):
        self._ventana.destroy()
        self.__seguir_actualizando = False
        while gtk.events_pending():
            gtk.main_iteration(False)
        while not gobject.source_remove(self.__tag):
            pass

    def mostrar(self):
        self._ventana.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
        self._ventana.show()
        self.__visible = True

    def ocultar(self):
        self._ventana.hide()
        self.__visible = False

    def set_valor(self, valor, texto = ''):
        """
        Si texto es None se respeta el que ya estuviera establecido.
        """
        if valor > 1.0:
            valor = 1.0
        if texto != None:
            self.__texto = texto
        self.__valor = valor
        while gtk.events_pending():
            gtk.main_iteration(False)

    def get_texto(self):
        """
        Devuelve el texto de la barra de progreso.
        """
        return self.__texto

    def get_valor(self):
        """
        Devuelve el valor actual (porcentaje completado) de 
        la barra de progreso de la ventana.
        """
        return self.__valor

    def actualizar(self):
        if self.__visible:
            self.__pbar.set_text(self.__texto)
            self.__pbar.set_fraction(self.__valor)
        return self.__seguir_actualizando

      
class VentanaActividad:
    """ 
    Muestra una ventana de progreso actualizable con prioridad alta; 
    del tipo Activity (no se sabe exactamente el porcentaje completado
    en cada actualización).
    Ejemplo de uso:
    from ventana_progreso import VentanaActividad
    vpro = VentanaActividad()
    vpro.mostrar()
    for tal in pascual:
        # Hacer lo que sea con tal.
        vpro.mover()
    vpro.ocultar()
    """
    def __init__(self, padre = None, texto = ''):
        self._ventana = gtk.Window()
        self._ventana.set_title('POR FAVOR, ESPERE')
        self._ventana.set_modal(True)
        self._ventana.set_transient_for(padre)
        self._ventana.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
        self.__pbar = gtk.ProgressBar()
        self.__pbar.set_pulse_step(0.01)
        if texto:
            self.__vbox = gtk.VBox()
            self.__vbox.add(gtk.Label(texto))
            self.__vbox.add(self.__pbar)
            self.__vbox.show_all()
            self._ventana.add(self.__vbox)
        else:
            self._ventana.add(self.__pbar)
            self.__pbar.show()
        self._ventana.resize(300, 40)
        self.__visible = False
        self.__seguir_actualizando = True
        self.tiempo = 100
        self.__tag = gobject.timeout_add(self.tiempo, self.actualizar, 
                                         priority = gobject.PRIORITY_HIGH)
        self._ventana.connect('delete_event', lambda w, e: True)

    def __del__(self):
        self._ventana.destroy()
        self.__seguir_actualizando = False
        while gtk.events_pending():
            gtk.main_iteration(False)
        while not gobject.source_remove(self.__tag):
            pass

    def mostrar(self):
        self._ventana.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
        self._ventana.show()
        self.__visible = True

    def ocultar(self):
        self._ventana.hide()
        self.__visible = False

    def actualizar(self):
        return self.__seguir_actualizando

    def mover(self):
        self.__pbar.pulse()
        while gtk.events_pending():
            gtk.main_iteration(False)


if __name__ == '__main__':
    import time
    def ejemplo():
        cosas = ['a', 'b', 'c', 'd', 'e']*50
        i = 0.0
        tot = len(cosas)
        vpro = VentanaProgreso()
        vpro.mostrar()
        for cosa in cosas:
            vpro.set_valor(i/tot, 'Procesando %s...' % cosa)
            time.sleep(0.03)
            i += 1
        vpro.ocultar()
        gtk.main_quit()
        return False
    
    def ejemplo2():
        cosas = ['a', 'b', 'c', 'd', 'e']*50
        vpro = VentanaActividad()
        vpro.mostrar()
        for cosa in cosas: 
            vpro.mover()
            time.sleep(0.03)
        vpro.ocultar()
        gtk.main_quit()
        return False

    def ejemplo3():
        cosas = ['a', 'b', 'c', 'd', 'e']*50
        vpro = VentanaActividad(texto = 'Procesando...')
        vpro.mostrar()
        for cosa in cosas: 
            vpro.mover()
            time.sleep(0.03)
        vpro.ocultar()
        gtk.main_quit()
        return False


    # Esto es sólo para un ejemplo, la clase NO se usa exactamente así.
    gobject.idle_add(ejemplo3)
    gtk.main()
    
