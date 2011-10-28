#!/usr/bin/env python
# -*- coding: utf-8 -*-

import reportlab
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import inch, cm
from os.path import join as pathjoin
from tempfile import gettempdir
import time, datetime
import sys, os
try:
    import utils
except ImportError:
    sys.path.insert(0, ".")
    import utils
try:
    from framework import pclases
except ImportError:
    import sys
    sys.path.insert(0, ".")
from utils.informes import * 

MAXLINEAS = 47 
WIDTH, HEIGHT = A4
# Márgenes (Considero el margen superior lo que está por debajo del
# encabezamiento.)
TM, BM, LM, RM = (680, 56.69, 28.35, 566.92)

def gettempfilename(nombre = ""):
    """
    Devuelve una ruta de ficero tomando como base «nombre». Usa una marca de 
    tiempo para evitar conflictos de nombre, ya que siempre devolverá una 
    ruta en el directorio temporal del usuario.
    """
    nomarchivo = "{0}_{1}.pdf".format(nombre, give_me_the_name_baby())
    ruta = pathjoin(gettempdir(), nomarchivo)
    return ruta

def simple(texto, titulo = "", basefilename = "simple", 
           watermark = "BORRADOR"):
    """
    Simplemente vuelca el texto recibido en un PDF.
    Si watermark es None, no se imprime. En otro caso se pone una marca de 
    agua con el texto recbido como fondo de la hoja.
    """
    una_linea = -12
    TM, BM, LM, RM = (680, 56.69, 28.35, 566.92)
    nomarchivo = gettempfilename(basefilename)
    c = canvas.Canvas(nomarchivo)
    c.setPageSize(A4)
    fuente, tamanno = "Helvetica", 10
    c.setFont(fuente, tamanno)
    lineas = texto.split("\n")
    while lineas:
        cabecera(c, titulo, utils.fecha.str_fecha(datetime.date.today()))
        # Marca "borrador"
        if watermark:
            c.saveState()
            c.setFont("Courier-BoldOblique", 42)
            ancho = c.stringWidth(watermark, "Courier-BoldOblique", 42)
            c.translate(A4[0] / 2.0, A4[1] / 2.0)
            c.rotate(45)
            c.setLineWidth(3)
            c.setStrokeColorRGB(1.0, 0.7, 0.7)
            c.setFillColorRGB(1.0, 0.7, 0.7)
            c.rect((-ancho - 10) / 2.0, -5, (ancho + 10), 37, fill = False)
            c.drawCentredString(0, 0, watermark)
            c.rotate(-45)
            c.restoreState()
        # EOMarca "borrador"
        x, y = LM, TM + 2.5 * cm
        while y >= BM and lineas:
            linea = lineas.pop(0)
            saltos = agregarFila(x, y, RM, escribe(linea), c, fuente, tamanno,
                                 a_derecha = False, altura_linea = -una_linea)
            y += una_linea * saltos
        c.showPage()
    c.save()
    return nomarchivo

if __name__ == "__main__":
    from utils.informes import abrir_pdf
    from __init__ import * 
    abrir_pdf(simple("Un texto\nmultilínea", titulo = "Test"))

