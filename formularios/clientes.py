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
Created on 30/11/2010 

@author: bogado

    Ventana de clientes.

'''

import gtk
from seeker import VentanaGenerica
from framework import pclases
from formularios.graficas import charting
import utils.ui
import datetime
from utils.informes import abrir_pdf

class Clientes(VentanaGenerica): 
    def __init__(self, objeto = None, usuario = None, run = True):
        """
        Constructor. objeto puede ser un objeto de pclases con el que
        comenzar la ventana (en lugar del primero de la tabla, que es
        el que se muestra por defecto).
        """
        self.__clase = pclases.Cliente
        self._objetoreciencreado = None
        if objeto and isinstance(objeto, self.__clase):
            VentanaGenerica.__init__(self, objeto = objeto, usuario = usuario, 
                                     run = False, 
                                     ventana_marco = "clientes.glade")
        elif objeto:
            VentanaGenerica.__init__(self, objeto = objeto, usuario = usuario, 
                                     clase = self.__clase, run = False,
                                     ventana_marco = "clientes.glade")
        else:
            VentanaGenerica.__init__(self, clase = self.__clase, 
                                     usuario = usuario, run = False,
                                     ventana_marco = "clientes.glade")
        b_facturar = gtk.Button(label = "Facturar\npendiente")
        self.wids['b_facturar'] = b_facturar
        b_facturar.connect("clicked", self.facturar_pendiente)
        self.wids['botonera'].pack_start(b_facturar)
        b_facturar.show()
        if run:
            gtk.main()

    def facturar_pendiente(self, boton = None):
        """
        Busca todos los resultados de laboratorio no facturados, los agrupa 
        por mes, crea una factura por cada uno de ellos y obra y las "imprime".
        """
        _resultados = pclases.Resultado.select(
            pclases.Resultado.q.lineaDeVenta == None)
        # Ahora filtro los del cliente y clasifico:
        resultados = {}
        for r in _resultados:
            if r.cliente == self.objeto:
                obra = r.obra
                if obra not in resultados:
                    resultados[obra] = {}
                mes = r.fecha.month
                if mes not in resultados[obra]:
                    resultados[obra][mes] = {}
                ensayo = r.ensayo
                try:
                    resultados[obra][mes][ensayo].append(r)
                except KeyError:
                    resultados[obra][mes][ensayo] = [r]
        if not resultados:
            utils.ui.dialogo_info(titulo = "NADA PENDIENTE", 
                texto = "El cliente no tiene nada pendiente que facturar.", 
                padre = self.wids['ventana'])
        else:
            ver_facturas_en_pantalla = utils.ui.dialogo(
                titulo = "¿VER FACTURAS?", 
                texto = "¿Desea repasar las facturas antes de imprimirlas?", 
                padre = self.wids['ventana'])
        # Genero las facturas... si es que hay resultados.
        for obra in resultados:
            for mes in resultados[obra]:  
                                    # TODO: Debería tener en cuenta el día 
                                    # de pago del cliente para meter en el mes
                                    # siguiente los resultados que se pasaran 
                                    # de esa fecha y generar la factura con 
                                    # esa fecha.
                try:
                    tipo = pclases.TipoFactura.selectBy(nombre="servicios")[0]
                except IndexError:
                    tipo = None
                serie_numerica = obra.cliente.serieNumerica
                fecha = datetime.date.today()
                fdp = obra.formaDePago
                try:
                    retencion = fdp.retencion
                except AttributeError:
                    retencion = 0.0
                numfactura = serie_numerica.get_next_numfactura(commit = True)
                f = pclases.FacturaVenta(
                        tipoFactura = tipo, 
                        obra = obra, 
                        serieNumerica = serie_numerica,  
                        formaDePago = fdp, 
                        numfactura = numfactura, 
                        fecha = fecha, 
                        retencion = retencion, 
                        observaciones = "Factura correspondiente a los "
                            "servicios prestados en el mes de {0}.".format(
                                fecha.strftime("%B"))
                        )

                # ... y las líneas de venta
                for ensayo in resultados[obra][mes]:
                    precio = ensayo.precio
                    cantidad = len(resultados[obra][mes][ensayo])
                    ldv = pclases.LineaDeVenta(
                            producto = None, 
                            facturaVenta = f, 
                            cantidad = cantidad, 
                            precio = precio, 
                            descuento = 0.0, 
                            iva = self.objeto.iva, 
                            descripcion = ensayo.get_info())
                    # Asocio los resultados a la LDV para que se queden 
                    # marcados como facturados:
                    for resultado in resultados[obra][mes][ensayo]:
                        resultado.lineaDeVenta = ldv
                        resultado.syncUpdate()
                # Vencimientos:
                f.crear_vencimientos()
                # Abro las facturas... si quiere el usuario, claro.
                if ver_facturas_en_pantalla:
                    from formularios import facturas_venta
                    v = facturas_venta.FacturasVenta(objeto = f, 
                                                 usuario = self.get_usuario(), 
                                                 run = True)
                else:
                    # ... y las "imprimo":
                    from informes import factura_multipag
                    fpdf = factura_multipag.go_from_facturaVenta(f)
                    abrir_pdf(fpdf)

    
def main():
    from formularios.options_ventana import parse_options
    params, opt_params = parse_options()
    ventana = Clientes(*params, **opt_params) 

if __name__ == "__main__":
    main()

