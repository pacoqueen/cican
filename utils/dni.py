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

    Algunas utilidades referentes al DNI, NIF, CIF, CCC, etc.
    
'''

from numero import parse_int

# Algoritmos de dígito de control en CCC y letra del DNI:
def cccCRC(cTexto):
    """Cálculo del CRC de un número de 10 dígitos
    ajustados con ceros por la izquierda"""
    factor=(1,2,4,8,5,10,9,7,3,6)
    # Cálculo CRC
    nCRC=0
    for n in range(10):
        nCRC += int(cTexto[n])*factor[n]
    # Reducción del CRC a un dígito
    nValor=11 - nCRC%11
    if nValor==10:
        nValor=1
    elif nValor==11:
        nValor=0
    return nValor

def calcularNIF(dni):
    if isinstance(dni, str):    # Tengo que pasar a número:
        DNI = parse_int(dni)
    else:
        DNI = dni
    if not isinstance(DNI, int):
        raise TypeError, "El parámetro debe ser un entero o una cadena."
    # DNI=12345678 
    NIF='TRWAGMYFPDXBNJZSQVHLCKE' 
    letra = NIF[DNI % 23]
    # print "El NIF del DNI es", letra
    return letra

def parse_cif(cif):
    """
    Devuelve un cif correcto o la cadena vacía si no se puede obtener un 
    CIF/DNI o CIF internacional válido.
    Formatos reconocidos: 
        * NIF 12345678X
        * CIF X12345678
        * Internacional: XYZ12345678
        * Griego: 123456789
        * Internacional 2: XY123456789
        * Especiales organismos oficiales: X1234567Y
    """
    # PLAN: Chequear que si el CIF/NIF es "españolo", que sea correcto. La 
    # letra es fácil de sacar (y hasta podría metérsela en caso de que solo 
    # hubiera 8 números sin letra). La comprobación de NIF de Hacienda no la 
    # conozco, pero debe andar por algún lado, porque el programa de ayuda 
    # del 349 detecta NIF incorrectos.
    # TODO: Ver http://es.wikipedia.org/wiki/Código_de_identificación_fiscal
    import string, re
    cif = str(cif).upper().strip()
    letras = string.letters[string.letters.index("A"):]
    numeros = "0123456789"
    cif = "".join([l for l in cif if l in letras or l in numeros])
    rex = re.compile("([A-Z][0-9]{8})|([0-9]{8}[A-Z])|([A-Z]{3}[0-9]{8})"
                     "|([0-9]{9})|([A-Z]{2}[0-9]{9})|([A-Z][0-9]{7}[A-Z])")
    res = rex.findall(cif)
    try:
        res = [i for i in res[0] if i]
            # La posición donde se encuentre dependerá de con qué parte del 
            # patrón coincida:
            # 0 -> NIF 12345678X
            # 1 -> CIF X12345678
            # 2 -> Internacional: XYZ12345678
            # 3 -> Griego: 123456789
            # 4 -> Internacional 2: XY123456789
        if not res:
            res = ""
        else:
            res = res[0]
    except IndexError:
        res = ""
    # CWT: CIFs pendientes, después pasa lo que pasa.
    if cif == "PENDIENTE":
        return cif 
    return res

def calcCC(cBanco, cSucursal, cCuenta):
    """Cálculo del Código de Control Bancario"""
    cTexto="00%04d%04d" % (int(cBanco),int(cSucursal))
    DC1 = cccCRC(cTexto)
    cTexto="%010d" % long(cCuenta)
    DC2 = cccCRC(cTexto)
    return "%1d%1d" % (DC1,DC2)


