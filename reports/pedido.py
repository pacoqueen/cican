#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
# Copyright (C) 2005-2011  Francisco José Rodríguez Bogado                    #
#                          (pacoqueen@users.sourceforge.net)                  #
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

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.platypus import TableStyle, Image, XPreformatted, Preformatted 
from reportlab.platypus import PageBreak, KeepTogether, CondPageBreak
from reportlab.platypus import LongTable
from reportlab.platypus.flowables import Flowable
from reportlab.lib import colors, enums
from reportlab.lib.pagesizes import A4, A5
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
from reports.factura_multipag import LineaHorizontal,Linea,TablaFija,sanitize

#ALTO = A4[1] / 2; ANCHO = A4[0] / 2
#ALTO = A4[0]; ANCHO = A4[1] / 2
ALTO = A5[1]; ANCHO = A5[0]
estilos = getSampleStyleSheet()
MARGEN_IZQUIERDO = MARGEN_DERECHO = 0.5*cm

def build_encabezado(lineas_empresa, dpeticion):
    """
    Cuadro de encabezado con el logotipo de la empresa (posición 0 de 
    lineas_empresa) y los datos recibidos (posiciones 1 en adelante).
    """
    logo = lineas_empresa[0]
    info = lineas_empresa[1:]
    #estilos["h6"].fontSize -= 2
    estilos["h6"].spaceAfter = 0
    estilos["h6"].spaceBefore = 0
    if lineas_empresa [0]:
        logo = Image(lineas_empresa[0])
        logo.drawHeight = 1.5*cm * logo.drawHeight / logo.drawWidth
        logo.drawWidth = 1.5*cm
    else:
        logo = Paragraph("", estilos["h6"])
    lineas_empresa = lineas_empresa[1:]
    #if len(lineas_empresa) <= 3:
    #    empresa = Preformatted("\n".join(lineas_empresa) + 
    #        "\nHoja n.º: {hoja}"
    #        "\nFecha pedido: {fecha pedido}".format(**dpeticion),
    #        estilos["h6"])
    #else:
    #    texto_empresa = lineas_empresa[0] + "\n"
    #    resto_lineas = lineas_empresa[1:]
    #    pivot = len(resto_lineas)/2
    #    r1, r2 = resto_lineas[:pivot], resto_lineas[pivot:]
    #    texto_empresa += ". ".join(r1) + "\n" + ". ".join(r2)
    #    empresa = Preformatted(texto_empresa + 
    #        "\nHoja n.º: {hoja:d}"
    #        "\nFecha pedido: {fecha pedido:s}".format(**dpeticion), 
    #        estilos["h6"])
    empresa = []
    for l in lineas_empresa:
        empresa.append(Paragraph(l, estilos["h6"]))
    estilos["h2"].spaceAfter = 0
    estilos["h2"].spaceBefore = 0
    estilos["h2"].alignment = enums.TA_LEFT
    estilos["h2"].fontSize = 10
    estilos["h2"].leading = 10
    empresa.append(Paragraph("Hoja n.º: {hoja:d}".format(**dpeticion), 
                             estilos["h2"]))
    empresa.append(Paragraph(
                    "Fecha pedido: {fecha pedido:s}".format(**dpeticion), 
                    estilos["h2"]))
    estilos["h5"].alignment = enums.TA_CENTER
    datos = ([logo, 
              Paragraph("SOLICITUD DE RECOGIDA", estilos["h5"]), 
              empresa], 
            )
    #encabezado = TablaFija(MARGEN_IZQUIERDO + 5.9*cm, ALTO - 3*cm, 
    encabezado = TablaFija(MARGEN_IZQUIERDO + 4*cm, ALTO - 3*cm, 
        datos, hAlign = enums.TA_CENTER, colWidths = (
            (ANCHO - MARGEN_IZQUIERDO - MARGEN_DERECHO - 4*cm) * (1/4.), 
            (ANCHO - MARGEN_IZQUIERDO - MARGEN_DERECHO) * (1/4.), 
            (ANCHO - MARGEN_IZQUIERDO - MARGEN_DERECHO) * (1/2.)))
    encabezado.setStyle(TableStyle([
        ("ALIGN", (0, 0), (1, 0), "CENTER"),
        ("ALIGN", (2, 0), (2, 0), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),  
        ]))
    return encabezado

def build_datos_cliente(dobra, dpedido):
    """
    Escribe los datos de los diccionarios recibidos en una lista de párrafos.
    """
    estilos["h4"].spaceAfter = 0
    estilos["h4"].spaceBefore = 2
    #estilos["h4"].fontSize -= 2
    cliente = Paragraph(escribe("CLIENTE: {cliente}".format(**dobra)), 
                        estilos["h4"])
    obra = Paragraph(escribe("OBRA: {obra}".format(**dobra)), 
                     estilos["h4"])
    solicitante = Paragraph(escribe(
                                "SOLICITANTE: {solicitante}".format(**dobra)), 
                            estilos["h4"])
    contacto = Paragraph(escribe(
        "PERSONA DE CONTACTO: {persona de contacto}".format(**dobra)), 
        estilos["h4"])
    fecha = Paragraph("FECHA: {fecha recogida}".format(**dpedido), 
                      estilos["h4"])
    res = [cliente, obra, solicitante, contacto, fecha]
    return res

def build_tabla_contenido(dic_material, lineas_ensayo, dic_peticion):
    """
    Devuelve una lista de párrafos y líneas horizontales con las cuatro filas 
    de material, ensayos, observaciones y persona que recogió el pedido. 
    Extrae los datos que necesita de los diccionarios recibidos.
    """
    linea = LineaHorizontal(ANCHO)# - MARGEN_IZQUIERDO - MARGEN_IZQUIERDO - 1*cm) 
    # Para que la última línea de "recibido" esté pegada al fondo de la página 
    # hay que meter espacio en observaciones (dejando, de paso, espacio para 
    # anotaciones a boli). Como la página se construye dinámicamente, tengo 
    # que estimar el espacio que falta en función a la información escrita 
    # hasta ahora.
    #restante = 2*cm
    # TODO: Empiezo con una estimación al azar. Ya afinaré o acabaré 
    # metiendo la línea "Recibido" como pie de página igual que hice con 
    # los totales de factura_multipag.
    #espacio = Spacer(ANCHO, restante)
    estilos["Normal"].leading = 8
    estilos["Normal"].leftIndent = 10
    estilos["BodyText"].leftIndent = 30
    #estilos["Normal"].fontSize -= 2
    material0 = Paragraph("<u>MATERIAL A ENSAYAR:</u>", estilos["Normal"])
    material1 = Paragraph(escribe(dic_material["material"]), 
                          estilos["BodyText"])
    #material = Table([[material0], [material1]], hAlign = enums.TA_LEFT, 
    #    colWidths = (ANCHO))
    #material.setStyle(TableStyle([
    #    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    #    ('LINEABOVE', (0, 0), (-1, 0), 1, colors.black),  
    #    ('LINEBELOW', (0, 1), (-1, 1), 1, colors.black),  
    #    ]))
    ensayos0 = Paragraph("<u>ENSAYOS SOLICITADOS:</u>", estilos["Normal"])
    ensayos1 = []   # Después se "aplanará"
    if not lineas_ensayo:
        lineas_ensayo = [""]    # Que haya al menos un huequín que haga bonito.
    for ensayo in lineas_ensayo:
        ensayos1.append(Paragraph(escribe(ensayo), estilos["BodyText"]))
    observaciones0 = Paragraph("<u>OBSERVACIONES:</u>", estilos["Normal"])
    observaciones1 = Paragraph(escribe(dic_peticion["observaciones"]), 
                               estilos["BodyText"])
    recibido0 = Paragraph("Recibido por:", estilos["Normal"])
    recibido1 = Paragraph(escribe(dic_peticion["recibido por"]), 
                          estilos["BodyText"])
    res = [linea, Spacer(1, 0.05*cm), material0, material1, Spacer(1, 0.2*cm),
           linea, Spacer(1, 0.05*cm), ensayos0, ensayos1, Spacer(1, 0.2*cm),
           linea, Spacer(1, 0.05*cm), observaciones0, observaciones1]
           # , espacio, linea, recibido0, 
           # recibido1, Spacer(1, 0.2*cm), linea]
    recibido = TablaFija(MARGEN_IZQUIERDO + 4*cm, 1*cm, 
        [[recibido0], [recibido1]], hAlign = enums.TA_LEFT, 
        colWidths = (ANCHO)
        ) 
    recibido.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ('LINEABOVE', (0, 0), (-1, 0), 1, colors.black),  
        ('LINEBELOW', (0, 1), (-1, 1), 1, colors.black),  
        ]))
    res.append(recibido)
    return res

def go(titulo,
       ruta_archivo,
       lineas_empresa,
       dic_peticion,
       dic_obra,
       dic_material, 
       lineas_ensayo):
    """
    Recibe el título del documento y la ruta completa del archivo PDF,
    una lista de líneas con la información de la empresa, un diccionario con 
    los datos de la petición, otro con los de la obra, otro con los del 
    material a ensayar y una lista de cadenas con los ensayos a realizar.
    La primera posición de la lista de datos de la empresa es la ruta al 
    logotipo (cadena vacía si no se quiere logotipo).
    """
    doc = SimpleDocTemplate(ruta_archivo,
                            title = titulo,
                            topMargin = 0.5*cm,
                            bottomMargin = 0.5*cm,
                            leftMargin = MARGEN_IZQUIERDO,
                            rigthMargin = MARGEN_DERECHO, 
                            pagesize = (ANCHO, ALTO), 
                            showBoundary = 0)   # 1 para "debug"
    encabezado = build_encabezado(lineas_empresa, dic_peticion)
    datos_cliente = build_datos_cliente(dic_obra, dic_peticion)
    contenido = build_tabla_contenido(dic_material, lineas_ensayo, dic_peticion)
    story = [encabezado,
             #Spacer(1, 0.1 * cm),
             datos_cliente, 
             Spacer(1, 1 * cm),
             contenido
             # Linea((ANCHO - 1.05*cm, 24.5*cm - 3*cm),
             #       (ANCHO - 1.05*cm, 2.5*cm + 3*cm + 0.25*cm)),
             # Spacer(1, 0.15 * cm),
             # Línea doble.
             #KeepTogether([LineaHorizontal(0.9 * ANCHO),
             #              Spacer(1, 0.05 * cm),
             #              LineaHorizontal(0.9 * ANCHO)]),
             #CondPageBreak(13*cm),
            ]
    story = misc.aplanar([i for i in story if i])
    doc.build(story)
    return ruta_archivo

def go_from_peticion(peticion):
    """
    Construye el PDF a partir de un objeto peticion y no de sus datos
    sueltos.
    """
    obra = peticion.obra
    cliente = obra.cliente
    direccion = obra.direccion
    if not direccion:
        direccion = pclases.Direccion.get_direccion_por_defecto()
    ciudad = direccion.ciudad
    provincia = ciudad.provincia
    datos_peticion = {"hoja": peticion.id, 
                      "fecha pedido": 
                        fecha.str_fecha(peticion.fechaSolicitud), 
                      "fecha recogida":  
                        fecha.str_fecha(peticion.fechaRecogida), 
                      "hora": fecha.str_hora_corta(peticion.horaRecogida), 
                      "observaciones": peticion.observaciones, 
                      "recibido por": 
                        peticion.usuario and peticion.usuario.nombre or ""}
    strobra = obra and obra.nombre or ""
    if obra and obra.direccion:
        strobra += "({0})".format(obra.direccion.get_direccion_completa())
    datos_obra = {"cliente": cliente and cliente.nombre or "", 
                  "obra": obra, 
                  "solicitante": peticion and peticion.solicitante or "",
                  "persona de contacto": peticion and peticion.contacto 
                    and peticion.contacto.get_nombre_completo() or ""}
    datos_material = {"material": peticion.material 
                        and peticion.material.nombre or ""}
    datos_ensayo = [e.nombre for e in peticion.ensayos]
    try:
        dde = pclases.get_dde()
        datos_de_la_empresa = [os.path.join("imagenes", dde.logo),
                               #dde.nombre +
                               # (dde.cif and " (" + dde.str_cif_o_nif() +": " 
                               #  + dde.cif + ")" or ""),
                               dde.direccion,
                               "%s %s (%s), %s" % (dde.cp,
                                                   dde.ciudad,
                                                   dde.provincia,
                                                   dde.pais),
                               ]
        if dde.fax:
            if dde.fax.strip() == dde.telefono.strip():
                datos_de_la_empresa.append("Telf. y fax: %s" % dde.telefono)
            else:
                datos_de_la_empresa.append("Telf.: %s" % (dde.telefono))
                datos_de_la_empresa.append("Fax: %s" % (dde.fax))
        #if dde.email:
        #    datos_de_la_empresa.append(dde.email)
    except IndexError:
        datos_de_la_empresa = [None]
    nomarchivo = os.path.join(gettempdir(),
                              "peticion_{0}_{1}.pdf".format(
                                peticion.id, give_me_the_name_baby()))
    return go("Peticion {0}".format(peticion.id), 
              nomarchivo,
              datos_de_la_empresa,
              datos_peticion,
              datos_obra, 
              datos_material,
              datos_ensayo)


if __name__ == "__main__":
    try:
        print go_from_peticion(pclases.Peticion.select()[-1])
    #except Exception, msg:
    except ZeroDivisionError, msg:
        sys.stderr.write(`msg`)
        datos_peticion = {"hoja": 123, 
                          "fecha pedido": "09/09/2011", 
                          "fecha recogida": "20/09/2011", 
                          "hora": "05:11", 
                          "observaciones": "Ninguna", 
                          "recibido por": "La teniente Ripley"}
        datos_obra = {"cliente": "Nike+", 
                      "obra": "UTE efe 8 (Calle de AC/DC, Leganés)", 
                      "solicitante": "Asafa Powell", 
                      "persona de contacto": "Usain Bolt"}
        datos_material = {"material": "Hormigón"}
        datos_ensayo = ["10 series", "20 series"]
        datos_de_la_empresa = ["imagenes/dorsia.png",
                               "P. Ind. Amudayne",
                               "Ctra. N-IV Km.: 678",
                               "Los Palacios y Villafranca (Sevilla)", 
                               "Tlno.: 955811245 Fax: 955812545"]
        print go("Solicitud de recogida",
                 "/tmp/peticion.pdf",
                 datos_de_la_empresa,
                 datos_peticion,
                 datos_obra,
                 datos_material, 
                 datos_ensayo)

