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
Created on 10/09/2010

@author: bogado
'''
import sys, os
if os.path.realpath(os.path.curdir).split(os.path.sep)[-1] == "BD":
    sys.path.append("..")
from framework import pclases

def main():
    admin = pclases.Usuario.get(1)
    # Módulos y ventanas:
    ayuda = pclases.Modulo(nombre = "Ayuda", icono = "doc_y_ayuda.png", 
                           descripcion = "Documentación y ayuda")
    labo = pclases.Modulo(nombre = "Laboratorio", icono = "laboratorio.png", 
                          descripcion = "Laboratorio")
    debug = pclases.Modulo(nombre = "DEBUG", icono = "debug.png", 
                descripcion = "Utilidades de depuración para el administrador")
    general = pclases.Modulo(nombre = "General", icono = "func_generales.png", 
                descripcion = "Datos comunes a todos los módulos")
    almacen = pclases.Modulo(nombre = "Almacén", icono = "almacen.png", 
                descripcion = "Ventanas de gestión del almacén")
    administracion = pclases.Modulo(nombre = "Administración", 
                icono = "administracion.png", 
                descripcion = "Tareas administrativas")
    ventanas = []
    ventanas.append(pclases.Ventana(modulo = ayuda, 
                                    descripcion = "Acerca de...", 
                                    fichero = "acerca_de.py", 
                                    clase = "acerca_de", 
                                    icono = "acerca.png"))
    ventanas.append(pclases.Ventana(modulo = administracion, 
                                    descripcion = "Facturas de venta", 
                                    fichero = "facturas_venta.py", 
                                    clase = "FacturasVenta", 
                                    icono = "factura_venta.png"))
    ventanas.append(pclases.Ventana(modulo = debug, 
                                    descripcion = "Trazabilidad interna", 
                                    fichero = "trazabilidad.py", 
                                    clase = "Trazabilidad", 
                                    icono = "trazabilidad.png"))
    ventanas.append(pclases.Ventana(modulo = debug, 
                                    descripcion = "Visor del log", 
                                    fichero = "logviewer.py", 
                                    clase = "LogViewer", 
                                    icono = "trazabilidad.png"))
    ventanas.append(pclases.Ventana(modulo = general, 
                                    descripcion = "Gestión de usuarios", 
                                    fichero = "usuarios.py", 
                                    clase = "Usuarios", 
                                    icono = "usuarios.png")) 
    ventanas.append(pclases.Ventana(modulo = almacen, 
                                    descripcion = "Albaranes de entrada de muestras", 
                                    fichero = "albaran_entrada.py", 
                                    clase = "VentanaAlbaranesEntrada", 
                                    icono = None)) 
    ventanas.append(pclases.Ventana(modulo = labo, 
                                    descripcion = "Laborantes", 
                                    fichero = "laborantes.py", 
                                    clase = "VentanaLaborantes", 
                                    icono = "users.png")) 
    ventanas.append(pclases.Ventana(modulo = labo, 
                                    descripcion = "Resultados de análisis", 
                                    fichero = "resultados.py", 
                                    clase = "VentanaResultados", 
                                    icono = None)) 
    ventanas.append(pclases.Ventana(modulo = general, 
                                    descripcion = "Series numéricas de facturas", 
                                    fichero = "contadores.py", 
                                    clase = "Contadores", 
                                    icono = None)) 
    ventanas.append(pclases.Ventana(modulo = labo, 
                                    descripcion = "Solicitudes de recogida", 
                                    fichero = "peticiones.py", 
                                    clase = "Peticiones", 
                                    icono = None)) 
    ventanas.append(pclases.Ventana(modulo = general, 
                                    descripcion = "Clientes", 
                                    fichero = "clientes.py", 
                                    clase = "Clientes", 
                                    icono = None)) 
    for v in ventanas:
        pclases.Permiso(ventana = v, usuario = admin, permiso = True, 
                        lectura = True, escritura = True, nuevo = True)

if __name__ == "__main__":
    main()

