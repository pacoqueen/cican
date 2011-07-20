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
'''

import os

class Singleton(type):
    """
    Patrón Singleton para evitar que una misma instancia del programa trabaje 
    con varias configuraciones:
    
    # PyUML: Do not remove this line! # XMI_ID:_XVvIwO5DEd-QvZvwvxUy6Q
    """
    def __init__(self, *args):
        type.__init__(self, *args)
        self._instances = {}
    def __call__(self, *args):
        if not args in self._instances:
            self._instances[args] = type.__call__(self, *args)
        return self._instances[args]

class ConfigConexion:
    """
    Clase que recoge los parámetros de configuración
    a partir de un archivo.
    
    # PyUML: Do not remove this line! # XMI_ID:_XVxlAO5DEd-QvZvwvxUy6Q
    """
    __metaclass__ = Singleton

    def __init__(self, fileconf = 'ginn.conf'):
        if fileconf == None:
            fileconf = "ginn.conf"
        if os.sep in fileconf:
            fileconf = os.path.split(fileconf)[-1]
        self.__set_conf(fileconf)

    def __set_conf(self, fileconf):
        """
        Abre el fichero de configuración y parsea la información del mismo.
        """
        self.__fileconf = fileconf
        if not os.path.exists(self.__fileconf):
            self.__fileconf = os.path.join('framework', fileconf)
        if not os.path.exists(self.__fileconf):
            self.__fileconf = os.path.join('..', 'framework', fileconf)
        if not os.path.exists(self.__fileconf):
            # Es posible que estemos en un directorio más interno. Como por 
            # ejemplo, cuando se genera la documentación.
            self.__fileconf = os.path.join('..', '..', 'framework', fileconf)
        if not os.path.exists(self.__fileconf):
            # Último intento... buscar donde siempre [(C)Mi madre.]
            dirpaquete_framework = os.path.dirname(__file__)
            self.__fileconf = os.path.join(dirpaquete_framework, fileconf)
        try:
            self.__fileconf = open(self.__fileconf)
        except IOError:
            self.__fileconf = None
            self.__conf = {}
            diractual = os.path.realpath(os.path.curdir)
            txt = "configuracion::__set_conf -> "\
                  "ERROR: Fichero de configuración '%s' no encontrado.\n"\
                  "\tDirectorio actual: %s" % (fileconf, diractual)
            print txt
        else:
            self.__conf = self.__parse()

    def set_file(self, fileconf):
        """
        Cambia el fichero de configuración y la configuración en sí por el recibido.
        """
        self.__set_conf(fileconf)

    def __parse(self):
        conf = {}
        l = self.__fileconf.readline()
        while l != '':
            l = l.replace('\t', ' ').replace('\n', '').split()
            if l and not l[0].startswith("#"):   
                # Ignoro líneas en blanco y las que comienzan con #
                conf[l[0]] = " ".join([p for p in l[1:] if p.strip() != ""])
            l = self.__fileconf.readline()
        return conf

    def get_tipobd(self):
        return self.__conf['tipobd']
        
    def get_user(self):
        return self.__conf['user']
    
    def get_pass(self):
        return self.__conf['pass']

    def get_dbname(self):
        return self.__conf['dbname']
        
    def get_host(self):
        return self.__conf['host']

    def get_logo(self):
        try:
            logo = self.__conf['logo']
        except KeyError:
            logo = "logo.png"       # Logo genérico
        return logo

    def get_title(self):
        """
        Título de la aplicación que se mostrará en el menú principal.
        """
        try:
            title = self.__conf['title']
        except KeyError:
            title = "CICAN"
        return title
    
    def get_puerto(self):
        """
        Devuelve el puerto de la configuración o el puerto por defecto 5432 
        si no se encuentra.
        """
        try:
            puerto = self.__conf['port']
        except KeyError:
            puerto = '5432'
        return puerto

    def get_dir_adjuntos(self):
        """
        Devuelve el directorio donde se guardarán los adjuntos. Por defecto 
        "adjuntos". La ruta debe ser un único nombre de directorio y se 
        alojará como subdirectorio del "raíz" de la aplicación. Al mismo 
        nivel que "framework", "formularios", etc.
        """
        try:
            ruta = self.__conf['diradjuntos']
        except KeyError:
            ruta = "adjuntos"
        return ruta

    def get_anchoticket(self):
        try:
            ancho = int(self.__conf['anchoticket'])
        except (KeyError, TypeError, ValueError):
            ancho = 48
        return ancho

    def get_largoticket(self):
        """
        Líneas del ticket por detrás de la última línea
        antes de enviar el corte al puerto.
        """
        try:
            largo = int(self.__conf['largoticket'])
        except (KeyError, TypeError, ValueError):
            largo = 0
        return largo

    def get_codepageticket(self):
        """
        Algunas ticketeras no soportan codepages configurables 
        mediante códigos de escape (p. ej. la SAMSUNG SRP 270 C).
        Si este parámetro de configuración es False no intentará
        cambiar el codepage en el TPV.
        """
        try:
            set_c = bool(int(self.__conf['codepageticket']))
        except (KeyError, TypeError, ValueError):
            set_c = True
        return set_c

    def get_cajonserie(self):
        """
        Devuelve True si el cajón portamonedas opera por puerto 
        serie. False si opera a través de la impresora de ticket 
        por el puerto paralelo.
        Si en la configuración no se especifica toma la última
        opción (paralelo) por defecto.
        """
        try:
            cajonserie = bool(int(self.__conf['cajonserie']))
        except (KeyError, TypeError, ValueError):
            cajonserie = False
        return cajonserie

    def get_mostrarcontactoenticket(self):
        """
        Devuelve True si se debe mostrar el nombre de contacto bajo el 
        nombre de la empresa en el ticket.
        False en caso contrario.
        Valor por defecto es True.
        """
        try:
            mostrarcontactoenticket = bool(int(self.__conf['mostrarcontactoenticket']))
        except (KeyError, TypeError, ValueError):
            mostrarcontactoenticket = False
        return mostrarcontactoenticket

    def get_puerto_ticketera(self):
        """
        Devuelve el puerto paralelo por donde opera la impresora de tickets.
        Por defecto /dev/lp0 si el sistema es UNIX y LPT1 en otro caso.
        """
        from os import name as osname
        try:
            puerto = self.__conf['puerto_ticketera']
        except KeyError:
            if osname == "posix":
                puerto = "/dev/lp0"
            else:
                puerto = "LPT1"
        return puerto

    def get_desplegar_tickets(self):
        """
        Devuelve True si se deben desplegar todos los tickets en el TPV.
        False para desplegar únicamente el último.
        Por defecto True.
        """
        try:
            desplegar = bool(int(self.__conf['desplegar_tickets']))
        except (KeyError, TypeError, ValueError):
            desplegar = True
        return desplegar

    def get_oki(self):
        """
        Devuelve True si en la configuración hay una entrada «oki 1».
        Por defecto es False (impresora de tickets es POS estándar y no 
        OKIPOS -derivado de comandos STAR-).
        """
        try:
            okipos = bool(int(self.__conf['oki']))
        except (KeyError, TypeError, ValueError):
            okipos = False
        return okipos

    def get_valorar_albaranes(self):
        """
        Devuelve True si los albaranes deben imprimirse valorados.
        Por defecto es False.
        """
        try:
            valorar = bool(int(self.__conf['valorar_albaranes']))
        except (KeyError, TypeError, ValueError):
            valorar = False
        return valorar

    def get_valorar_albaranes_con_iva(self):
        """
        Devuelve True si los albaranes deben imprimirse valorados con IVA 
        incluido en precio unitario y total del línea.
        Por defecto es True.
        """
        try:
            valorar = bool(int(self.__conf['valorar_albaranes_con_iva']))
        except (KeyError, TypeError, ValueError):
            valorar = True
        return valorar

    def get_carta_portes(self):
        """
        Devuelve True si los albaranes deben imprimirse en forma de 
        carta de portes.
        Por defecto es False.
        CMR y carta_portes son excluyentes (ver albaranes_de_salida.py).
        """
        # FIXME: No sé si al final esto llevará CRM o carta de portes.  
        try:
            carta_portes = bool(int(self.__conf['carta_portes']))
        except (KeyError, TypeError, ValueError):
            carta_portes = False
        return carta_portes

    def get_multipagina(self):
        """
        Devuelve True si los albaranes y facturas deben imprimirse  
        con el formato multipágina (alias "sobrio con tabla contínua").
        Por defecto es False.
        NOTA: Esta opción tiene prioridad sobre la de valorar albaranes.
        """
        try:
            multipagina = bool(int(self.__conf['multipagina']))
        except (KeyError, TypeError, ValueError):
            multipagina = False
        return multipagina

    def get_diastpv(self):
        """
        Número de días a mostrar en la lista de últimas 
        ventas del TVP.
        """
        try:
            dias = int(self.__conf['diastpv'])
        except (KeyError, TypeError, ValueError):
            dias = 3
        return dias

    def get_orden_ventanas(self):
        """
        Orden de las ventanas "Dirección correspondencia" y "Dirección 
        fiscal" en las facturas de venta. Por defecto "cf" (correspondencia 
        a la izquierda, fiscal a la derecha).
        """
        try:
            orden = self.__conf['ventanas_sobre'].strip().lower()
            assert len(orden) == 2 and 'c' in orden and 'f' in orden
        except(KeyError, ValueError, TypeError, AssertionError):
            orden = "cf"
        return orden

    def get_modelo_presupuesto(self):
        """
        Devuelve una cadena con el nombre del módulo que contiene el modelo 
        de presupuesto (el que no es tipo carta).
        Si no se especifica, se usa el por defecto: presupuesto
        Por supuesto, si se implementan modelos nuevos deben cumplir la 
        interfaz -no definida formalmente de momento- con los procedimientos 
        "go", "go_from_presupuesto", etc.
        """
        try:
            modulo = self.__conf["modelo_presupuesto"].strip().lower()
        except (KeyError, ValueError, TypeError):
            modulo = "presupuesto"
        return modulo

def unittest():
    """
    Pruebas unitarias del patrón Singleton.
    """
    class Test:
        __metaclass__=Singleton
        def __init__(self, *args): pass
            
    ta1, ta2 = Test(), Test()
    assert ta1 is ta2
    tb1, tb2 = Test(5), Test(5)
    assert tb1 is tb2
    assert ta1 is not tb1

 
