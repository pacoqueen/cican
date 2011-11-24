#!/usr/bin/env python
# -*- coding: utf-8 -*-

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.platypus import TableStyle, Image, XPreformatted, Preformatted 
from reportlab.platypus import PageBreak, KeepTogether, CondPageBreak
from reportlab.platypus import LongTable
from reportlab.platypus.flowables import Flowable
from reportlab.rl_config import defaultPageSize
from reportlab.lib import colors, enums
from reportlab.lib.units import cm
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
import sys, os#, Image

midir = os.path.split(os.path.dirname(os.path.abspath(__file__)))[-1]
if os.path.realpath(os.path.curdir).split(os.path.sep)[-1] == midir:
    sys.path.append("..")
root, dirs, files = os.walk(".").next()
if "utils" in dirs:
    sys.path.insert(0, ".")

from framework import pclases
from utils.fixedpoint import FixedPoint
from utils.informes import give_me_the_name_baby, escribe, rectangulo
from utils.informes import el_encogedor_de_fuentes_de_doraemon, agregarFila
from utils import numero, misc, fecha, numerals
from tempfile import gettempdir

PAGE_HEIGHT = defaultPageSize[1]; PAGE_WIDTH = defaultPageSize[0]
estilos = getSampleStyleSheet()


def build_datos_peticion(peticion):
    parrafos = []
    hora = peticion.horaRecogida.strftime("%H:%M")
    datos_recogida = "{0}{1}".format(peticion.obra.get_info(), 
        peticion.direccion 
            and " - " + peticion.direccion.get_direccion_completa()
            or "")
    p = Paragraph("{:>6}: {:s}".format(hora, datos_recogida), estilos["Definition"])
    parrafos.append(p)
    ensayos = [] 
    for e in peticion.ensayos:
        p = Paragraph(e.get_info(), estilos["Bullet"])
        ensayos.append(p)
    parrafos.append(ensayos)
    return parrafos

def build_datos_laborante(laborante):
    p = Paragraph(laborante.get_nombre_completo(), estilos["Title"])
    return p

def go(ruta_archivo, 
       laborante, 
       peticiones, 
       titulo = "Hoja de ruta", ):
    doc = SimpleDocTemplate(ruta_archivo, 
                            title = titulo, 
                            topMargin = 2.30 * cm, 
                            bottomMargin = 2 * cm)
    datos_laborante = build_datos_laborante(laborante)
    logo = build_logo_cabecera()
    story = [logo, datos_laborante]
    for fecha in peticiones:
        story.append(build_fecha(fecha))
        for peticion in peticiones[fecha]:
            datos_peticion = build_datos_peticion(peticion)
            story.append(datos_peticion)
    story = misc.aplanar(story)
    doc.build(story)
    return ruta_archivo

def build_logo_cabecera():
    try:
        ruta_logo = pclases.DatosDeLaEmpresa.select()[0].logo
    except:
        logo = Paragraph("", estilos["Normal"])
    else:
        ruta_imagenes = os.path.join(midir, "..", "imagenes")
        logo = Image(os.path.join(ruta_imagenes, ruta_logo))
        logo.drawHeight = 2*cm * logo.drawHeight / logo.drawWidth
        logo.drawWidth = 2*cm
    t = Table([[logo, Paragraph("Hoja de ruta", estilos["Heading2"])]])
    return t

def build_fecha(f):
    p = Paragraph(f.strftime("%d/%m/%Y"), estilos["Heading1"])
    return p

def gettempfilename(nombre = ""):
    """
    Devuelve una ruta de fichero tomando como base «nombre». Usa una marca de 
    tiempo para evitar conflictos de nombre, ya que siempre devolverá una 
    ruta en el directorio temporal del usuario.
    """
    nomarchivo = "{0}_{1}.pdf".format(nombre, give_me_the_name_baby())
    ruta = os.path.join(gettempdir(), nomarchivo)
    return ruta

def hoja_ruta(laborante, peticiones, basefilename = "hoja_ruta"):
    """
    Recibe un laborante y una lista de peticiones. Genera un PDF con 
    el nombre del laborante y las peticiones en el orden en que estén 
    en la lista.
    """
    basefilename += "".join([i[0].lower() 
                             for i in laborante.get_nombre_completo().split()])
    nomarchivo = gettempfilename(basefilename)
    peticiones = clasificar_peticiones(peticiones)
    nomarchivo = go(nomarchivo, 
                    laborante, 
                    peticiones, 
                    "Hoja de ruta - {0}".format(
                        laborante.get_nombre_completo()))
    return nomarchivo

def clasificar_peticiones(ps):
    res = {}
    for p in ps:
        fecha = p.fechaRecogida
        try:
            res[fecha].append(p)
        except KeyError:
            res[fecha] = [p]
    for fecha in res:
        res[fecha].sort(key = lambda p: p.horaRecogida)
    return res


if __name__ == "__main__":
    from utils.informes import abrir_pdf
    from __init__ import * 
    abrir_pdf(hoja_ruta(pclases.Empleado.select()[0], 
                        pclases.Peticion.select()[:5]))

