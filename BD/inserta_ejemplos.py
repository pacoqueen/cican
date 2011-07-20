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
import sys, os
if os.path.realpath(os.path.curdir).split(os.path.sep)[-1] == "BD":
    sys.path.append("..")
from framework import pclases

def main():
    # Y por supuesto los datos de la empresa:
    pclases.DatosDeLaEmpresa(
        nombre = "CICAN",  
        cif = "A41892217", 
        dirfacturacion = "Polígono industrial Nuevo Torneo. Acústica, 24; edificio Puerta de Indias.", 
        cpfacturacion = "41015",  
        ciudadfacturacion = "Sevilla", 
        provinciafacturacion = "Sevilla", 
        direccion = "Polígono industrial Almudayne, N-IV, km 567",  
        cp = "41720",  
        ciudad = "Los Palacios y Villafranca", 
        provincia = "Sevilla", 
        telefono = "955811245",  
        fax = "955812545", 
        email = "jmfigueroa@cican.net",  
        paisfacturacion = "España",  
        pais = "España",  
        telefonofacturacion = "955811245",  
        faxfacturacion = "955812545",  
        nombreResponsableCompras = "",  
        telefonoResponsableCompras = "",  
        nombreContacto = "Juan Miguel Figueroa Yáñez",  
        registroMercantil = "",  
        emailResponsableCompras = "",  
        logo = "logo.png",  
        logo2 = "",  
        bvqi = False, 
        nomalbaran2 = "",  
        diralbaran2 = "", 
        cpalbaran2 = "",  
        ciualbaran2 = "",  
        proalbaran2 = "",  
        telalbaran2 = "",  
        faxalbaran2 = "",  
        regalbaran2 = "",  
        irpf = 0.0, 
        esSociedad = True, 
        logoiso1 = "",  
        logoiso2 = "",  
        recargoEquivalencia = False, 
        iva = 0.18,
        pedCompraTextoFijo = "",  
        pedCompraTextoEditable = "",  
        pedCompraTextoEditableConNivel1 = "",  
        direccionLaboratorio = "Polígono industrial Almuayde, N-IV, km 567", 
        cpLaboratorio = "41720",  
        ciudadLaboratorio = "Los Palacios y Villafranca",  
        provinciaLaboratorio = "Sevilla", 
        telefonoLaboratorio = "955811245")
    # Inserto algunos empleados:
    pclases.Empleado(dni = "00000000-T", 
                     nombre = "Jesús Noel", 
                     apellidos = "Alzugaray")
    pclases.Empleado(dni = "00000001-R", 
                     nombre = "Roberto", 
                     apellidos = "Luzardo")
    # Ahora un par de clientes:
    tyrell = pclases.Cliente(cif = "A21000000", 
                             nombre = "Tyrell Corporation")
    pclases.Cliente(cif = "A21000001", 
                    nombre = "Cyberdyne Systems Corporation")
    # Un par de obras:
    pclases.Obra(nombre = "Obra 0", 
                 cliente = tyrell)
    pclases.Obra(nombre = "Obra 1", 
                 cliente = tyrell)
    # El libro de registro:
    pclases.LibroRegistro(numero = 0)
    # Un centro de tranajo:
    pclases.CentroTrabajo(nombre = "Laboratorio de Los Palacios")
    # Algunos materiales: 
    hormigon = pclases.Material(nombre = "Hormigón")
    zahorra = pclases.Material(nombre = "Zahorra natural")
    ladrillo = pclases.Material(nombre = "Ladrillo de arcilla cocida")
    # Y una estructura simple de capítulos
    capitulo1 = pclases.Capitulo(nombre = "Capítulo I: Movimiento de tierras")
    pclases.Capitulo(nombre = "Capítulo II: Obras de drenaje", 
                     codigo = "")
    subcapitulo = pclases.Capitulo(nombre = "Caracterización del terreno "
                                            "natural subyacente",
                                   codigo = "1",  
                                   nivel = 1, 
                                   capitulo = capitulo1)
    subsubcapitulo = pclases.Capitulo(
                        nombre = "Identificación del terreno natural"
                                 " subyacente", 
                        codigo = "1.1", 
                        nivel = 2, 
                        capitulo = subcapitulo)
    pclases.Capitulo(nombre = "Estabilización de suelos con cal o cemento",
                     codigo = "2",  
                     nivel = 1, 
                     capitulo = capitulo1)    
    # Ensayos:
    pclases.Ensayo(material = hormigon, 
                   nombre = "Ensayo de rotura de probetas", 
                   codigo = 1, 
                   capitulo = subsubcapitulo, 
                   precio = 100)
    pclases.Ensayo(material = hormigon, 
                   nombre = "Consistencia en Cono de Abrams",  
                   codigo = 3003, 
                   capitulo = subsubcapitulo, 
                   precio = 0.50)
    pclases.Ensayo(material = zahorra, 
                   nombre = "Ensayo de zahorra natural", 
                   codigo = 2, 
                   capitulo = subsubcapitulo, 
                   precio = 1)
    pclases.Ensayo(material = ladrillo, 
                   nombre = "Ensayo de ladrillo", 
                   codigo = 3, 
                   capitulo = subsubcapitulo, 
                   precio = 9999.99)
    # Algunas muestras y resultados
    from random import randrange, random, randint
    select_random = lambda clase: clase.select()[randrange(clase.select().count())]
    for i in range(10):
        empleado = select_random(pclases.Empleado)
        obra = select_random(pclases.Obra)
        libroRegistro = select_random(pclases.LibroRegistro)
        centroTrabajo = select_random(pclases.CentroTrabajo)
        material = select_random(pclases.Material)
        codigo = "".join([`randint(0, 9)` for x in xrange(6)])
        muestra = pclases.Muestra(empleado = empleado, 
                                  obra = obra, 
                                  albaranEntrada = None, 
                                  libroRegistro = libroRegistro, 
                                  centroTrabajo = centroTrabajo, 
                                  material = material, 
                                  codigo = codigo)
    for i in range(30):
        muestra = select_random(pclases.Muestra)
        ensayo = select_random(pclases.Ensayo)
        pclases.Resultado(muestra = muestra, 
                          ensayo = ensayo, 
                          valor = round(random() * 100, 2))
    

if __name__ == "__main__":
    main()
