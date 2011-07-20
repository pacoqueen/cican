#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
# Copyright (C) 2005-2010  Francisco José Rodríguez Bogado                    #
#                          <bogado@qinn.es>                                   #
#                                                                             #
# This file is part of $NAME.                                                 #
#                                                                             #
# $NAME is free software; you can redistribute it and/or modify               #
# it under the terms of the GNU General Public License as published by        #
# the Free Software Foundation; either version 2 of the License, or           #
# (at your option) any later version.                                         #
#                                                                             #
# $NAME is distributed in the hope that it will be useful,                    #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU General Public License for more details.                                #
#                                                                             #
# You should have received a copy of the GNU General Public License           #
# along with $NAME if not, write to the Free Software                         #
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA  #
###############################################################################


###################################################################
## facturas_venta.py - Facturas de venta. 
###################################################################


import gtk
from seeker import VentanaGenerica
from framework import pclases
import gobject
import utils
import os
from framework.configuracion import ConfigConexion
from utils.ui import escalar_a
from formularios.ventana_generica import _abrir_en_ventana_nueva
from informes.factura_multipag import go_from_facturaVenta as imprimir_factura
from utils.informes import abrir_pdf

class FacturasVenta(VentanaGenerica): 
    def __init__(self, objeto = None, usuario = None, run = True):
        """
        Constructor. objeto puede ser un objeto de pclases con el que
        comenzar la ventana (en lugar del primero de la tabla, que es
        el que se muestra por defecto).
        """
        __clase = pclases.FacturaVenta
        self.usuario = usuario
        VentanaGenerica.__init__(self, objeto = objeto, 
                                 usuario = self.usuario, 
                                 clase = __clase, run = False, 
                                 ventana_marco = 'facturas_venta.glade')
        connections = {}
        self.add_connections(connections)
        # Elementos que me interesa deshabilitar:
        for nombrecampo in ("tipoFacturaID", "serieNumericaID"):
            w = self.widgets_campos[nombrecampo]
            for c in w.parent.parent.parent.get_children():
                #c.set_sensitive(False)
                c.set_property("visible", False)
        # TreeViews adicionales:
        self.crear_treeviews()
        # Otros pequeños cambios:
        self.wids['label_relaciones'].set_text("Contenido de la factura")
        self.wids['obraID'].connect_after("changed", self.actualizar_retencion)
        self.wids['vencimientosCobro'].parent.parent.parent.reparent(
            self.wids['vbox_vtos_y_pagos'])
        self.wids['cobros'].parent.parent.parent.reparent(
            self.wids['vbox_vtos_y_pagos'])
        b_imprimir = gtk.Button(stock = gtk.STOCK_PRINT)
        self.wids['b_imprimir'] = b_imprimir
        b_imprimir.show()
        b_imprimir.connect("clicked", self.imprimir)
        self.wids['botonera'].pack_start(b_imprimir)
        self.wids['botonera'].reorder_child(b_imprimir, 0)
        self.wids['b_imprimir'].set_sensitive(self.objeto != None)
        # Siguiendo la estrategia de modificar la ventana DESPUÉS de haber 
        # montado todo lo genérico (en lugar de al revés, que sería lo suyo), 
        # quito el totalizador de líneas de venta, que no tiene sentido:
        self.wids['totalizador_lineasDeVenta'].set_property("visible", False)
        boton_recalcular = gtk.Button(label = "Recalcular")
        boton_recalcular.connect("clicked", self.calcular_totales)
        boton_recalcular.show()
        self.wids['botonera_vencimientosCobro'].pack_start(boton_recalcular, 
                                                           expand = True, 
                                                           fill = False)
        # Columna de subtotales:
        # TODO: Hay que hacer en utils.ui un método para añadir columnas 
        # a un TreeStore después de haberse creado. Mucho me temo que habrá 
        # crear un nuevo modelo y reasignarlo al TreeView. No hay métodos 
        # directos de gtk.* para añadir columnas "al vuelo".
        if run:
            gtk.main()

    def imprimir(self, boton):
        """
        Genera y abre un documento imprimible a partir de la factura. 
        """
        if not self.objeto.obra:
            utils.ui.dialogo_info(titulo = "SELECCIONE CLIENTE", 
                texto = "Debe seleccionar una obra para la factura.", 
                padre = self.wids['ventana'])
        else:
            if not self.objeto.formaDePago:
                formas_de_pago = [(f.puid, f.get_info()) for f in 
                                  pclases.FormaDePago.select(orderBy = "id")]
                fdp_puid = utils.ui.dialogo_radio(
                    titulo = "SELECCIONE FORMA DE PAGO", 
                    texto = "Debe seleccionar una forma de pago para la "
                            "factura.", 
                    padre = self.wids['ventana'], 
                    ops = formas_de_pago)
                if fdp_puid:
                    fdp = pclases.getObjetoPUID(fdp_puid)
                    self.objeto.formaDePago = fdp
                    self.objeto.syncUpdate()
                    self.objeto.retencion = fdp.retencion
                    self.actualizar_ventana()
                    # FIXME: No sé por qué todavía, pero hay que actualizar 
                    # dos veces la ventana para que el importe de la retención 
                    # sea correcto, si no le asigna lo mismo que al resto de 
                    # vencimientos.
                    self.actualizar_ventana()
                else:
                    return
            pdf_fra = imprimir_factura(self.objeto)
            if pdf_fra:
                abrir_pdf(pdf_fra)
            else:
                utils.dialogo_info(titulo = "ERROR IMPRESIÓN", 
                    texto = "Ocurrió un error al generar la copia"
                            " impresa de la factura.", 
                    padre = self.wids['ventana'])

    def actualizar_retencion(self, combo):
        id = utils.ui.combo_get_value(combo)
        obra = pclases.Obra.get(id)
        if obra.retencion != self.objeto.retencion:
            actualizar = utils.ui.dialogo(titulo = "¿ACTUALIZAR FACTURA?", 
                texto = "Ha cambiado el cliente de la factura.\n\n"
                        "¿Desea actualizar el porcentaje de retención\n"
                        "de acuerdo a los nuevos valores de la obra?", 
                padre = self.wids['ventana'])
            if actualizar:
                #self.objeto.retencion = obra.retencion
                # Que lo guarde si quiere. Yo solo lo pongo en ventana.
                self.escribir_valor(self.clase.sqlmeta.columns['retencion'], 
                                    obra.retencion)

    def crear_treeviews(self):
        if not self.wids['tv_muestras'].get_model():
            # Primero compruebo que no se hayan creado ya.
            for nombretv in ("tv_muestras", "tv_ensayos", "tv_informes"):
                utils.ui.preparar_listview(
                  self.wids[nombretv], 
                  (("Info", "gobject.TYPE_STRING", False, True, True, None), 
                   ("PUID", "gobject.TYPE_STRING", False, False, False, None)))
                self.wids[nombretv].connect("row_activated", 
                    _abrir_en_ventana_nueva, 
                    self.usuario) 
                self.wids[nombretv].set_headers_visible(False)

    def calcular_totales(self, *args, **kw):
        try:
            subtotal = self.objeto.calcular_subtotal()
        except AttributeError:
            subtotal = 0.0
        try:
            total = self.objeto.calcular_total()
        except AttributeError:
            total = 0.0
        try:
            importe_iva = self.objeto.calcular_importe_iva()
        except AttributeError:
            importe_iva = 0.0
        try:
            importe_retencion = self.objeto.calcular_importe_retencion()
        except AttributeError:
            importe_retencion = 0.0
        self.wids['e_subtotal'].set_text(utils.numero.float2str(subtotal, 2))
        self.wids['e_total_iva'].set_text(
            utils.numero.float2str(importe_iva, 2))
        self.wids['e_total'].set_text(utils.numero.float2str(total, 2))
        self.wids['e_importe_retencion'].set_text(
            utils.numero.float2str(importe_retencion, 2))
        # Y ahora me aseguro de que los vencimientos existen y coinciden:
        if self.objeto.check_vencimientos():
            colvtos = [c for c in self.objeto.sqlmeta.joins 
                       if c.joinMethodName == "vencimientosCobro"][0]
            try:
                self.rellenar_tabla(colvtos, coltotal = "importe", 
                            e_total = self.wids['e_total_vencimientosCobro'])
            except KeyError, e:
                print e

    def rellenar_widgets(self):
        # Experimentos con gaseosa:
        #for wname in ("e_fecha", "b_buscar_fecha"):
        #    self.wids[wname].set_property("visible", False)
        pixbuf_logo = gtk.gdk.pixbuf_new_from_file(
            os.path.join('imagenes', ConfigConexion().get_logo()))
        pixbuf_logo = escalar_a(100, 75, pixbuf_logo)
        self.wids['logo'].set_from_pixbuf(pixbuf_logo)
        VentanaGenerica.rellenar_widgets(self)
        self.rellenar_muestras_ensayos_informes()
        self.calcular_totales()

    def rellenar_muestras_ensayos_informes(self):
        tv_m = self.wids['tv_muestras']
        tv_e = self.wids['tv_ensayos']
        tv_r = self.wids['tv_informes']
        model_m = tv_m.get_model()
        try:
            model_m.clear()
        except AttributeError:  # Model no existe. TV no se ha preparado.
            self.crear_treeviews()
            model_m = tv_m.get_model()
            model_m.clear()
        model_e = tv_e.get_model()
        model_e.clear()
        model_r = tv_r.get_model()
        model_r.clear()
        ensayos = []
        muestras = []
        if self.objeto:
            for ldv in self.objeto.lineasDeVenta:
                for r in ldv.informes:
                    model_r.append((r.get_info(), r.puid))
                    if r.ensayo not in ensayos:
                        e = r.ensayo
                        model_e.append((e.get_info(), e.puid))
                        ensayos.append(e)
                    if r.muestra not in muestras:
                        m = r.muestra
                        model_m.append((m.get_info(), m.puid))
                        muestras.append(m)

    def nuevo(self, boton):
        """
        Crea una factura de venta nueva:
        0.- Pide el tipo de factura. 
        1.- Determina la serie de facturas en curso.
        2.- Obtiene el número de factura.
        3.- Crea la nueva factura con la fecha por defecto para evitar 
            entorpecer al usuario con preguntas. Si necesita cambiar la fecha, 
            que lo haga en la ventana y salve. Ya determinaremos si el 
            cambio se puede hacer o no en función de la secuencialidad, etc.
        """
        tipo = solicitar_tipo_factura(self.wids['ventana'])
        try:
            serie_numerica = tipo.serieNumerica
        except AttributeError:
            pass    # No eligió tipo de factura.
        else:
            numfactura = serie_numerica.get_next_numfactura(commit = True)
            f = pclases.FacturaVenta(numfactura = numfactura, 
                                     serieNumerica = serie_numerica)
            self.ir_a(f)


def solicitar_tipo_factura(ventana_padre = None):
    """
    Devuelve un tipo de facturas de venta o None si se cancela el diálogo.
    """
    opciones = [(t.id, t.nombre) for t in 
                pclases.TipoFactura.select(orderBy = "nombre")]
    id = utils.ui.dialogo_radio(titulo = "TIPO DE FACTURA", 
        texto = "Seleccione un tipo de factura.", 
        ops = opciones, 
        padre = ventana_padre)
    if id:
        res = pclases.TipoFactura.get(id)
    else:
        res = None
    return res 

def solicitar_serie_numerica(ventana_padre = None):
    """
    Devuelve una serie numérica o None si se cancela el diálogo.
    """
    # UNUSED
    anno_en_curso = datetime.date.today().year
    tarifa_defecto = pclases.SerieNumerica.get_serie_defecto(anno_en_curso)
    try:
        valor_defecto = tarifa_defecto.id
    except AttributeError:
        valor_defecto = None
    series = pclases.SerieNumerica.select(pclases.OR(
            pclases.SerieNumerica.q.fechaFin == None, 
            pclases.SerieNumerica.q.fechaFin >= datetime.date.today()), 
        orderBy = "prefijo")
    if valor_defecto and valor_defecto not in opciones:
        opciones.append((tarifa_defecto.id, tarifa_defecto.get_info()))
    opciones = [(s.id, s.get_info()) for s in series]
    id = utils.ui.dialogo_radio(titulo = "SERIE NUMÉRICA", 
        texto = "Seleccione una serie numérica para la factura.", 
        ops = opciones, 
        valor_por_defecto = valor_defecto, 
        padre = ventana_padre)
    if id:
        res = pclases.SerieNumerica.get(id)
    else:
        res = None
    return None


def main():
    from formularios.options_ventana import parse_options
    params, opt_params = parse_options()
    ventana = FacturasVenta(*params, **opt_params) 
    
if __name__ == "__main__":
    main()

