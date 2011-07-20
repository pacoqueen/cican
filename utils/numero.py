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

    Algunas funciones genéricas para trabajar con números

'''

from fixedpoint import FixedPoint as Ffloat

def parse_int(str, invertir = False):
    """
    Devuelve el primero de los números que se pueda extraer 
    de la cadena str o None si no contiene ninguna cifra.
    Si invertir == True, devuelve el primer número encontrado por el final.
    """
    import re
    regexp = re.compile("[0-9]*")
    try:
        ultimo = [int(item) for item in regexp.findall(str) if item!='']
        if not invertir:
            ultimo = ultimo[0]
        else:
            ultimo = ultimo[-1]
    except (IndexError, ValueError, TypeError):
        ultimo = None
    return ultimo

def parse_float(n):
    """
    "Parsea" un flotante ignorando todo lo que no sean números, «,» y «.».
    """
    if isinstance(n, str):
        n = "".join([l for l in n if l in "0123456789.,"])
        return _float(n)
    return float(n)

def _float(x): #, precision = 2):
    #if isinstance(x, float):
    #    x = float2str(x, precision)
    if isinstance(x, str) and (',' in x):
        x = x.replace(".", "")
        x = x.replace(",", ".")
    #res = ffloat(x, precision)
    res = float(x)
    return res

def float2str(n, precision = 2, autodec = False, separador_decimales = ","):
    """
    Devuelve una cadena con el flotante convertido a entero en 
    formato xxx.xxx.xxx[,{y}]. La "precisión" (número de decimales
    mostrados) por defecto es 2.
    Si autodec es True, autodecrementa el número de decimales para no
    mostrar ceros a la derecha en la parte fraccionaria.
    """
    if precision == 0:
        res = str(int(round(n, 0)))
    elif precision > 0:
        try:
            from decimal import Decimal
            if isinstance(n, Decimal):
                n = float(n)
        except ImportError:
            pass
        es_de_tipo_numerico = isinstance(n, (float, Ffloat, int, long))
        if es_de_tipo_numerico:
            if n < 0:   # Es negativo
                negativo = True
                n = -n  # Lo hago positivo y después le añadiré el signo -.
            else:
                negativo = False
            # Cutrealgoritmo Bankers Rounding. Lo hago después de comprobar si 
            # es negativo para un redondeo simétrico:
            # Algo un poco más profesional pero que no logro hacer que 
            # funcione como quiero: http://fixedpoint.sourceforge.net
            n = round_banquero(n, precision)
            s = "%%.%df" % precision
            s = s % (n)
            s = s.replace('.', ',')
            i = s.rindex(',')
            i -= 3
            while i > 0:
                s = s[:i] + "." + s[i:]
                i -= 3
            if negativo:
                s = "-"+s
            res = s
        elif isinstance(n, str):
            if "," in n:      # Seguramente venga en formato "123.234,234" así que:
                n = n.replace('.', '')
                n = n.replace(',', '.')
            res = float2str(float(n), precision)
        else:
            try:
                res = float2str(float(n), precision)
            except Exception:
                raise ValueError, "El valor %s no se pudo convertir a cadena." % n
    if autodec:
        while "," in res and len(res) - res.index(",") > 2 and res[-1] == '0':
            res = res[:-1]
        if res[-1] == '0' and res[-2] == ",":
            res = res[:-2]
    res = res.replace(",", separador_decimales)
    return res

def float2str_autoprecision(n, c, t, p = 2):
    """
    Devuelve un flotante como cadena con la precisión suficiente como para que 
    al multiplicarse con «c» dé «t».
    «p» es la precisión mínima deseada.
    (Similar al método usado por la clase LineaDeVenta en 
    «calcular_precio_unitario_coherente», solo que no es dependiente de ningún 
    atributo de LDV.
    """
    totlinea = t
    cantidad = c
    precision = p
    for i in range(precision, 6):
        precio = float2str(n, i)
        # Emulo lo que saldrá en pantalla, para ver si cuadra:
        strsubtotal1 = float2str(totlinea, precision)
        subtotal2 = _float(precio) * cantidad
        strsubtotal2 = float2str(subtotal2, precision)
        if strsubtotal1 == strsubtotal2:
            break
    # Reduzco los ceros por la derecha hasta llegar a la precisión mínima
    # requerida en «p».
    def numdecimales(p):
        "NOTA: El separador de decimales debe ser la coma."
        try:
            numdec = len(p) - p.index(",") - 1
        except ValueError:
            numdec = 0  # No hay separador decimal.
        return numdec
    while precio.endswith("0") and "," in precio and numdecimales(precio) > p:
        precio = precio[:-1]
    if precio.endswith(","):
        precio = precio[:-1]
    return precio

def int2str(n):
    """
    Devuelve el número entero recibido como 
    cadena con formato de punto de separación 
    cada 3 dígitos.
    P.ej: int2str(1234) = "1.234"
          int2str(0) = "0"
          etc...
    """
    # ¿Quién dijo que Python no podía ser tan críptico como Perl? 
    # Todo es ponerse ;)
    puntuar_entero = lambda s: ".".join([(i>=3 and [s[i-3:i]] or [s[:abs(0-i)]])[0] for i in range(len(s), 0, -3)][::-1])
    if isinstance(n, float):
        return puntuar_entero(str(int(round(n))))
    elif isinstance(n, str): 
        return puntuar_entero(str(int(round(float(n)))))
    elif isinstance(n, int):
        return puntuar_entero(str(n))
    else:
        return puntuar_entero(str(int(round(n))))
    
def check_num(num):
    """
    Detecta si un número que viene como cadena respeta el formato 1234.56
    Si puede, lo formatea correctamente antes de devolverlo. En otro caso
    devuelve la misma cadena recibida.
    OBSOLETO.
    """
    if isinstance(num, str):
        if ('.' in num and ',' in num) or num.count('.') > 1:
            num = num.replace('.', '')
        if ',' in num:
            num = num.replace(',', '.')
    return num

def round_banquero(numero, precision = 2):
    """
    Redondea a "precisión" decimales. Por defecto a 2.
    Por ejemplo: 
        0.076 -> 0.08
        0.071 -> 0.07
    """
    return int(numero*(10.0**(precision)) + 0.5)/(10.0**(precision))

def convertir_a_numero(n):
    """
    Convierte n a flotante.
    Devuelve None si no se puede.
    """
    res = None
    try:
        res = _float(n)
    except:
        if isinstance(n, str) and "€" in n:
            try:
                res = parse_euro(n)
            except:
                res = None
        elif isinstance(n, str) and "%" in n:
            try:
                res = parse_porcentaje(n)
            except:
                res = None
    return res

def parse_euro(strfloat):
    """
    Recibe una cantidad monetaria como cadena. Puede incluir el un espacio,
    el signo menos (-) y el euro (€).
    La función procesa la cadena y devuelve un flotante que se 
    corresponde con el valor o lanza una excepción ValueError si 
    no se puede parsear.
    """
    if not isinstance(strfloat, str):   # Por si las moscas
        strfloat = str(strfloat)
    res = strfloat.replace('€', '')
    res = res.strip()
    try:
        res = _float(res)
    except ValueError, msg:
        res = None
        #utils.dialogo('El número no se puede interpretar.')
        raise ValueError, "%s: El número %s no se puede interpretar como"\
                          " moneda." % (msg, strfloat)
    return res

def el_reparador_magico_de_representacion_de_flotantes_de_doraemon(filas):
    ## HACK:
    # El render usa el método __repr__ para escribir los floats en la celda.
    # Esto tiene un problema: 100.35.__repr__() devuelve 100.3499999... debido
    # a la representación interna del punto flotante <i>iecubo-sietecincocuatro</i>
    # etcétera, etcétera.
    # Al hacerle un print, operar y todas esas cosas se comporta perfectamente,
    # pero al pasar por el render, se pinta 100.349999... Eso yo lo puedo 
    # entender; pero dile a mi cliente que es por el estándar de representación
    # binaria de los flotantes, a ver dónde te manda.
    # TOTAL: Que los voy a pasar a string antes de mostrarlos, que así sí se 
    # ven correctamente: (Otra cosa curiosa que tengo que mirar a fondo
    # porque no me cuadra. ¿Por qué `0.3`!=str(0.3)? ¿Tiene algo que ver con
    # el Frente Popular de Judea y el Frente Judaico Popular?
    # ...
    # Ok, una explicación convincente de las dos formas de comportarse está
    # aquí: file:///usr/share/doc/python2.3/html/tut/node15.html
    for f in xrange(len(filas)):
        fila = list(filas[f])
        filas[f] = fila
        # OJO porque filas debe ser una lista, si no, no aceptará la asignación.
        for c in xrange(len(fila)):
            item = fila[c]
            if isinstance(item, float):
                fila[c] = str(round(item, 2))
            if item == None:    # Voy a aprovechar el invento para quitarme  
                                # los None de encima, que tampoco acaban de 
                                # sentarle bien al TreeView.
                fila[c] = ''

def parse_porcentaje(strfloat, fraccion = False):
    """
    Recibe un porcentaje como cadena. Puede incluir el un espacio,
    el signo menos (-) y el porciento (%).
    La función procesa la cadena y devuelve un flotante que se 
    corresponde con el valor del porcentaje como fracción de 1, es decir, 
    en la forma 10 % = 0.1, si «fracción» es True.
    En otro caso devuelve el valor numérico sin más una vez filtrado el 
    símbolo "%".
    """
    res = strfloat.replace('%', '')
    res = res.replace(',', '.')
    res = res.strip()
    try:
        res = _float(res)
    except ValueError, msg:
        res = 0.0
        #utils.dialogo('El número no se puede interpretar.')
        raise ValueError, "%s: El número %s no se puede interpretar como porcentaje." % (msg, strfloat)
    if fraccion:
        res /= 100.0
    return res

def parse_formula(_cad, tipo = float):
    """
    Intenta convertir la cadena recibida en un valor numérico del tipo 
    especificado (por defecto, flotante).
    Si no contiene operadores aritméticos o no puede acabar convirtiéndolo 
    todo a un número, devuelve el valor tal y cual le llega.
    """
    EOS = chr(0)    # Necesito un fin de cadena para saber cuándo he 
                    # terminado en el parser.
    cad = _cad + EOS
    operadores = ('=', 'X', 'x', '*', '+', '-', '/', '^', '(', ')')
    intentarlo = False
    for o in operadores:
        if o in cad:
            intentarlo = True
            break
    if not intentarlo:
        res = _cad
    else:
        cad = cad.replace("=", "").replace("x", "*").replace("X", "*")
        tokens = []
        token = ""
        for letra in cad:
            if letra.isdigit():             # Si es número, apilo.
                token += letra
            elif letra not in operadores and letra != EOS:   
                    # Si punto, coma, etc... apilo. 
                token += letra
            else:                           # Operador, trato y siguiente.
                try:
                    token = float2str(_float(token), separador_decimales = ".")
                except (ValueError, TypeError):
                    res = _cad
                    break   # NaN. Me salgo y devuelvo la cadena original. 
                tokens.append(token)
                if letra in operadores:
                    tokens.append(letra)    # Apilo también el operador
                token = ""
        # He acabado de separar valores y formatear los números correctamente.
        # Toca intentar resolver la fórmula:
        expresion = "".join(tokens)
        try:
            res = eval(expresion)
        except: # Petó. Qué mala fuerte, shato.
            res = _cad
        else:
            try:
                res = tipo(res)
            except (TypeError, ValueError):
                res = _cad
    return res

