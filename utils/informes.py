#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
# Copyright (C) 2005-2008 Francisco José Rodríguez Bogado,                    #
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


# Usando ReportLab como herramienta para la generación de informes
# en GeotexINN.



############## DONE-LIST #############################
# 27 - XI - 2005
# A parte de hacer todos los informes que quedan. Hay varios
# puntos que tenemos que comentar y arreglar:
# + DONE: Codificación de caracteres para correcta visualización de
# + DONE: Nombre de cliente salta una excepción por excesiva recursividad
# - ¿DONE?: Tratamiento de informes de varias página, sólo aproximación
#           momentánea
# + Dejar más espacio para cantidad en facturas y quitar de precio unitario.
# 19 - VII - 2005
# + DONE: Crear los PDF en el temporal del usuario (ver import tempfile)
# + Hacer las facturas de abono con el mismo diseño que las facturas normales.
# + Buscar función para poner título a los PDF que genero (todos tienen
#   "untitled", que es el valor por defecto de ReportLab).
########################################################

import subprocess, os

def abrir_pdf(fpdf):
    """
    Abre con el visor predeterminado del sistema operativo el fichero 
    recibido.
    """
    if os.name == "posix":
        retcode = subprocess.call(("xdg-open", fpdf))
    elif os.name == "nt":
        try:
            retcode = os.startfile(fpdf)  # En windows no debería fallar.
        except:
            retcode = subprocess.call(("start", fpdf))
    elif os.name == "mac":
        retcode = subprocess.call(("open", fpdf))
    return retcode
        

import sys, Image, re, time, datetime 
import reportlab
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import inch, cm
from tempfile import gettempdir

if os.path.realpath(os.path.curdir).split(os.path.sep)[-1] == "utils":
    sys.path.append("..")
root, dirs, files = os.walk(".").next()
if "framework" in dirs:
    sys.path.insert(0, ".")
from framework.pclases import get_dde, DEBUG, VERBOSE
import utils 

# Medidas fundamentales
# Ancho y alto
MAXLINEAS = 47 
MAXLINAB = 28
# Márgenes (Considero el margen superior lo que está por debajo del
# encabezamiento.)
tm, bm, lm, rm = (680, 56.69, 28.35, 566.92)
width, height = A4
linea = 0

def apaisar(apaisar = True):
    global width, height, rm, tm, MAXLINEAS  # ¿Por qué globales? ¡¿POR QUÉ?!
                                             # Repito: ¡¡¡¡¡¡ POR QUÉ !!!!!!!
    if apaisar:
        width, height = landscape(A4)
        rm = width - 0.5 * cm
        tm = height - 5.8 * cm      # Por probar con algo de margen
        MAXLINEAS = 30              # Por poner algo, pero que sepas que esto
                                    # NO ES CORRECTO. El número de líneas no
                                    # es fijo.
    else:
        width, height = A4
        rm = 566.92
        tm = 680
        MAXLINEAS = 47 # Por poner algo, pero que sepas que esto
                       # NO ES CORRECTO. El número de líneas no es fijo.
    return rm, tm, width, height, MAXLINEAS

def cursiva(c,              # Canvas
            x,              # Posición X
            y,              # Posición y,
            text,           # Texto a escribir
            fontName,       # Fuente
            fontSize,       # Tamaño
            fillColor,      # Color
            skewAngle,      # Ángulo de inclinación
           ):
    from reportlab.graphics.shapes import skewX

    skewMatrix = skewX(skewAngle)
    c.saveState()
    c.setFillColor(fillColor)
    c.setFont(fontName, fontSize)
    for t in text:
        c.saveState()
        c.translate(x, y)
        c.transform(*skewMatrix)
        c.drawString(0, 0, t)
        c.restoreState()
        x += c.stringWidth(t, fontName, fontSize)
    c.restoreState()

def give_me_the_name_baby(prefix = "", suffix = ""):
    #import time
    #return '_'.join(map(str, time.localtime()[:6]))
    res = "{0}{1}{2}".format(prefix, time.strftime("%Y%m%d%H%M%S"), suffix)
    return res

def escribe(cadena_original):
    """
    Dada una cadena la convierte a un formato en el que
    ReportLab es capaz de escribir tildes.
    """
    if isinstance(cadena_original, datetime.date):
        cadena = utils.fecha.str_fecha(cadena_original)
    elif isinstance(cadena_original, datetime.datetime):
        cadena = utils.fecha.str_fechahora(cadena_original)
    else:
        cadena = str(cadena_original)
    if (reportlab.__version__
        != ' $Id: informes.py,v 1.475 2010/11/09 12:39:18 pacoqueen Exp $ '
        and '2877 2006-05-18 15:11:23Z andy ' not in reportlab.__version__):
        # Compruebo la versión porque la de la máquina de desarrollo SÍ
        # soporta UTF y falla con cp1252.
        try:
            cadena = cadena.encode('cp1252')
        except Exception, msg:
            if DEBUG and VERBOSE:
                print 'informes.py (escribe): No se pudo cambiar'\
                      ' codificación de cadena "%s". Mensaje de la excepción'\
                      ': %s' % (cadena, msg)
            try:
                cadena = cadena.decode("utf-8", "ignore").encode("cp1252")
            except Exception, msg:
                if DEBUG and VERBOSE:
                    print 'informes.py (escribe): No se pudo decodificar de '\
                          'UTF-8 la cadena "%s". Mensaje de la excepción: '\
                          '%s' % (cadena, msg)
                try:
                    cadena = cambiar_tildes(cadena)
                except Exception, msg:
                    if DEBUG:
                        print 'informes.py (escribe): No se pudieron '\
                              'sustituir los acentos gráficos de "%s". '\
                              'Mensaje de la excepción: %s' % (cadena, msg)
                    cadena = ''
    try:
        canvas_tmp = canvas.Canvas(os.path.join(gettempdir(), "tmp.pdf"))
        ancho = canvas_tmp.stringWidth(cadena, "Helvetica", 10)
    except UnicodeDecodeError:
        cadena = cadena_original
    return cadena

def cambiar_tildes(cadena):
    """
    Cambia las tildes de la cadena con caracteres sin tilde.
    """
    res = cadena
    dic = {'á': 'a',
           'Á': 'A',
           'é': 'e',
           'É': 'E',
           'í': 'i',
           'Í': 'I',
           'ó': 'o',
           'Ó': 'O',
           'ú': 'u',
           'Ú': 'U'}
    for con_tilde in dic:
        res = res.replace(con_tilde, dic[con_tilde])
    return res

def cambiar_caracteres_problematicos(cadena):
    cadena = cambiar_tildes(cadena)
    for mala, buena in (("ñ", "nn"), ("Ñ", "NN"), 
                        ("ü", "u"), ("Ü", "U"), 
                        ("ç", "c"), ("Ç", "C"), 
                        ("(", ""), (")", "")):
        cadena = cadena.replace(mala, buena)
    return cadena

def sigLinea(valor = 15, actual = None):
    global linea
    if actual == None:
        actual = linea
    return actual - valor

def primLinea():
    return tm - 15

def cabecera(c, texto, fecha = None, apaisado = False):
    """
    Dibuja la cabecera del informe
    """
    datos_empresa = get_dde()

    global lm, rm, bm, tm, width, height
    if apaisado:
        rm, tm, width, height, MAXLINEAS = apaisar()
    else:
        rm, tm, width, height, MAXLINEAS = apaisar(False)

    xIzquierda = lm -4
    rectangulo(c, (xIzquierda, tm+2*inch), (rm, bm-0.2*inch))
    try:
        flogo = os.path.join('imagenes', datos_empresa.logo)
    except IOError:
        flogo = os.path.join('..', 'imagenes', datos_empresa.logo)
    c.drawImage(flogo, lm+0.1*inch, height - 1*inch, 0.7*inch, 0.7*inch)
    c.setFont("Helvetica", 20)

    el_encogedor_de_fuentes_de_doraemon(c, "Helvetica", 20, lm+inch, rm,
                                        height-0.75*inch, texto, alineacion=0)
    #c.drawString(lm+inch, height-0.75*inch, escribe(texto))
    c.line(xIzquierda, height-inch, rm, height-inch)
    c.setFont("Helvetica", 10)
    if fecha != None:
        xFecha = rm - 5
        yFecha = tm + 1.8*inch
        c.drawRightString(xFecha, yFecha, escribe(fecha))

def pie(c, actualPagina, totalPagina, apaisado = False):
    """
    Pone el número de página y una línea en el pie
    """
    global width, height, rm, tm, linea

    if apaisado:
        rm, tm, width, height, MAXLINEAS = apaisar()
    else:
        rm, tm, width, height, MAXLINEAS = apaisar(False)

    x = width / 2
    linea = bm - 0.6*inch
    #c.line(lm, linea, rm, linea)
    c.setFont('Times-Italic', 12)
    # TODO: Esto hay que corregirlo tarde o temprano. De momento corrijo las
    # últimas páginas al vuelo para que no quede "Página 7 de 4". Al menos que
    # ponga "7 de 7" aunque al final sean 8.
    if actualPagina > totalPagina:
        totalPagina = actualPagina
    label = "Página %d de %d" % (actualPagina, totalPagina)
    c.drawCentredString(x, linea, escribe(label))

def rectangulo(hoja,
               esquina1,
               esquina2,
               texto = '',
               alinTxtX = None,
               alinTxtY = None,
               doble = False,
               color_relleno = None):
    """
    Dada la tupla esquina superior izquierda y la
    tupla inferior derecha traza un rectángulo
    Si se pasa un texto como parámetro lo escribe en la
    esquina superior izquierda por dentro
    """
    if doble:
        hoja.saveState()
        hoja.setLineWidth(0.5)
        hoja.line(esquina1[0], esquina1[1], esquina1[0], esquina2[1])
        hoja.line(esquina1[0], esquina2[1], esquina2[0], esquina2[1])
        hoja.line(esquina2[0], esquina2[1], esquina2[0], esquina1[1])
        hoja.line(esquina2[0], esquina1[1], esquina1[0], esquina1[1])

        hoja.line(esquina1[0]+2, esquina1[1]-2, esquina1[0]+2, esquina2[1]+2)
        hoja.line(esquina1[0]+2, esquina2[1]+2, esquina2[0]-2, esquina2[1]+2)
        hoja.line(esquina2[0]-2, esquina2[1]+2, esquina2[0]-2, esquina1[1]-2)
        hoja.line(esquina2[0]-2, esquina1[1]-2, esquina1[0]+2, esquina1[1]-2)
        hoja.restoreState()
    else:
        hoja.line(esquina1[0], esquina1[1], esquina1[0], esquina2[1])
        hoja.line(esquina1[0], esquina2[1], esquina2[0], esquina2[1])
        hoja.line(esquina2[0], esquina2[1], esquina2[0], esquina1[1])
        hoja.line(esquina2[0], esquina1[1], esquina1[0], esquina1[1])

    if color_relleno:
        hoja.saveState()
        hoja.setFillColorRGB(*color_relleno)
        hoja.rect(esquina1[0], esquina1[1],
                  esquina2[0] - esquina1[0], esquina2[1] - esquina1[1],
                  fill = 1)
        hoja.restoreState()

    if alinTxtY == None:
        lin = esquina2[1]+4
    elif alinTxtY == 'arriba':
        lin = esquina1[1] - 11
    elif alinTxtY == 'centro':
        lin = ((esquina1[1] + esquina2[1]) / 2) - 5

    fuente = hoja._fontname
    tamannoini = hoja._fontsize
    if texto: # != "":
        if alinTxtX == None or alinTxtX == 'izquierda':
            # el_encogedor_de_fuentes_de_doraemon(hoja, fuente, tamannoini,
            # esquina1[0]+5, esquina2[0]-2, lin, escribe(texto), alineacion=-1)
            el_encogedor_de_fuentes_de_doraemon(hoja, fuente, tamannoini,
                esquina1[0]+5, esquina2[0]-2, lin, texto, alineacion = -1)
            # hoja.drawString(esquina1[0]+5, lin, escribe(texto))
        elif alinTxtX == 'centro':
            #el_encogedor_de_fuentes_de_doraemon(hoja, fuente, tamannoini,
            # esquina1[0]+5, esquina2[0]-2, lin, escribe(texto), alineacion=0)
            el_encogedor_de_fuentes_de_doraemon(hoja, fuente, tamannoini,
                esquina1[0]+5, esquina2[0]-2, lin, texto, alineacion = 0)
            #hoja.drawCentredString((esquina1[0]+esquina2[0])/2, lin,
            #   escribe(texto))
        elif alinTxtX == 'derecha':
            #el_encogedor_de_fuentes_de_doraemon(hoja, fuente, tamannoini,
            # esquina1[0]+5, esquina2[0]-2, lin, escribe(texto), alineacion 1)
            el_encogedor_de_fuentes_de_doraemon(hoja, fuente, tamannoini,
                esquina1[0]+5, esquina2[0]-2, lin, texto, alineacion = 1)
            #hoja.drawRightString(esquina2[0]-2, lin, escribe(texto))

def el_encogedor_de_fuentes_de_doraemon(canvas, fuente, tamannoini, xini,
                                        xfin, y, texto, alineacion = -1):
    """
    Comenzando por el tamaño inicial "tamannoini", encoge el texto
    hasta que quepa en los límites fijados y después lo escribe.
    Convierte el texto por si está en una codificación no soportada.
    Al finalizar, devuelve las propiedades de texto del canvas a
    su estado original y la fuente a su tamaño inicial.
    NO AVANZA LÍNEA.
    Si alineacion == -1: Alineación a la izquierda. Si 0, centrado y si 1, a
    la derecha.
    """
    # PLAN: No estaría mal pasar un tamaño mínimo de fuente, y si se alcanza o
    # se supera, cortar la línea con agregarFila y el último tamaño de fuente
    # válido. Claro que entonces habría que devolver también las líneas
    # avanzadas, etc...
    canvas.saveState()
    size = tamannoini
    texto = escribe(texto)
    while canvas.stringWidth(texto, fuente, size) > (xfin - xini) and size > 4:
        size -= 1
    canvas.setFont(fuente, size)
    if alineacion == -1:
        canvas.drawString(xini, y, texto)
    elif alineacion == 1:
        canvas.drawRightString(xfin, y, texto)
    elif alineacion == 0:
        canvas.drawCentredString((xfin + xini) / 2.0, y, texto)
    else:
        print "informes.py::el_encogedor_de_fuentes_de_doraemon -> Error "\
              "alineación. Uso alineación a la izquierda por defecto."
        canvas.drawString(xini, y, texto)
    canvas.restoreState()

def trazabilidad(texto):
    """
    Simplemente vuelca el texto recibido en un PDF.
    """
    una_linea = -12
    tm, bm, lm, rm = (680, 56.69, 28.35, 566.92)
    nomarchivo = os.path.join(gettempdir(),
        "trazabilidad_%s.pdf" % (give_me_the_name_baby()))
    c = canvas.Canvas(nomarchivo)
    c.setPageSize(A4)
    fuente, tamanno = "Helvetica", 10
    c.setFont(fuente, tamanno)
    lineas = texto.split("\n")
    while lineas:
        cabecera(c, 'Informe de trazabilidad',
                 utils.str_fecha(mx.DateTime.localtime()))
        # Marca "borrador"
        c.saveState()
        c.setFont("Courier-BoldOblique", 42)
        ancho = c.stringWidth("BORRADOR", "Courier-BoldOblique", 42)
        c.translate(A4[0] / 2.0, A4[1] / 2.0)
        c.rotate(45)
        c.setLineWidth(3)
        c.setStrokeColorRGB(1.0, 0.7, 0.7)
        c.setFillColorRGB(1.0, 0.7, 0.7)
        c.rect((-ancho - 10) / 2.0, -5, (ancho + 10), 37, fill = False)
        c.drawCentredString(0, 0, "BORRADOR")
        c.rotate(-45)
        c.restoreState()
        # EOMarca "borrador"
        x, y = lm, tm + 2.5 * cm
        while y >= bm and lineas:
            linea = lineas.pop(0)
            saltos = agregarFila(x, y, rm, escribe(linea), c, fuente, tamanno,
                                 a_derecha = False, altura_linea = -una_linea)
            y += una_linea * saltos
        c.showPage()
    c.save()
    return nomarchivo

def texto_libre(texto, txtcabecera = "", incluir_fecha_del_dia = True):
    """
    Simplemente vuelca el texto recibido en un PDF.
    """
    una_linea = -12
    tm, bm, lm, rm = (680, 56.69, 28.35, 566.92)
    nomarchivo = os.path.join(gettempdir(),
        "trazabilidad_%s.pdf" % (give_me_the_name_baby()))
    c = canvas.Canvas(nomarchivo)
    c.setPageSize(A4)
    fuente, tamanno = "Courier", 10
    c.setFont(fuente, tamanno)
    lineas = texto.split("\n")
    while lineas:
        cabecera(c, txtcabecera, incluir_fecha_del_dia
                 and utils.str_fecha(mx.DateTime.localtime()) or "")
        x, y = lm, tm + 2.5 * cm
        while y >= bm and lineas:
            linea = lineas.pop(0)
            if len(linea) > 0:
                sangria = 0
                i = 0
                car = linea[i]
                while car == ' ' and i < len(linea):
                    sangria += 0.2*cm
                    i += 1
                    car = linea[i]
                x = lm + sangria
            saltos = agregarFila(x, y, rm, escribe(linea), c, fuente, tamanno,
                                 a_derecha = False, altura_linea = -una_linea)
            y += una_linea * saltos
        c.showPage()
    c.save()
    return nomarchivo

def agregarFila(origen,
                linea,
                limite,
                cadena,
                hoja,
                fuente,
                tamano,
                a_derecha = False,
                altura_linea = 10,
                centrado = False, 
                simular = False, 
                subrayador_fosforito = None):
    """
    Intenta escribir el texto en el espacio comprendido entre
    origen y limite. Si no tiene espacio suficiente la corta
    en las líneas que sean necesarias y devuelve el número
    de líneas que ha avanzado.

    Si a_derecha == True, dibuja el texto alineado a la derecha.
    altura_linea es la altura de la línea (en positivo).

    Si «simular» es True no escribe nada, simplemente devuelve las líneas 
    que se sumarían en caso de hacerlo.

    Si «subrayador_fosforito» es una tupla de tres números entre 0 y 1, 
    subraya las líneas escritas en el color RGB de la tupla.
    """
    #print "fuente", fuente
    #print "tamaño", tamano
    # XXX: Refactorizar. Menudo spaghetti code.
    cadena = cadena.replace("\n", ". ").strip()
    # Había un caso extremo (espacio al final de la cadena) que acababa en
    # bucle infinito.
    try:
        cadena = unicode(cadena)
        # OJO: IMPORTANTE: Verificar que esto (que funciona bien para el
        # ReportLab de la máquina de desarrollo "nostromo") va igual de bien
        # en "melchor", "alfred" y en producción.
    except UnicodeDecodeError:
        pass
        # Efectivamente, con la versión en producción de ReportLab casca.
        # No convierto.
    longitud = hoja.stringWidth(cadena, fuente, tamano)
    longitudLimite = limite - origen
    lineasSumadas = 1
    hoja.saveState()
    hoja.setFont(fuente, tamano)
    # ------------------------------------------------------------------- 
    def make_subrayado(color_rgb, hoja, x, y, cadena, alto):
        #global fuente, tamano
        if color_rgb and cadena:
            ancho = hoja.stringWidth(cadena, fuente, tamano)
            hoja.saveState()
            hoja.setFillColorRGB(*(color_rgb))
            hoja.setStrokeColorRGB(*(color_rgb))
            hoja.rect(x, 
                      y - 4, 
                      ancho, 
                      alto, 
                      stroke = 0, fill = 1)
            hoja.restoreState()
    # ------------------------------------------------------------------- 
    if longitud < longitudLimite:
        if a_derecha:
            try:
                if not simular:
                    make_subrayado(subrayador_fosforito, hoja, 
                                   limite - 0.1*cm, linea, 
                                   cadena, altura_linea)
                    hoja.drawRightString(limite - 0.1 * cm, linea, cadena)
            except KeyError:
                # Alguna tilde dando por culo y el texto no se ha filtrado
                # por "escribe". Lo intento yo aquí.
                if not simular:
                    make_subrayado(subrayador_fosforito, hoja, 
                                   limite - 0.1*cm, linea, 
                                   escribe(cadena), altura_linea)
                    hoja.drawRightString(limite - 0.1 * cm, linea, 
                                         escribe(cadena))
        elif centrado:
            izquierda = limite - 0.1 * cm
            derecha = origen
            centro_x = (derecha + izquierda) / 2.0
            try:
                if not simular:
                    make_subrayado(subrayador_fosforito, hoja, 
                                   centro_x - limite/2.0, 
                                   linea, cadena, altura_linea)
                    hoja.drawCentredString(centro_x, linea, cadena)
            except KeyError:
                # Alguna tilde dando por culo y el texto no se ha filtrado
                # por "escribe". Lo intento yo aquí.
                if not simular:
                    make_subrayado(subrayador_fosforito, hoja, 
                                   centro_x - limite/2.0, 
                                   linea, escribe(cadena), altura_linea)
                    hoja.drawCentredString(centro_x, linea, escribe(cadena))
        else:
            try:
                if not simular:
                    make_subrayado(subrayador_fosforito, hoja, origen, linea, 
                                   cadena, altura_linea)
                    hoja.drawString(origen, linea, cadena)
            except KeyError:
                if not simular:
                    make_subrayado(subrayador_fosforito, hoja, origen, linea, 
                                   escribe(cadena), altura_linea)
                    hoja.drawString(origen, linea, escribe(cadena))
    else:
        cadena1 = cadena
        cadena2 = cadena
        # OJO: Si una palabra es más larga que longitudLimite, no se corta y
        # lo sobrepasará (mejor eso que el bucle infinito en el caía antes).
        while (hoja.stringWidth(cadena2, fuente, tamano) > longitudLimite
               and " " in cadena2):
            #print "cadena1", cadena1, "cadena2", cadena2, "tamano", tamano
            i = 1
            cadena = cadena1 = cadena2
            while (i <= len(cadena)
                   and (hoja.stringWidth(cadena1, fuente, tamano)
                        > longitudLimite or cadena1[-1] != " ")):
                #print "i", i, "cad", cadena, "cad1", cadena1, "cad2", cadena2
                cadena1 = cadena[:-i]
                cadena2 = cadena[-i:]
                i += 1
            if len(cadena1) <= 1:   # He repetido el bucle y no he conseguido
                                    # que entre en el hueco cortando por
                                    # espacios. Reduzco la fuente:
                #print "TATE"
                tamano -= 1
                cadena1 = cadena2 = cadena
                continue
            if a_derecha:
                try:
                    if not simular:
                        make_subrayado(subrayador_fosforito, hoja, 
                                       limite - 0.1*cm, linea, 
                                       cadena1, altura_linea)
                        hoja.drawRightString(limite - 0.1 * cm, linea, cadena1)
                except KeyError:
                    if not simular:
                        make_subrayado(subrayador_fosforito, hoja, 
                                       limite - 0.1*cm, linea, 
                                       escribe(cadena1), altura_linea)
                        hoja.drawRightString(limite - 0.1 * cm, linea,
                                         escribe(cadena1))
            elif centrado:
                izquierda = limite - 0.1 * cm
                derecha = origen
                centro_x = (derecha + izquierda) / 2
                try:
                    if not simular:
                        make_subrayado(subrayador_fosforito, hoja, 
                                       centro_x - limite/2.0, 
                                       cadena, limite, altura_linea)
                        hoja.drawCentredString(centro_x, linea, cadena)
                except KeyError:
                    # Alguna tilde dando por culo y el texto no se ha filtrado
                    # por "escribe". Lo intento yo aquí.
                    if not simular:
                        make_subrayado(subrayador_fosforito, hoja, 
                                       centro_x - limite/2.0, 
                                       escribe(cadena), limite, altura_linea)
                        hoja.drawCentredString(centro_x,linea,escribe(cadena))
            else:
                try:
                    if not simular:
                        make_subrayado(subrayador_fosforito, hoja, origen, 
                                       linea, cadena1, altura_linea)
                        hoja.drawString(origen, linea, cadena1)
                except KeyError:
                    if not simular:
                        make_subrayado(subrayador_fosforito, hoja, origen, 
                                       linea, escribe(cadena1), altura_linea)
                        hoja.drawString(origen, linea, escribe(cadena1))
            linea -= altura_linea
            lineasSumadas += 1
            cadena1 = cadena2
        cadena = cadena2
        if a_derecha:
            try:
                if not simular:
                    make_subrayado(subrayador_fosforito, hoja, 
                                   limite - 0.1*cm, linea, 
                                   cadena, altura_linea)
                    hoja.drawRightString(limite - 0.1 * cm, linea, cadena)
            except KeyError:
                if not simular:
                    make_subrayado(subrayador_fosforito, hoja, 
                                   limite - 0.1*cm, linea, 
                                   cadena, altura_linea)
                    hoja.drawRightString(limite - 0.1 * cm, linea, cadena)
        elif centrado:
            izquierda = limite - 0.1 * cm
            derecha = origen
            centro_x = (derecha + izquierda) / 2
            try:
                if not simular:
                    make_subrayado(subrayador_fosforito, hoja, 
                                   centro_x - limite/2.0, 
                                   linea, cadena, altura_linea)
                    hoja.drawCentredString(centro_x, linea, cadena)
            except KeyError:
                # Alguna tilde dando por culo y el texto no se ha filtrado
                # por "escribe". Lo intento yo aquí.
                if not simular:
                    make_subrayado(subrayador_fosforito, hoja, 
                                   centro_x - limite/2.0, 
                                   linea, escribe(cadena), altura_linea)
                    hoja.drawCentredString(centro_x, linea, escribe(cadena))
        else:
            try:
                if not simular:
                    make_subrayado(subrayador_fosforito, hoja, origen, linea, 
                                   cadena, altura_linea)
                    hoja.drawString(origen, linea, cadena)
            except KeyError:
                if not simular:
                    make_subrayado(subrayador_fosforito, hoja, origen, linea, 
                                   cadena, altura_linea)
                    hoja.drawString(origen, linea, cadena)
    hoja.restoreState()
    return lineasSumadas

def exportar_a_csv(ruta, cabecera, datos):
    import treeview2csv
    ruta_form = os.path.join("..", "formularios")
    if ruta_form not in sys.path:
        sys.path.append(ruta_form)
    from informes import abrir_csv
    datos_iso = []
    for fila in datos:
        fila_iso = []
        for item in fila:
            if isinstance(item, bool):
                item = item and u"Sí".encode("iso-8859-15") or "No"
            else:
                item = ("%s" % item).replace(";", ",")
                try:
                    item.encode("iso-8859-15")
                    item = item.replace("€", chr(164))
                        # Lo hago a manopla porque no sé por que el encoding
                        # no se cepilla el euro y lo cambia por el chr(164).
                except Exception, msg:
                    print msg
            fila_iso.append(item)
        datos_iso.append(fila_iso)
    cabecera_iso = []
    for item in cabecera:
        try:
            item = item[0].encode("iso-8859-15")
        except:
            pass
        cabecera_iso.append(item)
    treeview2csv.generar_csv(ruta, cabecera_iso, datos_iso)
    abrir_csv(ruta)

def parse_fuente(cad, hoja):
    """
    Si la cadena contiene algo de la forma [fuente=%s] intenta reconocer  
    la fuente y devuelve la misma cadena sin la subcadena 
    reconocida.
    La subcadena debe ser de la forma "nombre fuente::tamaño"
    Fuentes reconocidas (al menos):
    ['Courier',
     'Courier-Bold',
     'Courier-BoldOblique',
     'Courier-Oblique',
     'Helvetica',
     'Helvetica-Bold',
     'Helvetica-BoldOblique',
     'Helvetica-Oblique',
     'Symbol',
     'Times-Bold',
     'Times-BoldItalic',
     'Times-Italic',
     'Times-Roman',
     'ZapfDingbats']
    Devuelve None donde no pueda reconocer fuente o tamaño.
    """
    try:
        fuente_tamanno=re.compile("\[fuente=\w+\-?\w*::\d+\]").findall(cad)[0]
    except IndexError:
        fuente = tamanno = None
    else:
        cad = cad.replace(fuente_tamanno, "")
        fuente_tamanno = fuente_tamanno[1:-1]   # Quito corchetes.
        fuente_tamanno = fuente_tamanno.replace("fuente=", "")
        fuente, tamanno = fuente_tamanno.split("::")
        tamanno = int(tamanno)  # Lanzará ValueError si no es un entero.
        if fuente not in hoja.getAvailableFonts():
            raise ValueError, "geninformes::parse_fuente: La fuente debe es"\
                              "tar en %s." % hoja.getAvailableFonts()
    #print cad, fuente, tamanno, type(tamanno)
    return cad, fuente, tamanno

def generar_pdf(archivo,
                titulo,
                campos,
                datos,
                fecha = None,
                cols_a_derecha = (),
                graficos = [],
                apaisado = False,
                sobrecampos = (),
                lineas_verticales = (),
                exportar_a_csv_a = None,
                cols_centradas = (), 
                pijama = False):
    """
    Veamos, veamos. La idea es tener este método y pasarle chorrecientos
    parámetros de modo que luego el método se encargue de ordenar las cosas.
    Hay varios problemas inciales:
    - Cada informe imprime unos datos que no tienen porqué tener nada que ver
      con el formulario o el objeto en pantalla. Incluso pueden imprimirse
      desde el menú principal, es decir, sin ningún objeto en memoria.
    - Cada informe imprime unos campos, cada campo tiene un tamaño máximo y
      han de ajustarse de modo que quepan todos al mismo tiempo que la cosa
      quede elegante.

    Parámetros a pasar:
    - Nombre del archivo de salida *.pdf
    - Título (cabecera) del informe
    - Lista de campos (los títulos) y el ancho máximo de cada uno de modo que
      una funcioncilla calcule el ancho de cada uno en el papel. Hay que tener
      en cuenta que la longitud horizontal de impresión es de rm-lm pixeles.
      Esto no es tan fácil además que las fuentes no son Monospace, ummm.
      Bueno, hay otra salida: Considerar los porcentajes que debe ocupar cada
      campo y así dividirlo y ubicarlo sobre la marcha. Así que finalmente el
      parámetro campos es una lista de tuplas de la forma ('Campo',
      porcentaje). El porcentaje es lo que ocupa ese campo. Lo primero será
      comprobar que la suma de los porcentajes no es mayor que 100.
    - Lista de datos: Es sencillo. Una lista con todas las filas del informe.
      Cada fila es una tupla cuya longitud (y orden) debe ser igual al número
      de campos.

    cols_a_derecha es una lista de los índices de las columnas
    (empezando por 0) que deben ser alineadas a la derecha.

    graficos es una lista de NOMBRES DE ARCHIVO que contienen imágenes que
    serán colocadas una tras otra al final del informe.

    Seguimos complicando el tema. "sobrecampos" es una lista de
    (('palabra1', x1%), ('palabra2', x2%), ...) que se colocarán en la
    cabecera de los campos, un poco más arriba de los títulos, centradas en
    las posiciones "x" indicadas (tanto porciento respecto al ancho de la
    página).

    ¡No se vayan todavía, aún hay más! Si algún campo contiene la cadena de
    texto "---" se dibujará una línea en el ancho de ese campo. Si es "==="
    dibujará una línea doble.

    Seguimos aumentando la lista interminable de parámetros:
    "lineas_verticales" es una lista de posiciones (siempre en tantos por
    ciento) donde se dibujarán líneas verticales que irán desde el borde
    superior de la cabecera hasta el borde inferior del cuadro del cuerpo si
    el segundo elemento de cada sublista es False o desde el borde superior de
    la cabecera hasta el borde inferior de la página si es True:
    P.ej: ((20, False), (50, True)) produce:
    -----------------
    |        |      |
    -----------------
    |   |    |      |
    |   |    |      |
    -----------------

    Ahora acepta colores en el texto. Hay que pasarlos en cualquier posición
    del texto a colorear de la siguiente forma:
        (ejemplo) "Uno de los valores[color=rojo]"  -> Escribirá "Uno de los
        valores" en rojo.
        De momento acepta:
            [color=rojo]
            [color=azul]
            [color=verde]
            [color=gris]

    "Mais" cositas: Si un campo contiene la cadena ">->", se extenderá el
    límite del campo anterior al límite de ese campo de forma que el texto
    del campo anterior ocupará el espacio de su campo y el del que contiene
    ">->".

    Otro parámetro one more time: exportar_a_csv_a. Si es None no hace nada.
    Si es una cadena de texto volcará una versión en formato CSV del informe
    generado (es decir, cabecera + datos, básicamente). El archivo resultante
    se abre directamente con el programa relacionado, NO SE DEVUELVE, SE RECIBE
    EL NOMBRE DEL FICHERO DESTINO.

    «pijama» es un parámetro de última hornada que sirve para irte a la cama a 
    soñar con la teniente Ellen Ripley. También vale para que las líneas se 
    dibujen con color de fondo alternativo al estilo de los viejos rollos de 
    papel contínuo en verde-blanco.
    """
    if exportar_a_csv_a:
        exportar_a_csv(exportar_a_csv_a, campos, datos)
    from reportlab.lib import colors

    if len(datos) == 0:
        return

    global linea, tm, lm, rm, tm, MAXLINEAS, bm

    if archivo.lower().endswith(".pdf"):
        archivo = archivo[:-4]
    if apaisado:
        rm, tm, width, height, MAXLINEAS = apaisar()
        hoja = canvas.Canvas("%s.pdf" % (archivo), pagesize = landscape(A4))
    else:
        rm, tm, width, height, MAXLINEAS = apaisar(False)
        hoja = canvas.Canvas(archivo + ".pdf", pagesize = A4)

    hoja.setTitle(titulo)

    x, y = lm, tm + inch

    texto = hoja.beginText()
    # Ponemos la cabecera
    cabecera(hoja, titulo, fecha, apaisado = apaisado)
    linea = tm + 0.8*inch
    # El cuerpo
    fuente = "Helvetica-Bold"
    tamanno = 9
    hoja.setFont(fuente, tamanno)
    suma = sum([i[1] for i in campos])
    if suma > 100:
        #print 'ERROR: Los campos ocupan más de lo que permite la hoja'
        #return
        # En lugar de abortar, recorto campos hasta llegar al 100.
        campos = [list(c) for c in campos]
        c = len(campos)
        while sum([i[1] for i in campos]) > 100:
            c -= 1
            campos[c][1] -= 1
            if c <= 0:
                # Vuelvo a empezar
                c = len(campos)
    if len(datos[0]) != len(campos):
        print 'ERROR: Los datos no concuerdan con los campos del informe'
        return
    # xcampo guarda la coordenada x donde irá cada campo
    xcampo = [lm]
    anchoHoja = rm - lm
    for i in campos:
        xcampo.append( (i[1]*anchoHoja/100) + xcampo[len(xcampo)-1] )
    xcampo = xcampo[:-1]
    yCabecera = tm + inch
    for sobrecampo, posicion in sobrecampos:
        posicion_sobrecampo = (lm - 4) + (1.0 * posicion * anchoHoja / 100)
        hoja.drawCentredString(posicion_sobrecampo, yCabecera + 0.3 * cm,
                               escribe(sobrecampo))
    hoja.saveState()
    for linea_vertical, hasta_arriba in lineas_verticales:
        # El porqué de toda esta incoherencia entre anchos, márgenes y ajustes
        # manuales chapuceros es que la ignorancia es muy atrevida.
        # Hay que hacerle una limpieza de código total a esto. Me metí a
        # toquetear sin conocer bien el ReportLab y... en fin.
        ancho = anchoHoja
        arriba = height - inch
        abajo = bm - 0.2 * inch
        medio = yCabecera - 2
        # Para que no pise a las columnas alineadas a la dcha.:
        posicion_linea_vertical = ((lm - 4)
                                    + (1.0 * linea_vertical * ancho / 100) + 2)
        if hasta_arriba:
            hoja.setLineWidth(0.4)
            hoja.setDash()
            hoja.line(posicion_linea_vertical, arriba,
                      posicion_linea_vertical, medio)
        hoja.setLineWidth(0.2)
        hoja.setDash(1, 4)  # 1 punto negro, 4 blancos
        hoja.line(posicion_linea_vertical, medio, posicion_linea_vertical,
                  abajo)
    hoja.restoreState()
    for i in range(len(campos)):
        try:
            #hoja.drawCentredString((xcampo[i]+xcampo[i+1])/2, yCabecera,
            #                       escribe(campos[i][0]))
            el_encogedor_de_fuentes_de_doraemon(hoja, fuente, tamanno,
                xcampo[i], xcampo[i+1], yCabecera, campos[i][0], alineacion=0)
        except IndexError:
            #hoja.drawCentredString((xcampo[i]+rm)/2, yCabecera,
            #                       escribe(campos[i][0]))
            el_encogedor_de_fuentes_de_doraemon(hoja, fuente, tamanno,
                xcampo[i], rm, yCabecera, campos[i][0], alineacion = 0)
    hoja.line(lm - 4, yCabecera-2, rm, yCabecera-2)
    linea = yCabecera
    fuente = old_fuente = "Helvetica"
    tamanno = old_tamanno = 6
    hoja.setFont(fuente, tamanno)
    # 41 es el número máximo de líneas en el área de impresión
    paginas = int(len(datos) / MAXLINEAS) +1
    x = lm
    y = linea
    # contLinea se va incrementando con cada elemento y llegado al tope de
    # líneas provoca la creación de una nueva página.
    contLinea = 0
    actualPagina = 1
    lineasASaltar = []
    linea = sigLinea()
    for dato in datos:
        # LE PIYAMA
        # Hay que hacerlo ANTES de escribir porque no hay manera de ordenar 
        # capas en el canvas. ¿Problema? Que no sé el alto de la fila hasta 
        # que no termine de escribir todas las columnas.
        if pijama:
            xizq = lm - 4   #OJO: HARCODED. Ver def cabecera.
            xder = rm
            draw_fondo_pijama(hoja, 
                              xizq, linea, 
                              xder,  
                              datos.index(dato), 
                              dato, xcampo, fuente, tamanno, 
                              cols_a_derecha, cols_centradas)
        # EOLP

        d = list(dato)
        lineasASaltar = []
        for i in range(len(d)):
            try:
                xizq, xder = xcampo[i], xcampo[i+1]
            except IndexError:
                xizq, xder = xcampo[i], rm
            ## "Parser" de códigos especiales: ################
            # Extensión de límite derecho (">->")
            j = i+1
            while j < len(d) and d[j] == ">->":
                try:
                    xder = xcampo[j+1]
                except IndexError:
                    xder = rm
                j += 1
            if d[i] == "---":
                hoja.saveState()
                hoja.setLineWidth(0.5)
                lineasSumadas = 1
                hoja.line(xizq, linea, xder, linea)
                hoja.restoreState()
            elif d[i] == "===":
                hoja.saveState()
                hoja.setLineWidth(0.5)
                lineasSumadas = 1
                hoja.line(xizq, linea+1, xder, linea+1)
                hoja.line(xizq, linea-1, xder, linea-1)
                hoja.restoreState()
            elif d[i] == ">->":
                pass    # No escribo nada en el PDF. El espacio ya ha sido
                        # ocupado por la columna anterior cuyo dato != >->
            else:
                # Colores   (de momento es un poco cutre, pero no voy a
                #            escribir un compilador ni me voy a inventar un
                #            lenguaje de marcado sólo para poder poner un par
                #            de colores cómodamente).
                hoja.setFillColor(colors.black)
                try:
                    keycad_rgb = "[color=RGB{"
                    endkeycad_rgb = "}]"
                    if "[color=rojo]" in d[i]:
                        d[i] = d[i].replace("[color=rojo]", "")
                        hoja.setFillColor(colors.red)
                    elif "[color=verde]" in d[i]:
                        d[i] = d[i].replace("[color=verde]", "")
                        hoja.setFillColor(colors.green)
                    elif "[color=azul]" in d[i]:
                        d[i] = d[i].replace("[color=azul]", "")
                        hoja.setFillColor(colors.blue)
                    elif "[color=gris]" in d[i]:
                        d[i] = d[i].replace("[color=gris]", "")
                        hoja.setFillColor(colors.gray)
                    elif keycad_rgb in d[i]:
                        desde = d[i].index(keycad_rgb) + len(keycad_rgb)
                        hasta = d[i].index(endkeycad_rgb) 
                        strcolor = d[i][desde:hasta]
                        d[i] = d[i][:desde] + d[i][hasta:]
                        d[i] = d[i].replace(keycad_rgb, "")
                        d[i] = d[i].replace(endkeycad_rgb, "")
                        r, g, b = map(float, strcolor.split(","))
                        hoja.setFillColorRGB(r, g, b)
                    # XXX: Cambio de fuente. 
                    old_fuente = fuente
                    old_tamanno = tamanno
                    d[i], fuente, tamanno = parse_fuente(d[i], hoja)
                    if fuente == None:
                        fuente = old_fuente
                    if tamanno == None:
                        tamanno = old_tamanno
                except TypeError, msg:      # Se nos ha colado un entero,
                                            # probablemente.
                    # print msg, type(d[i]), d[i]
                    pass
            ## EOP ############################################
                lineasSumadas = agregarFila(xizq,
                                            linea,
                                            xder,
                                            escribe(d[i]),
                                            hoja,
                                            fuente,
                                            tamanno,
                                            a_derecha = i in cols_a_derecha,
                                            centrado = i in cols_centradas)
            lineasASaltar.append(lineasSumadas)
            # Restauro fuente y tamaño:
            fuente = old_fuente
            tamanno = old_tamanno
            # Si he cambiado de color, vuelvo al negro.
            hoja.setFillColor(colors.black) 

        contLinea += max(lineasASaltar)
        if contLinea >= MAXLINEAS:
            pie(hoja, actualPagina, paginas, apaisado = apaisado)
            hoja.showPage()
            contLinea = 0
            actualPagina += 1
            cabecera(hoja, titulo, fecha, apaisado = apaisado)
            linea = yCabecera
            # El cuerpo
            x, y = lm, tm
            yCabecera = tm + inch
            hoja.setFont("Helvetica-Bold", 9)
            #hoja.setFont("Helvetica-Bold", 10)
            for sobrecampo, posicion in sobrecampos:
                posicion_sobrecampo = ((lm - 4)
                                        + (1.0 * posicion * anchoHoja / 100))
                hoja.drawCentredString(posicion_sobrecampo,
                                       yCabecera + 0.3 * cm,
                                       escribe(sobrecampo))
            hoja.saveState()
            for linea_vertical, hasta_arriba in lineas_verticales:
                ancho = anchoHoja
                arriba = height - inch
                abajo = bm - 0.2 * inch
                medio = yCabecera - 2
                posicion_linea_vertical = ((lm - 4)
                    + (1.0 * linea_vertical * ancho / 100) + 2)   # Para que
                                # no pise a las columnas alineadas a la dcha.
                if hasta_arriba:
                    hoja.setLineWidth(0.4)
                    hoja.setDash()
                    hoja.line(posicion_linea_vertical, arriba,
                              posicion_linea_vertical, medio)
                hoja.setLineWidth(0.2)
                hoja.setDash(1, 4)  # 1 punto negro, 4 blancos
                hoja.line(posicion_linea_vertical, medio,
                          posicion_linea_vertical, abajo)
            hoja.restoreState()
            for i in range(len(campos)):
                try:
                    #hoja.drawCentredString((xcampo[i]+xcampo[i+1])/2,
                    #                       yCabecera, escribe(campos[i][0]))
                    el_encogedor_de_fuentes_de_doraemon(hoja, fuente, tamanno,
                        xcampo[i], xcampo[i+1], yCabecera, campos[i][0],
                        alineacion = 0)
                except IndexError:
                    #hoja.drawCentredString((xcampo[i]+rm)/2, yCabecera,
                    #                       escribe(campos[i][0]))
                    el_encogedor_de_fuentes_de_doraemon(hoja, fuente, tamanno,
                        xcampo[i], rm, yCabecera, campos[i][0], alineacion = 0)
            hoja.line(lm, yCabecera-2, rm, yCabecera-2)
            hoja.setFont(fuente, tamanno)
            x = lm
            linea = sigLinea()
        else:
            for i in range(max(lineasASaltar)):
                linea = sigLinea()
            x = lm
    hoja.drawText(texto)
    # AQUÍ LOS GRÁFICOS.
    for imagen in graficos:
        ancho, alto = get_ancho_alto(imagen, limiteh = rm - lm)
    # TODO: Comprobar que no se sale de los márgenes ni de la página, que se
    # pasa de página si no cabe, que se incrementa el número de páginas, etc...
        linea = linea - alto
        hoja.drawImage(imagen, lm, linea - 1 * cm)
    # Ponemos el pie
    pie(hoja, actualPagina, paginas, apaisado = apaisado)
    # Salvamos la página
    hoja.showPage()
    # Salvamos el documento
    hoja.save()
    # Antes de salir voy a dejar las globales como estaban (vaya horror,
    # coños, andar a estas alturas peleándome con globales, grrrr):
    rm, tm, width, height, MAXLINEAS = apaisar(False)
    nomarchivo = archivo
    if not nomarchivo.lower().endswith(".pdf"):
        nomarchivo += '.pdf'
    return nomarchivo 

def draw_fondo_pijama(c, x0, y0, x1, contador, 
                      datos_col, xcoords, fuente, tamanno, 
                      cols_a_derecha, cols_centradas, 
                      rgbcolor = (0.8, 0.9, 0.7)):
    """
    Dibuja un rectángulo del color recibido entre las coordenadas (x0, y0) y 
    (x1, y0 + #líneas de texto * altura) siempre que el contador sea impar.
    La coordenada "y" final puede no coincidir con la recibida si para 
    mostrar los textos de «datos_col» se necesita más de una línea.
    """
    if contador % 2:
        # Miro la altura final con la ayuda de 
        # el_encogedor_de_fuentes_de_doraemon
        d = list(datos_col)
        xcampo = xcoords
        lineasASaltar = []
        for i in range(len(d)):
            try:
                xizq, xder = xcampo[i], xcampo[i+1]
            except IndexError:
                xizq, xder = xcampo[i], rm
            ## "Parser" de códigos especiales: ################
            # Extensión de límite derecho (">->")
            j = i+1
            while j < len(d) and d[j] == ">->":
                try:
                    xder = xcampo[j+1]
                except IndexError:
                    xder = rm
                j += 1
            lineasSumadas = agregarFila(xizq,
                                        y0,
                                        xder,
                                        escribe(d[i]),
                                        c,
                                        fuente,
                                        tamanno,
                                        a_derecha = i in cols_a_derecha,
                                        centrado = i in cols_centradas, 
                                        simular = True)
            lineasASaltar.append(lineasSumadas)
        lineas = (max(lineasASaltar))
        altura_linea = 10   # OJO: HARCODED a valor por defecto de agregarFila
        h = lineas * altura_linea
        for i in range(lineas-1):
            y0 = sigLinea(valor = altura_linea, actual = y0)
        # Dibujo el fondo en sí.
        r, g, b = rgbcolor
        c.saveState()
        c.setFillColorRGB(r, g, b)
        c.setStrokeColorRGB(r, g, b)
        c.setLineWidth(1)
        c.rect(x0+1, y0 - 7, 
               abs(x1-x0-2), h + 5, 
               fill = 1)
        c.restoreState()

def get_ancho_alto(imagen, limitev = None, limiteh = None):
    """
    Devuelve el ancho y el alto de la imagen
    correspondiente al nombre de fichero recibido.
    ¡Necesita PIL!
    Si limiteh es distinto de None, se redimensiona la
    imagen en caso de que supere el límite horizontal.
    Lo mismo con limitev.
    """
    try:
        i = Image.open(imagen)
    except IOError:
        print "informes.py (get_ancho_alto): Imagen %s no encontrada." % (
            imagen)
        return (0, 0)
    ancho, alto = i.size
    ratio = float(alto) / ancho
    if limiteh:
        ancho = int(limiteh)
        alto = int(ancho * ratio)
    if limitev:
        if alto > limitev:
            alto = int(limitev)
            ancho = int((1 / ratio) * alto)
    i = i.resize((ancho, alto), Image.BICUBIC)
    i.save(imagen)
    return i.size

def abreviar(cad, l = 8):
    """
    Acorta una cadena hasta dejarla en una longitud «l» intentando 
    respetar la primera palabra.
    """
    separadores = (" ", "_", ",", ".")
    while len(cad) > l:
        for separador in separadores:
            palabras = cad.split(separador)
            # Si de entrada la primera palabra ya es mayor, mal empezamos.
            if len(palabras[0]) > l:
                palabras[0] = palabras[0][:-1]
            # Intento respetar la primera palabra y acorto solo las demás.
            if sum([len(p) for p in palabras]) > l:
                for i in range(1, len(palabras)):
                    palabras[i] = palabras[i][:-1]
            cad = separador.join(palabras)
            # Si solo en separadores me voy a comer el espacio...
            if cad.count(separador) > l:
                cad = cad[::-1].replace(separador, "", 1)[::-1]
            cad = cad.strip()
    return cad

def corregir_nombres_fecha(s):
    """
    Porque todo hombre debe enfrentarse al menos una
    vez en su vida a dos tipos de sistemas operativos:
    los que se no se pasan por el forro las locales,
    y MS-Windows.
    """
    trans = {'Monday': 'lunes',
             'Tuesday': 'martes',
             'Wednesday': 'miércoles',
             'Thursday': 'jueves',
             'Friday': 'viernes',
             'Saturday': 'sábado',
             'Sunday': 'domingo',
             'January': 'enero',
             'February': 'febrero',
             'March': 'marzo',
             'April': 'abril',
             'May': 'mayo',
             'June': 'junio',
             'July': 'julio',
             'August': 'agosto',
             'September': 'septiembre',
             'October': 'octubre',
             'November': 'noviembre',
             'December': 'diciembre'}
    for in_english in trans:
        s = s.replace(in_english, trans[in_english])
    return s

def cuadrito(c, x, y, relleno):
    """
    Dibuja en checkbox en el pdf y lo rellena
    si el parámetro está a 1
    """
    c.rect(x, y, 4, 4, fill = relleno)

def escribir_mail(c, x, y, email):
    """
    Escribe y hace "clicable" la dirección de correo electrónico «email»
    en la posición (x, y) del canvas «c».
    """
    from reportlab.lib import colors
    c.saveState()
    c.setFont("Courier", 10)
    c.setFillColor(colors.blue)
    c.drawString(x, y, escribe(email))
    ancho = c.stringWidth(email, "Courier", 10)
    rect = (x, y, x + ancho, y + 0.5*cm)
    c.linkURL("mailto:%s" % (email), rect)
    c.restoreState()

# ------------------------- PRUEBINES, GUAJE -------------------------
def pruebines():
    params = {'archivo': give_me_the_name_baby("test_"),
              'titulo': "Pruebines, guaje.",
              'campos': (("Campo 1", 50), 
                         ("Campo 2", 50)),
              'datos': (("Valor 0.1", 0), 
                        ("Valor 0.2", 1.33)),
              'fecha': None,
              'cols_a_derecha': (),
              'graficos': [],
              'apaisado': False,
              'sobrecampos': (),
              'lineas_verticales': (),
              'exportar_a_csv_a': None,
              'cols_centradas': (), 
              'pijama': False}
    abrir_pdf(generar_pdf(**params))

# --------------------------------------------------------------------


if __name__=='__main__':
    pruebines()

