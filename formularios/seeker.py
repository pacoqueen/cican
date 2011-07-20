#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
# Copyright (C) 2005-2008 Francisco José Rodríguez Bogado.                    #
#                          (bogado@qinn.es)                                   #
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

"""
They call me The Seeker 
I've been searching low and high 
I won't get to get what I'm after 
'till the day I die.
"""

# Galactus, el devorador de mundos (TM), se convierte esta vez en el devorador 
# de parámetros. Es una función que no hace nada y la voy a usar como 
# valor por defecto para procedimientos que esperan recibir métodos a los que 
# llamar.

import pygtk
pygtk.require('2.0')
import gtk, gtk.glade 
import sys, os, datetime
if os.path.realpath(os.path.curdir).split(os.path.sep)[-1] == "formularios":
    os.chdir("..")
sys.path.append(".")
from framework import pclases
import utils
from formularios.resultado import Resultado
from formularios.ventana_generica import VentanaGenerica

class Seeker:
    """
    Un buscador que indaga en todas las clases de "pclases".
    """
    def __init__(self, termino_busqueda = None, clase = None):
        """
        termino_busqueda es el token a buscar. Si no se recibe, debe 
        instanciarse mediante el método buscar o no podrá usarse el 
        objeto buscador.
        Si se recibe, entonces no es necesario llamar a "buscar" para 
        acceder a los resultados.
        
        @param termino_busqueda: Cadena con los textos a buscar separados por 
                                 espacios.
        @param clase: Si se pasa, solo buscará en esa clase. Puede ser un 
                      nombre de clase o una clase de pclases en sí.
        """
        self.tokenes = None
        self.resultados = []
        if clase and isinstance(clase, pclases.declarative.DeclarativeMeta):
            self.clase = clase.__name__
        elif clase and clase.startswith("pclases."):
            self.clase = clase.split(".")[-1]
        else:
            self.clase = clase
        self._cargar_tokenes(termino_busqueda)
        if self.tokenes:
            self.buscar()
            
    def _cargar_tokenes(self, txt):
        """
        Construye la lista de tokenes a partir del texto. Soporta None para 
        no buscar, cadena vacía para devolver todos los registros y palabras 
        separadas por espacios.
        """
        if txt != None:
            if txt != '':
                self.tokenes = txt.split()
            else:
                self.tokenes = [""]

    def buscar(self, termino_busqueda = None):
        """
        Busca el término de búsqueda "termino_busqueda" y construye la 
        lista de resultados. Si termino_busqueda es None intentará usar 
        el término de búsqueda ya almacenado. Si éste también es None 
        lanza una excepción ValueError.
        """
        if termino_busqueda != None:    # Primero compruebo para no machacar 
                                        # los posibles tokenes ya cargados.
            self._cargar_tokenes(termino_busqueda)
        self._buscar()
        return self.resultados

    def _buscar(self):
        """
        Método protegido que realiza la búsqueda en sí.
        Primero recorre la lista de clases derivadas de SQLObject y PRPCTOO, que 
        son las que representan a los objetos de la base de datos en el ORM. 
        Después, para cada una de esas clases hace una búsqueda OR pasando el 
        término a buscar en un .contains (i.e. ILIKE '%término%' en mi versión 
        "custom" de SQLObject). Finalmente, reúne todos los results en una única
        lista de resultados.
        """
        if not self.clase:
            clases = buscar_clases_pclases()
        else:
            clases = [getattr(pclases, self.clase)]
        tratados = []
        for clase in clases:
            consulta = self.__construir_criterio_consulta(clase)
            if pclases.DEBUG:
                print "seeker::_buscar -> consulta: %s" % consulta
            if consulta != None:
                resultados_select = clase.select(consulta)
                if pclases.DEBUG:
                    print "seeker::_buscar -> ", resultados_select.count()
                for resultado_select in resultados_select:
                    if resultado_select not in tratados:
                        resultado = Resultado(resultado_select)
                        resultado.sync()    # No quiero datos desactualizados.
                        self.resultados.append(resultado)
                        tratados.append(resultado_select)
            elif self.tokenes == ['']: #Caso especial, busco '', devuelvo todo.
                resultados_select = clase.select()
                for resultado_select in resultados_select:
                    if resultado_select not in tratados:
                        resultado = Resultado(resultado_select)
                        resultado.sync()    # No dirty data.
                        self.resultados.append(resultado)
                        tratados.append(resultado_select)
            else:
                # print clase, "Sin campos de texto donde buscar."
                pass

    def __construir_criterio_consulta(self, clase):
        """
        Recibe una clase de pclases y devuelve un objeto 
        que se usará para la consulta en sí. Los criterios 
        se encadenarán con OR y cada uno de ellos será una búsqueda 
        del término de búsqueda en un campo de la clase.
        No chequea que el término de búsqueda esté instanciado.
        """
        criterios = []
        #print self.tokenes
        for token in self.tokenes:
            if pclases.DEBUG:
                print "seeker::__construir_criterio_consulta"\
                      " -> token: %s (%s)" % (token, type(token))
            subcriterios = []
            for nombre_campo in clase.sqlmeta.columns.keys():
                query_attr = getattr(clase, "q")
                campo_query = getattr(query_attr, nombre_campo)
                campo = clase.sqlmeta.columns[nombre_campo]
                if isinstance(campo, pclases.SOStringCol):
                    criterio = campo_query.contains(token)
                elif isinstance(campo, pclases.SOBoolCol): 
                    if isinstance(token, type(True)):
                        criterio = campo_query == token
                    else:
                        continue
                elif isinstance(campo, pclases.SOForeignKey):
                    if isinstance(token, type(1)):
                        # TODO: Esto no es muy útil, debería poder buscar 
                        # por alguno de los campos de los objetos relacionados.
                        criterio = campo_query == token
                    else:
                        continue
                elif isinstance(campo, pclases.SOIntCol): 
                    try:
                        criterio = campo_query == int(token)
                    except ValueError:
                        continue
                elif isinstance(campo, pclases.SOFloatCol): 
                    try:
                        criterio = campo_query == float(token)
                    except ValueError:
                        continue
                elif isinstance(campo, pclases.SODateCol): 
                    try:
                        fecha = utils.fecha.parse_fecha(token)
                    except (ValueError, TypeError):
                        continue
                    else:
                        criterio = campo_query == fecha 
                elif isinstance(campo, pclases.SOCol):
                    # Aquí estarían los DateTime con hora (timestamp)
                    continue
                else:
                    continue
                subcriterios.append(criterio)
            if len(subcriterios) >= 2:
                #subcriterios = pclases.AND(*subcriterios)
                subcriterios = pclases.OR(*subcriterios)
            elif len(subcriterios) == 1:
                subcriterios = subcriterios[0]
            else:
                continue 
            criterios.append(subcriterios)
        if len(criterios) >= 2:
            res = pclases.AND(*criterios)
        elif len(criterios) == 1:
            res = criterios[0]
        else:
            res = None
        return res
                
def buscar_clases_pclases():
    """
    Devuelve una lista de clases del Object Relational Mapper que 
    realmente correspondan a una clase válida en la BD. (Esto es, 
    son derivadas de SQLObject y PRPCTOO).
    """
    res = []
    for clase_str in dir(pclases):
        clase = getattr(pclases, clase_str)
        try:
            if issubclass(clase, pclases.SQLObject) and issubclass(clase, pclases.PRPCTOO): 
                res.append(clase)
        except TypeError: # No es una clase. Debe ser una función, no la trato.
            pass
    return res


if __name__ == "__main__":
    if len(sys.argv) > 1:
        buscador = Seeker()
        buscador.buscar(sys.argv[1])
        if buscador.resultados:
            print len(buscador.resultados), "resultados encontrados. "\
                                            "Muestro el primero de todos."
            for resultado in buscador.resultados: 
                print resultado.puid
            clase_objeto_resultado = getattr(pclases, buscador.resultados[0].clase)
            objeto_resultado = clase_objeto_resultado.get(buscador.resultados[0].id)
            v = VentanaGenerica(objeto = objeto_resultado)
        else:
            print "No se encontró %s" % sys.argv[1]
    else:
        pclases.DEBUG = True
        #VentanaGenerica(pclases.Muestra)
        VentanaGenerica(pclases.Ensayo)
        #VentanaGenerica(pclases.AlbaranEntrada, usuario = pclases.Usuario.get(1))

