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
Created on 23/08/2011

@author: bogado

    Clase heredable que construye automáticamente los controles para los 
    formularios de consulta y listado de datos.

'''

NUMERO_ARBITRARIAMENTE_GRANDE = 1000    # Si los resultados a mostrar por el 
    # número de columnas es mayor que esto, el TreeView se actualizará 
    # "off-line", es decir, sin refrescar en pantalla hasta que no se hayan 
    # recuperado todos los datos.
MAX_DATA_GRAFICA = 5    # Número máximo de barras en la gráfica, para evitar 
                        # que quede feote con muchos datos apiñados.

import pygtk
pygtk.require('2.0')
import gtk, gtk.glade 
from ventana import Ventana
from framework import pclases
import utils
from formularios.ventana_progreso import VentanaProgreso
import datetime, os
from gettext import gettext as _
from gettext import bindtextdomain, textdomain
bindtextdomain("cican", 
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "l10n")))
textdomain("cican")

from gobject import TYPE_INT64 as ENTERO
from gobject import TYPE_STRING as CADENA

from ventana_generica import camelize, humanizar, \
                             _abrir_en_ventana_nueva, GALACTUS, \
                             build_widget_valor, labelize
from formularios.graficas import charting


class VentanaConsulta(Ventana):
    """
    Ventana de consulta que se construye dinámicamente dependiendo de la  
    clase donde buscar los resultados.
    """

    def __init__(self, clase = None, objeto = None, usuario = None, 
                 run = True, ventana_marco = 'ventana_consulta.glade', 
                 campos = None, filtros = [], filtros_defecto = {}, 
                 agrupar_por = None):
        """
        Recibe la clase base para construir la ventana.
        Opcionalmente recibe un objeto para mostrar en la misma y 
        el usuario registrado en el sistema.
        Construye la ventana e inicia el bucle Gtk si «run» es True.
        
        @param clase: Clase de pclases. Se puede omitir para obtenerla del 
                      objeto.
        @param objeto: Objeto instanciado de pclases. Se puede omitir si se 
                       especifica «clase». 
        @param usuario: Objeto usuario de la aplicación o None.
        @param run: Si True inicia Gtk. Si no, solo crea la ventana en memoria.
        @param ventana_marco: Ventana glade con los controles a mostrar.
        @param campos: Lista o tupla de campos para construir las columnas del 
                       TreeView de resultados.
        @param filtros Lista de filtros que se insertarán de manera 
                       automática. Deben ser campos (como cadena, igual que 
                       "campos") de la tabla principal. En función del tipo 
                       de campo, se mostrará un tipo de filtro u otro.
        @param filtros_defecto: Diccionario de campos y valores que tomarán 
                                por defecto los filtros de esos campos. Todas 
                                las claves del diccionario deben estar en 
                                la lista de filtros o se ignorarán.
        @param agrupar_por: Campo por el que se agruparán los resultados en 
                            en TreeView o None para verlos "planos".
        """
        # Antes de nada, si me llegan como PUID por haberse invocado desde 
        # línea de comandos o algo, transformo a objetos en memoria:
        if isinstance(clase, str):
            if not clase.startswith("pclases"):
                clase = "pclases.%s" % clase
            clase = eval(clase)
        if hasattr(objeto, "isdigit") and objeto.isdigit():
            objeto = int(objeto)
        if isinstance(objeto, str):
            objeto = pclases.getObjetoPUID(objeto)
        elif isinstance(objeto, int) and clase:
            objeto = clase.get(objeto)
        if isinstance(usuario, str):
            try:
                usuario = pclases.getObjetoPUID(usuario)
            except ValueError:
                if hasattr(usuario, "isdigit") and usuario.isdigit():
                    usuario = pclases.Usuario.selectBy(id = int(usuario))[0]
                else:
                    usuario = pclases.Usuario.selectBy(usuario = usuario)[0]
        elif isinstance(usuario, int):
            usuario = pclases.Usuario.get(usuario)
        # Y ahora sigo con lo mío
        if not clase and not objeto:
            raise ValueError, _("Debe pasar al menos la clase o un objeto.")
        self.__usuario = usuario
        if isinstance(clase, pclases.SQLObject):
            #print "AHORA SHIIIII!" 
            clase, objeto = None, clase
        if not clase:
            self.clase = objeto.__class__
        else:
            if isinstance(clase, str):
                clase = getattr(pclases, clase)
            self.clase = clase
        self.objeto = objeto
        self.resultados = pclases.SQLtuple(())
        Ventana.__init__(self, ventana_marco, objeto, usuario)
        self.columnas = campos
        self.filtros = filtros
        self.filtros_defecto = filtros_defecto
        self.agrupar_por = agrupar_por
        self.inicializar_ventana()
        titulo_ventana = self.wids['ventana'].get_title()
        if (not titulo_ventana or titulo_ventana.strip() == "" 
            or titulo_ventana == "Oh, the humanity!"):
            self.wids['ventana'].set_title(self.clase.__name__)
        # Botones genéricos:
        connections = {'b_salir/clicked': self.salir, 
                       'b_actualizar/clicked': self.actualizar_ventana, 
                       'b_exportar/clicked': self.exportar, 
                       'b_imprimir/clicked': self.imprimir, 
                       'b_fini/clicked': self.set_fecha_ini, 
                       'b_ffin/clicked': self.set_fecha_fin, 
                       'e_fini/focus-out-event': self.show_fecha, 
                       'e_ffin/focus-out-event': self.show_fecha, 
                      }
        try:
            self.wids['e_fini'].set_text("")
        except KeyError:    # No tiene filtros de fecha
            connections.pop("e_fini/focus-out-event")
            connections.pop("b_fini/clicked")
        #self.wids['e_ffin'].set_text(
        #    utils.fecha.str_fecha(datetime.date.today()))
        try:
            self.wids['e_ffin'].set_text("")
        except KeyError:    # No tiene filtros de fecha
            connections.pop("e_ffin/focus-out-event")
            connections.pop("b_ffin/clicked")
        self.add_connections(connections)
        self._funcs_actualizacion_extra = []    # Lista de funciones que se 
            # llamarán cuando se actualice la ventana.
        if run:
            gtk.main()

    def set_fecha_ini(self, boton):
        utils.ui.set_fecha(self.wids['e_fini'])

    def set_fecha_fin(self, boton):
        utils.ui.set_fecha(self.wids['e_ffin'])

    def show_fecha(self, entry, event):
        """
        Muestra la fecha en modo texto después de parsearla.
        """
        if entry.get_text():
            try:
                entry.set_text(utils.fecha.str_fecha(utils.fecha.parse_fecha(
                    entry.get_text())))
            except (ValueError, TypeError):
                entry.set_text(utils.fecha.str_fecha(datetime.date.today()))

    def get_usuario(self):
        return self.__usuario

    # Funciones estándar "de facto":
    def actualizar_ventana(self, boton = None):
        cursor_reloj = gtk.gdk.Cursor(gtk.gdk.WATCH)
        self.wids['ventana'].window.set_cursor(cursor_reloj)
        utils.ui.set_unset_urgency_hint(self.wids['ventana'], False)
        while gtk.events_pending(): gtk.main_iteration(False)
        self.rellenar_widgets()
        self.wids['ventana'].window.set_cursor(None)

    def inicializar_ventana(self):
        """
        Inicializa los controles de la ventana, construyendo 
        los modelos para los TreeView, etc.
        Si se recibe «columnas», que sea una lista de nombres de columnas en 
        el orden en que se deben mostrar en la ventana; tanto de columnas 
        normales como de relaciones (claves ajenas y múltiples).
        """
        if self.columnas is None:
            self.columnas = [c.name for c in self.clase.sqlmeta.columnList]
        cols = []
        # Nombre, tipo de datos, editable, ordenable, buscable, func. edición.
        for nombre_col in self.columnas:
            sqlcol = self.clase.search_col_by_name(nombre_col)
            tipo_gobject = utils.ui.sqltype2gobject(sqlcol)
            col=(labelize(nombre_col), tipo_gobject, False, True, False, None)
            cols.append(col)
        cols.append(("PUID", "gobject.TYPE_STRING", False, False, False, None))
        try:
            tv = self.wids['tv_datos']
        except KeyError:
            tv = None # No es "estándar" y tiene su propio TreeView
        if tv:
            utils.ui.preparar_treeview(tv, cols)
            tv.connect("row-activated", _abrir_en_ventana_nueva, 
                       self.__usuario, GALACTUS, None, self.clase)
            self.build_totales()
            self.build_filtros()
            self.build_agrupar_por()
            self.build_widget_grafico()
        try:
            self.wids['label_notas'].set_text("\nIntroduzca filtro en la "
                "parte superior y pulse actualizar.\n")
        except KeyError:
            pass    # Tampoco tiene label...
    
    def build_widget_grafico(self):
        try:
            wgrafica = self.wids['grafica']
        except KeyError:    # Efectivamente, no está creada.
            self.wids['grafica'] = gtk.Alignment(0.5, 0.5, 0.9, 0.9)
            self.wids['grafica'].set_property("visible", True)
            self.wids['eventbox_chart'].add(self.wids['grafica']) 
            self.grafica = charting.Chart(value_format = "%.1f",
                                          #max_bar_width = 20,
                                          #legend_width = 70,
                                          interactive = False)
            self.wids['grafica'].add(self.grafica)
            self.wids['eventbox_chart'].show_all()

    def actualizar_grafica(self, keys, data):
        """
        Actualiza (o crea) la gráfica contenida en el eventbox de la ventana.
        """
        try:
            self.grafica.plot(keys, data)
        except AttributeError: # Todavía no se ha creado el widget.
            self.build_widget_grafico()
            self.grafica.plot(keys, data)

    def build_agrupar_por(self):
        """
        Construye un combo para agrupar por algún campo en concreto. Toma por 
        defecto el valor pasado al constructor.
        """
        c = self.wids['vbox_filtros']
        cb_agrupar_por = gtk.ComboBox()
        self.wids['cb_agrupar_por'] = cb_agrupar_por
        utils.ui.rellenar_lista(cb_agrupar_por, 
            enumerate([labelize(i) for i in self.columnas]))
        if self.agrupar_por:    # Valor por defecto
            for i, col in enumerate(self.columnas):
                if col == self.agrupar_por:
                    utils.ui.combo_set_from_db(self.wids['cb_agrupar_por'], i)
        cb_agrupar_por.connect("changed", self.__store_agrupar)
        box_agrupar = gtk.HBox()
        box_agrupar.pack_start(gtk.Label("Agrupar resultados por"))
        box_agrupar.pack_start(cb_agrupar_por)
        box_agrupar.show_all()
        c.add(box_agrupar)

    def __store_agrupar(self, combo):
        indice = utils.ui.combo_get_value(combo)
        self.agrupar_por = self.columnas[indice]
        # No merece la pena actualizar. Que lo haga el usuario.

    def build_filtros(self):
        c = self.wids['vbox_filtros']
        for campo in self.filtros:
            sqlcampo = self.clase.sqlmeta.columns[campo]
            wfiltro, contenedor = build_filtro(sqlcampo)
            inner = gtk.HBox()
            inner.add(gtk.Label(labelize(campo)))
            try:
                inner.add(contenedor)
            except TypeError:   # No lleva contenedor
                inner.add(wfiltro)
            self.wids[wfiltro.name] = wfiltro
            try:    # Valor por defecto para el filtro
                escribir_valor(sqlcampo, 
                               self.filtros_defecto[wfiltro.name], 
                               self.wids[wfiltro.name])
            except KeyError:    # No hay valor para el filtro
                pass
            c.add(inner)
        c.show_all()

    def activar_widgets(self, activo = True):
        """
        Activa o desactiva los widgets de la ventana que 
        dependan del objeto mostrado (generalmente todos 
        excepto el botón de nuevo, salir y buscar).
        """
        pass

    def es_diferente(self):
        """
        Devuelve True si algún valor en ventana difiere de 
        los del objeto.
        """
        return False
    
    def rellenar_widgets(self):
        """
        Muestra los valores de cada atributo en el widget
        del campo correspondiente.
        """
        try:
            fechaini = self.wids['e_fini'].get_text().strip()
        except KeyError:    # No es una ventana de consulta "estándar".
            return
        if fechaini:
            try:
                fechaini = utils.fecha.parse_fecha(fechaini)
            except (ValueError, TypeError):
                utils.dialogo_info(titulo = "ERROR EN FECHA INICIAL", 
                 texto = "El texto «%s» no es una fecha correcta." % fechaini,
                 padre = self.wids['ventana'])
                fechaini = None
        fechafin = self.wids['e_ffin'].get_text().strip()
        if fechafin:
            try:
                fechafin = utils.fecha.parse_fecha(fechafin)
            except (ValueError, TypeError):
                utils.ui.dialogo_info(titulo = "ERROR EN FECHA FINAL", 
                 texto = "El texto «%s» no es una fecha correcta." % fechafin,
                 padre = self.wids['ventana'])
                fechafin = None
        if fechaini and fechafin and fechafin < fechaini:
            fechaini, fechafin = fechafin, fechaini
            self.wids['e_fini'].set_text(utils.fecha.str_fecha(fechaini))
            self.wids['e_ffin'].set_text(utils.fecha.str_fecha(fechafin))
        criterios = []
        try:
            campofecha = getattr(self.clase.q, 
                                 buscar_campos_fecha(self.clase)[0].name)
        except IndexError:
            pass    # No puedo filtrar por fecha.
        else:
            if fechaini:
                criterios.append(campofecha >= fechaini)
            if fechafin:
                criterios.append(campofecha <= fechafin)
        # Más filtros:
        # PLAN: No es demasiado útil tal y como está ahora. Debería permitir 
        # definir rangos y operadores >=, <>, etc.
        for filtro in self.filtros:
            sqlcolumn = self.clase.sqlmeta.columns[filtro]
            valor = leer_valor(sqlcolumn, 
                               self.wids[filtro])
            if isinstance(sqlcolumn, pclases.SOForeignKey) and valor == -1:
                criterios.append(getattr(self.clase.q, filtro) == None)
            elif valor:   # Si no especifica, es que no lo quiere usar. ¿No?
                criterios.append(getattr(self.clase.q, filtro) == valor)
        self.resultados = self.clase.select(pclases.AND(*criterios))
        self.rellenar_resultados()
        try:
            self.actualizar_total(self.wids['cb_total_totalizador'], 
                                  self.wids['e_total_totalizador'])
        except KeyError:
            pass    # No hay totalizador.

    def rellenar_resultados(self):
        vpro = VentanaProgreso(padre = self.wids['ventana'])
        txtpro = self.clase.__name__
        vpro.set_valor(0.0, txtpro)
        vpro.mostrar()
        model = self.wids['tv_datos'].get_model()
        try:
            tot = len(self.resultados)
        except TypeError:
            tot = self.resultados.count()
        if tot*len(self.columnas) > NUMERO_ARBITRARIAMENTE_GRANDE:
            self.wids['tv_datos'].freeze_child_notify()
            self.wids['tv_datos'].set_model(None)
        model.clear()
        i = 0.0
        padres = {}
        for registro in self.resultados:
            vpro.set_valor(i / tot, "[%d/%d] %s (%s)" % (
                i, tot, txtpro, registro.get_puid()))
            i += 1
            fila = []
            for columna in self.columnas:
                valor = getattr(registro, columna)
                valor = humanizar(valor, registro.sqlmeta.columns[columna])
                fila.append(valor)
            fila.append(registro.get_puid())
            if not self.agrupar_por:
                model.append(None, (fila))  # Es un treeview plano que usaré 
                                # como listview. Por eso el nodo padre es None.
            else:
                try:
                    padre = padres[getattr(registro, self.agrupar_por)]
                except KeyError:    # Primera vez que aparece este padre.
                    valor_cabecera = getattr(registro, self.agrupar_por)
                    puid = None
                    if isinstance(self.clase.sqlmeta.columns[self.agrupar_por],
                                  pclases.SOForeignKey):
                        valor_cabecera = getattr(registro, 
                            self.agrupar_por.replace("ID", ""))   # CHAPU
                        try:
                            puid = valor_cabecera.get_puid()
                            valor_cabecera = valor_cabecera.get_info()
                        except AttributeError:  # Es None
                            valor_cabecera = "Sin %s" % (
                                labelize(self.agrupar_por))
                            puid = None
                    fila_padre = [valor_cabecera]
                    for i in range(len(self.columnas) - 1):
                        fila_padre.append("")
                    fila_padre.append(puid)
                    padre = padres[getattr(registro, self.agrupar_por)] \
                        = model.append(None, (fila_padre))
                model.append(padre, (fila))
                # Actualizo totales numéricos del padre:
                ncell = 0
                for columna in self.columnas:
                    valor_hijo_columna = getattr(registro, columna)
                    sqlcolumna = registro.sqlmeta.columns[columna]
                    if (isinstance(valor_hijo_columna, (int, float)) and 
                        not isinstance(sqlcolumna, pclases.SOForeignKey)):
                        try:
                            nuevo_valor_padre = utils.numero._float(
                                model[padre][ncell]) 
                        except ValueError:
                            nuevo_valor_padre = 0
                        nuevo_valor_padre += valor_hijo_columna
                        nuevo_valor_padre = utils.numero.float2str(
                            nuevo_valor_padre)
                        model[padre][ncell] = nuevo_valor_padre
                    ncell += 1
        self.actualizar_totales()
        if tot*len(self.columnas) > NUMERO_ARBITRARIAMENTE_GRANDE:
            self.wids['tv_datos'].set_model(model)
            self.wids['tv_datos'].thaw_child_notify()
        vpro.ocultar()

    def actualizar_totales(self):
        """
        Actualiza el grid de totales.
        """
        self.wids['e_total_total'].set_text(str(self.clase.select().count()))
        self.wids['e_total_listed'].set_text(str(self.resultados.count()))

    def buscar(self, boton):
        """
        Pide un texto a buscar y hace activo el resultado 
        de la búsqueda.
        """
        pass

    def build_totales(self):
        """
        Crea el grid de totales y añade un combo para seleccionar la columna 
        de valores sobre la que hacer el sumatorio.
        """
        gt = self.wids['grid_totales']
        self.wids['e_total_total'] = gtk.Entry()
        self.wids['e_total_listed'] = gtk.Entry()
        filas = [("Número de elementos totales: ", self.wids['e_total_total']), 
                 ("Número de elementos listados", self.wids['e_total_listed'])]
        filas.append(self.build_totalizador())
        numfila = 0
        for etiqueta, entry in filas:
            if etiqueta and entry:
                numfila += 1
                gt.resize(numfila, 2)
                if isinstance(etiqueta, str):
                    label = gtk.Label(etiqueta)
                else:
                    label = etiqueta    # Debe ser el combo del toal.
                gt.attach(label, 0, 1, numfila - 1, numfila)
                entry.set_property("editable", False)
                entry.set_property("has-frame", False)
                entry.set_alignment(1.0)
                gt.attach(entry, 1, 2, numfila - 1, numfila)
        gt.show_all()

    def build_totalizador(self):
        """
        Devuelve un ComboBox y un Entry no editable. El ComboBox 
        tiene asociado al evento «changed» una función que hace un sumatorio 
        de la columna seleccionada en el mismo y lo escribe en el entry.
        En el Combo solo estarán las columnas de tipo Float o Int. No tiene 
        sentido sumar textos.
        """
        # TODO: PLAN: Hacer los totales también con horas 
        # (datetime.timedelta = SOTimeCol, creo porque los TimestampCol son 
        # fechas con hora).
        clases_numericas = (pclases.SOBigIntCol, pclases.SOCurrencyCol, 
                            pclases.SODecimalCol, pclases.SOFloatCol, 
                            pclases.SOIntCol, pclases.SOMediumIntCol, 
                            pclases.SOSmallIntCol, pclases.SOTinyIntCol) 
        nombres_colsnumericas = []
        for col in self.columnas:
            for clase_numerica in clases_numericas:
                sqlcol = self.clase.sqlmeta.columns[col]
                if isinstance(sqlcol, clase_numerica):
                    nombres_colsnumericas.append(col)
        if nombres_colsnumericas:
            nombres_colsnumericas.sort()
            combo_total = gtk.combo_box_new_text()
            for nombrecol in nombres_colsnumericas:
                combo_total.append_text(nombrecol)
            entry_total = gtk.Entry()
            entry_total.set_has_frame(False)
            entry_total.set_editable(False)
            combo_total.connect("changed", self.actualizar_total, 
                                entry_total)
            totalizador = gtk.HBox()
            labeler = gtk.Label("Totalizar ")
            labeler.set_alignment(1.0, labeler.get_alignment()[1])
            totalizador.pack_start(labeler)
            not_expansor = gtk.VBox()
            not_expansor.pack_start(combo_total, fill = False)
            totalizador.pack_start(not_expansor)
            #totalizador.pack_start(entry_total)
            entry_total.set_property("name", 
                                     "e_total_totalizador")
            self.wids[entry_total.name] = entry_total
            combo_total.set_property("name", 
                                     "cb_total_totalizador")
            self.wids[combo_total.name] = combo_total
            labeler.set_property("name", "l_total_totalizador")
            self.wids[labeler.name] = labeler
            totalizador.set_property("name", 
                                     "totalizador_container")
            self.wids[totalizador.name] = totalizador
        else:
            totalizador = entry_total = None
        return totalizador, entry_total
    
    def actualizar_total(self, combo, e_total):
        """
        Actualiza el TreeView indicado usando el nombre de columna marcado en 
        el combo para hacer la suma.
        """
        coltotal = combo.get_active_text()
        if coltotal:    # Se ha seleccionado campo para sumatorio.
            total = sum([getattr(i, coltotal) for i in self.resultados])
            self.wids['e_total_totalizador'].set_text(str(total))
            # Tremendo momento gráfica:
            data = {}
            for r in self.resultados:
                data[r.get_info()] = getattr(r, coltotal)
            #keys = sorted(data.keys(), key = lambda x: x[0])
            #values = [data[key] for key in keys]
            # Ordeno por valores, mejor:
            import operator
            keys = []
            values = []
            sorted_by_value = sorted(data.iteritems(), 
                                     key = operator.itemgetter(1), 
                                     reverse = True)
            for k, v in sorted_by_value:
                keys.append(k)
                values.append(v)
            if len(keys) > MAX_DATA_GRAFICA:
                resto = sum(values[MAX_DATA_GRAFICA:])
                keys = keys[:MAX_DATA_GRAFICA]
                keys.append("Resto")
                values = values[:MAX_DATA_GRAFICA]
                values.append(resto)
            self.actualizar_grafica(keys, values)
 
    def exportar(self, boton):
        """
        Exporta el contenido del TreeView a un CSV
        """
        try:
            tv = self.wids['tv_datos']
        except KeyError:
            return  # No es ventana estándar. Quien me herede, que redefina.
        from utils.treeview2csv import treeview2csv
        from utils.informes import abrir_csv
        abrir_csv(treeview2csv(tv))

    def imprimir(self, boton):
        """
        Genera un PDF con los datos en pantalla.
        """
        try:
            tv = self.wids['tv_datos']
        except KeyError:
            return  # No es ventana estándar. Quien me herede, que redefina.
        titulo = self.wids['ventana'].get_title()
        from utils.treeview2pdf import treeview2pdf
        from utils.informes import abrir_pdf
        strfini = self.wids['e_fini'].get_text()
        strffin = self.wids['e_ffin'].get_text()
        if strfini and strfin:
            strfecha = "%s - %s" % (strfini, strffin)
        elif not strfini and strffin:
            strfecha = "Hasta %s" % (strffin)
        elif strfini and not strffin:
            strfecha = "Desde %s" % (strfini)
        else:
            strfecha = None
        nomarchivo = treeview2pdf(tv, 
            titulo = titulo,
            fecha = strfecha)
        abrir_pdf(nomarchivo)


def buscar_campos_fecha(clase):
    """
    Busca y devielve los campos de fecha de la clase.
    @param clase: Clase de pclases.
    """
    res = []
    for c in clase.sqlmeta.columnList:
        if isinstance(c, (pclases.SODateCol, pclases.SODateTimeCol)):
            res.append(c)
    return res

def build_filtro(sqlcampo):
    wvalor, contenedor = build_widget_valor(sqlcampo, sqlcampo.name, 
                                            let_edit = False, 
                                            let_create = False) 
    # Ahora, si es una FK, tengo que dejar que ponga "Todos" o "Ninguno" y 
    # tratarlo después convenientemente.
    if isinstance(sqlcampo, pclases.SOForeignKey):
        model = wvalor.get_model()
        model.insert(0, (0, "Todos"))
        model.insert(1, (-1, "Ninguno"))
    return wvalor, contenedor

def leer_valor(col, widget):
    """
    Lee el valor de la ventana correspondiente al campo 
    "col" y lo trata convenientemente (p.e. convirtiéndolo 
    a float si el tipo de la columna es SOFloatCol) antes 
    de devolverlo.
    Lanza una excepción si ocurre algún error de conversión.
    """
    if isinstance(col, pclases.SOStringCol): 
        try:
            valor = widget.get_text()
        except AttributeError:      # Puede ser un TextView
            buffer = widget.get_buffer()
            valor = buffer.get_text(buffer.get_start_iter(), 
                                    buffer.get_end_iter())
    elif isinstance(col, pclases.SOIntCol):
        if isinstance(widget, gtk.SpinButton):
            valor = widget.get_value()
            valor = int(valor)
        else:
            valor = widget.get_text()
            valor = utils.numero.parse_formula(valor, int)
            try:
                valor = int(valor)
            except Exception, e:
                if pclases.DEBUG and pclases.VERBOSE:
                    ttt = "ventana_consulta::leer_valor -> "\
                          "Excepción {0} capturada "\
                          "al convertir «{1}» a entero."\
                          " Devuelvo None.".format(e, valor)
                    print ttt
                # raise e
                valor = None
    elif isinstance(col, pclases.SOFloatCol):
        valor = widget.get_text()
        valor = utils.numero.parse_formula(valor, int)
        try:
            valor = utils.numero._float(valor)
        except Exception, e:
            # Intento leerlo como euro
            try:
                valor = utils.numero.parse_euro(valor)
            except Exception, e:
                # Intento leerlo como porcentaje
                try:
                    valor = utils.numero.parse_porcentaje(valor)
                except Exception, e:
                    if pclases.DEBUG and pclases.VERBOSE:
                        ttt = "ventana_consulta::leer_valor -> "\
                              "Excepción {0} "\
                              "capturada al convertir «{1}» a flotante. "\
                              "Devuelvo None.".format(e, valor)
                        print ttt
                    #raise e
                    valor = None
    elif isinstance(col, pclases.SOBoolCol):
        valor = widget.get_active()
    elif isinstance(col, pclases.SODateCol):
        valor = widget.get_text()
        try:
            valor = utils.fecha.parse_fecha(valor)
        except Exception, e:
            if pclases.DEBUG and pclases.VERBOSE:
                ttt = "ventana_consulta::leer_valor -> Excepción %s "\
                      "capturada al convertir «%s» a fecha. "\
                      "Devuelvo None." % (e, valor)
                print ttt
            #raise e
            valor = None
    elif isinstance(col, pclases.SOForeignKey):
        valor = utils.ui.combo_get_value(widget)
    else:
        # Lo intento como puedo. A lo mejor faltaría intentarlo también 
        # como si fuera un TextView.
        if hasattr(widget, "child"):
            valor = widget.child.get_text()
        else:
            valor = widget.get_text()
    return valor

def escribir_valor(col, valor, widget):
    """
    Muestra el valor "valor" en el widget correspondiente 
    al campo "col", haciendo las transformaciones necesarias
    dependiendo del tipo de datos.
    El criterio para los valores nulos (NULL en la BD y None en Python) 
    es usar la cadena vacía para representarlos en pantalla y -1 en el caso 
    de las claves ajenas.
    """
    if isinstance(col, pclases.SOStringCol):
        if valor is None:
            valor = ""  # Prefiero que muestre la cadena vacía y que 
                        # el usuario guarde ese valor en lugar de None si 
                        # quiere.
        try:
            widget.set_text(valor)
        except AttributeError:  # Puede ser un TextView
            widget.get_buffer().set_text(valor)
        except TypeError:
            terr = "ventana_generica::escribir_valor -> El valor «%s» "\
                   "no es válido."
            raise TypeError, terr
    elif isinstance(col, pclases.SOIntCol):
        if isinstance(widget, gtk.SpinButton):
            widget.set_value(valor)
        else:
            try:
                if valor != None:
                    valor = str(valor)
                else:
                    valor = ""
            except Exception, e:
                if pclases.DEBUG:
                    print "Excepción %s capturada al convertir %s de "\
                          "entero a cadena." % (e, valor)
                raise e
            widget.set_text(valor)
    elif isinstance(col, pclases.SOFloatCol):
        try:
            # precision = 6 es por las coordenadas (lat, lon) GPS
            valor = utils.numero.float2str(valor, precision = 6, 
                                           autodec = True)
        except Exception, e:
            if pclases.DEBUG and pclases.VERBOSE:
                terr = "Excepción %s capturada al convertir «%s» de"\
                       " flotante a cadena." % (e, valor) 
                print terr
            #raise e
            valor = ''
        widget.set_text(valor)
    elif isinstance(col, pclases.SOBoolCol):
        widget.set_active(valor)
    elif isinstance(col, pclases.SODateCol):
        try:
            valor = utils.fecha.str_fecha(valor)
        except Exception, e:
            if pclases.DEBUG and pclases.VERBOSE:
                txterr =  "Excepción %s capturada al convertir «%s» "\
                          "de fecha a cadena." % (e, valor)
                print txterr
            #raise e
            valor = ""
        widget.set_text(valor)
    elif isinstance(col, pclases.SOForeignKey):
        utils.ui.combo_set_from_db(widget, valor)
    else:
        # Lo intento como puedo. A lo mejor faltaría intentarlo también 
        # como si fuera un TextView.
        if hasattr(widget, "child"):
            widget.child.set_text(`valor`)
        else:
            widget.set_text(`valor`)


if __name__ == "__main__":
    import sys
    try:
        glade = sys.argv[2]
    except IndexError:
        glade = "ventana_consulta.glade"
    if not glade.endswith(".glade"):
        glade += ".glade"
    try:
        clase = sys.argv[1]
    except IndexError:
        clase = camelize(glade.replace(".glade", "").title())
    VentanaConsulta(clase = clase, run = True, ventana_marco = glade, 
                    filtros = ["iva", "serieNumericaID"])

