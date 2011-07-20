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

    Utilidades de fecha.

'''

import time, datetime, numero

def convertir_a_fecha(f):
    """
    Intenta convertir f a una fecha.
    Devuelve None si no se puede.
    """
    try:
        res = parse_fecha(f)
    except:
        res = None
    return res

def correct_year(anno_as_int):
    """
    Tiene en cuenta el año actual para determinar si el año con dos cifras 
    se refiere a este siglo o al pasado.
    """
    anno_con_cuatro_digitos = anno_as_int
    anno_actual = datetime.date.today().year
    if anno_con_cuatro_digitos - anno_actual > 50:
        # ¿Tanto se ha ido en el futuro el usuario? Seguro que 
        # se refiere a 19xx, no a 20xx:
        anno_con_cuatro_digitos -= 100
    return anno_con_cuatro_digitos

def parse_year(fecha_as_str):
    """
    Interpreta el año recibido como cadena y devuelve el entero correcto.
    """
    _bingo = fecha_as_str
    anno_con_cuatro_digitos = 2000 + int(_bingo.split("/")[-1])
    anno_con_cuatro_digitos = correct_year(anno_con_cuatro_digitos)
    return anno_con_cuatro_digitos

def parse_fecha(txt):
    """
    Devuelve un datetime con la fecha de
    txt.
    Si no está en formato dd{-/\s}mm{/-\s}yy[yy] lanza una
    excepción.
    Reconoce también textos especiales para interpretar fechas:
    h -> Hoy. Fecha actual del sistema.
    d -> Días. Para sumar o restar días a la fecha que le preceda.
    pdm -> Primero de mes. Día 1 del mes corriente.
    udm -> Último de mes. Último día del mes corriente.

    doctest:

    >>> parse_fecha("01/01/2009").strftime("%d/%m/%y")
    '01/01/09'
    >>> utils.parse_fecha("010109").strftime("%d/%m/%y")
    '01/01/09'
    >>> utils.parse_fecha("01-01-2009").strftime("%d/%m/%y")
    '01/01/09'
    """
    # Navision plagiarism! (¿Quién lo diría?)
    txt = txt.strip().upper()
    if "PDM" in txt:
        tmpdate = datetime.datetime(
            day = 1, 
            month = datetime.date.today().month, 
            year = datetime.date.today().year)
        txt = txt.replace("PDM", tmpdate.strftime("%d/%m/%Y"))
    if "UDM" in txt:
        tmpdate = datetime.datetime(
            day = -1, 
            month = datetime.date.today().month, 
            year = datetime.date.today().year)
        txt = txt.replace("UDM", tmpdate.strftime("%d/%m/%Y"))
    if txt.count("-") == 2:
        txt = txt.replace("-", "/")
    if "+" in txt or "-" in txt:
        # DONE: Aquí hay un pequeño problema. Ya no acepta fechas 22-11-1979.
        txt = txt.replace("D", " * datetime.timedelta(days = 1)")
        txt = txt.replace("H", "datetime.date.today()")
        from re import compile
        rex = compile("[-]?\d+/\d+/\d+")
        for bingo in rex.findall(txt):
            try:
                _bingo = "/".join([`int(i)` for i in bingo.split("/")])
            except (TypeError, ValueError):
                pass
            try:
                if int(_bingo.split("/")[-1]) < 100: # Año con dos dígitos.
                    anno_con_cuatro_digitos = parse_year(_bingo)
                    _bingo="/".join([`int(i)` for i in _bingo.split("/")[:2]] +
                                     [`anno_con_cuatro_digitos`])
            except:
                pass
            datebingo = "datetime.date(day=%s,month=%s,year=%s)" % (
                _bingo.split("/")[0], 
                _bingo.split("/")[1], 
                _bingo.split("/")[2])
            txt = txt.replace(bingo, datebingo)
        try:
            tmpdate = eval(txt)
        except:
            raise ValueError, "%s no se pudo interpretar como fecha." % txt
        txt = tmpdate.strftime("%d/%m/%Y")
    if "H" in txt:
        txt = txt.replace("H", datetime.date.today().strftime("%d/%m/%Y"))
    try:
        dia, mes, anno = map(int, txt.split('/'))
    except ValueError:
        try:
            dia, mes, anno = map(int, txt.split('-'))
        except ValueError:
            if len(txt) >= 4:
                dia = int(txt[:2])
                mes = int(txt[2:4])
                if len(txt) >= 6: 
                    anno = int(txt[4:])
                else:
                    anno = datetime.date.today().year
            else:
                raise ValueError, "%s no se pudo interpretar como fecha." % txt
    if anno < 1000:
        anno += 2000    
        # Han metido 31/12/06 y quiero que quede 31/12/2006 y no 31/12/0006
    anno = correct_year(anno)
    return datetime.date(day = dia, month = mes, year = anno) 

def comparar_como_fechas(n, m):
    """
    Compara n y m como fechas.
    """
    n = convertir_a_fecha(n)
    m = convertir_a_fecha(m)
    if n < m:
        return -1
    elif n > m:
        return 1
    else:
        return 0

def comparar_como_fechahora(n, m):
    """
    Compara n y m como fechas con hora (DateTime completo).
    """
    n = convertir_a_fechahora(n)
    m = convertir_a_fechahora(m)
    if n < m:
        return -1
    elif n > m:
        return 1
    else:
        return 0

def convertir_a_fechahora(f):
    """
    Intenta convertir f a una fechahora.
    Devuelve None si no se puede.
    """
    try:
        res = parse_fechahora(f)
    except:
        res = None
    return res

def parse_fechahora(txt):
    """
    Devuelve un datetime con la fecha y hora de
    txt.
    Si no está en formato dd{-/}mm{-/}yy[yy] HH:MM[:SS] lanza una
    excepción.
    """
    try:
        import datetime
        if isinstance(txt, datetime.datetime):
            txt = txt.strftime("%d/%m/%Y %H:%M:%S")
    except ImportError:
        pass
    import re
    fechamysqlstyle = re.compile("\d+-\d+-\d+ \d{2}:\d{2}")
    if fechamysqlstyle.findall(txt):
        dia, mes, anno = txt.split(" ")[0].split("-")[:3]
        hora = txt.split(" ")[-1]
        if len(dia) > len(anno):    # Viene con el año al principio. 4 dígitos
            anno, dia = dia, anno   # mayor que 2.
        # Cambio el separador a la barra, que me lo reconoce el parse_fecha
        txt = dia + "/" + mes + "/" + anno + " " + hora
    if "-" in txt and " " not in txt:
        sep = "-"
    else:
        sep = " "
    fecha, hora = "".join(txt.split(sep)[:-1]), txt.split(sep)[-1]
    fecha = parse_fecha(fecha)
    hora = parse_hora(hora)
    res = fecha + hora      # Curioso... la suma de DateTime y DateTimeDelta 
    return res              # no tiene la propiedad conmutativa.

def parse_hora(txt):
    """
    Devuelve un datetime.timedelta a partir del 
    texto recibido.
    """
    if ":" not in txt:
        if len(txt) <= 2:
            txt = txt + "00"
        txt = txt[:-2] + ":" + txt[-2:]
    valores = txt.split(":")
    if len(valores) == 3:
        hora, minuto, segundo = map(numero._float, valores)
    else:
        segundo = 0
        hora, minuto = map(numero._float, valores)
    return datetime.timedelta(hours = hora, minutes = minuto, seconds = segundo)

def abs_fecha(fecha):
    """
    Devuelve la fecha "absoluta" (esto es, sin horas, minutos, segundos, etc.; 
    o, más bien, con la hora puesta a 0) partiendo de la fecha recibida.
    Útil para comparar dos fechas, una (o las dos) de ellas contiene además la hora 
    y sólo interesa saber si comparten fecha (día concreto, vamos).
    """
    return datetime.datetime(day = fecha.day, month = fecha.month, year = fecha.year) # hour, minutes... por defecto son 0

def cmp_abs_fecha(f1, f2):
    """
    Función de comparación para ordenación de fechas ignorando hora del día.
    """
    if abs_fecha(f1) < abs_fecha(f2):
        return -1
    elif abs_fecha(f1) > abs_fecha(f2):
        return 1
    else:
        return 0

def str_fechahoralarga(datetime):
    """
    Devuelve el datetime recibido como una cadena que 
    muestra la fecha y la hora.
    """
    return "%s %s" % (str_fecha(datetime), str_hora(datetime))

def str_fechahora(datetime):
    """
    Devuelve el datetime recibido como una cadena que 
    muestra la fecha y la hora.
    """
    return "%s %s" % (str_fecha(datetime), str_hora_corta(datetime))

def str_fecha(fecha = time.localtime()):
    """
    Devuelve como una cadena de texto en el formato dd/mm/aaaa
    la fecha pasada. 
    "fecha" debe ser de tipo time.struct_time, o
    bien una tupla [dd, mm, aaaa] como
    las que devuelve "mostrar_calendario".
    Si no se pasa ningún parámetro devuelve la fecha 
    del sistema.
    Si se pasa None, devuelve la cadena vacía ''.
    Si la fecha no es de ningún tipo de los permitidos
    saltará una excepción que debe ser atendida en 
    capas superiores de la pila de llamadas.
    """
    if fecha == None:    # Si es None (valor por defecto en envios)
        return ''
    if isinstance(fecha, tuple):    # Es una fecha de mostrar_calendario y ya viene ordenada
        t = fecha
    else:
        if isinstance(fecha, time.struct_time):
            tuplafecha = fecha
        elif isinstance(fecha, datetime.date):
            tuplafecha = fecha.timetuple()
        else:    # No es ni time ni None ni tupla ni nada de nada
            return None 
        t = list(tuplafecha)[2::-1]
    # Aquí ya tengo una lista [m, d, aa] o [mm, dd, aaaa]
    t = map(str, ['%02d' % i for i in t])    # "Miaque" soy rebuscado a veces. Con lo fácil que tiene que ser esto.
    t = '/'.join(t)
    return t

def str_hora(fh):
    """
    Devuelve la parte de la hora de una fecha
    completa (fecha + hora, DateTime).
    """
    try:
        return "%02d:%02d:%02d" % (fh.hour, fh.minute, fh.second)
    except:
        return ''

def str_hora_corta(fh):
    """
    Devuelve la parte de la hora de una fecha
    completa (fecha + hora, DateTime).
    """
    try:
        return "%02d:%02d" % (fh.hour, fh.minute)
    except:
        return ''

