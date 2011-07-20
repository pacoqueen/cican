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
Created on 20/05/2010

@author: bogado

    Clase heredable que construye automáticamente los controles para los 
    formularios CRUD.

'''

GALACTUS = lambda *args, **kw: None

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

(FORMATO_DESPLEGABLES_COMPLETO, 
 FORMATO_DESPLEGABLES_GETINFO, 
 FORMATO_DESPLEGABLES_PRIMERACOL) = range(3)

from gobject import TYPE_INT64 as ENTERO
from gobject import TYPE_STRING as CADENA

class VentanaGenerica(Ventana):
    """
    Ventana genérica que se construye dinámicamente dependiendo del 
    objeto que mostrará.
    """

    def __init__(self, clase = None, objeto = None, usuario = None, 
                 run = True, ventana_marco = 'ventana_generica.glade', 
                 campos = None):
        """
        Recibe la clase base para construir la ventana.
        Opcionalmente recibe un objeto para mostrar en la misma y 
        el usuario registrado en el sistema.
        Construye la ventana e inicia el bucle Gtk si «run» es True.
        
        @param clase: Clase de pclases. Se puede omitir para obtenerla del 
                      objeto.
        @param objeto: Objeto instanciado de pclases. Se puede omitir si se 
                       especifica «clase». En ese caso se mostrará en ventana 
                       el primero resultado de la consulta select sobre la 
                       clase.
        @param usuario: Objeto usuario de la aplicación o None.
        @param run: Si True inicia Gtk. Si no, solo crea la ventana en memoria.
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
            self.clase = clase
        self.objeto = objeto
        static_glade = overrides_glade(self.clase)
        if static_glade:
            ventana_marco = static_glade
        Ventana.__init__(self, ventana_marco, objeto, usuario)
        self.inicializar_ventana(campos)
        self.wids['ventana'].set_title(self.clase.__name__)
        # Botones genéricos:
        connections = {'b_salir/clicked': self.salir, 
                       'b_actualizar/clicked': self.actualizar_ventana, 
                       'b_nuevo/clicked': self.nuevo, 
                       'b_borrar/clicked': self.borrar, 
                       'b_buscar/clicked': self.buscar, 
                       'b_guardar/clicked': self.guardar
                      }
        self.add_connections(connections)
        self._funcs_actualizacion_extra = []    # Lista de funciones que se 
            # llamarán cuando se actualice la ventana.
        if self.objeto == None:
            self.ir_a_primero()
        else:
            self.ir_a(self.objeto)
        if run:
            gtk.main()

    def get_usuario(self):
        return self.__usuario

    # Funciones estándar "de facto":
    def inicializar_ventana(self, columnas = None):
        """
        Inicializa los controles de la ventana, construyendo 
        los modelos para los TreeView, etc.
        Si se recibe «columnas», que sea una lista de nombres de columnas en 
        el orden en que se deben mostrar en la ventana; tanto de columnas 
        normales como de relaciones (claves ajenas y múltiples).
        """
        self.campos_widgets = {}    # ¿Qué campo corresponde a cada widget?
        self.widgets_campos = {}    # ¿Qué widget corresponde a cada campo?
        if columnas is None:    # Enséñamelo todo, nena. Grñai mama
            columnas = self.clase.sqlmeta.columns.keys()
            columnas += [j.joinMethodName for j in self.clase.sqlmeta.joins]
        if pclases.DEBUG:
            print columnas
        for colname in columnas:
            try:
                col = self.clase.sqlmeta.columns[colname]
            except KeyError:    # Soy clave ajena de alguien.
                continue        # Este TreeView se montará después. No aquí.
            contenedor, widget = build_widget(col, ventana = self, 
                                              usuario = self.__usuario)
            self.wids[col.name] = widget
            self.wids["container_" + col.name] = contenedor
            if not contenedor.parent:
                self.wids['vbox'].add(contenedor)
            self.campos_widgets[widget] = colname
            self.widgets_campos[colname] = widget
        for col in self.clase.sqlmeta.joins:
            if col.joinMethodName not in columnas:
                continue
            contenedor, widget = self.build_listview(col)
            self.wids[col.joinMethodName] = widget
            self.wids["container_" + col.joinMethodName] = contenedor
            self.wids['vboxrelaciones'].add(contenedor)
        # Oculto la pestaña si no va a contener nada:
        if not self.clase.sqlmeta.joins:
            pagina_relaciones = self.wids['notebook'].get_nth_page(1)
            pagina_relaciones.set_property("visible", False)
        self.wids['vbox'].show_all()
        self.wids['b_actualizar'].set_sensitive(False)
        self.wids['b_guardar'].set_sensitive(False)
        self.wids['ventana'].set_title(self.clase.__name__)
        self.refocus_enter()

    def activar_widgets(self, activo = True):
        """
        Activa o desactiva los widgets de la ventana que 
        dependan del objeto mostrado (generalmente todos 
        excepto el botón de nuevo, salir y buscar).
        """
        if self.__usuario and self.__usuario.nivel >= 2:
            activo = False
        if self.objeto == None:
            activo = False
        excepciones = ["b_nuevo", "b_salir", "b_buscar"] #, "ventana"] # La 
            # ventana siempre, SIEMPRE, debe estar activa para poder recibir 
            # combinaciones de teclas y demás.
        _excepciones = set()
        while excepciones:
            wex = excepciones.pop()
            try:
                padre = self.wids[wex].parent
            except TypeError, e:
                txterr = "ventana_generica::activar_widgets -> "\
                         "¿Widget «%s» no existe? Excepción: %s" % (wex, e)
                print txterr
                sys.exit(_("Error en VentanaGenerica activando widgets."))
            if padre != None:
            #while padre != None:
                nombre_padre = padre.name
                excepciones.append(nombre_padre)
                #padre = padre.parent
                _excepciones.add(nombre_padre)
                _excepciones.add(wex)
        excepciones = tuple(_excepciones)
        for w in self.wids.keys():
            if (w != 'b_actualizar' and w != 'b_guardar' 
                and not w.startswith("b_undo_") # Botones deshacer.
                and not w.startswith("b_save_") # Botones guardar local.
                and w not in excepciones):
                self.wids[w].set_sensitive(activo)

    def es_diferente(self):
        """
        Devuelve True si algún valor en ventana difiere de 
        los del objeto.
        """
        if self.objeto == None:
            igual = True
        else:
            igual = self.objeto != None
            for colname in self.clase.sqlmeta.columns:
                col = self.clase.sqlmeta.columns[colname]
                valor_ventana = self.leer_valor(col)
                valor_objeto = getattr(self.objeto, col.name)
                este_campo_igual = valor_ventana == valor_objeto
                igual = igual and este_campo_igual
                if not este_campo_igual:
                    if pclases.DEBUG:
                        txtventana = "ventana_generica::es_diferente -> "\
                                     "[%s] Valor ventana: %s" % (colname, 
                                                                 valor_ventana)
                        txtobjeto = "ventana_generica::es_diferente -> "\
                                    "[%s] Valor objeto:%s" % (colname, 
                                                              valor_objeto)
                        print txtventana 
                        print txtobjeto 
                    self.destacar_widget(colname)
                else:
                    self.destacar_widget(colname, None, None)
        return not igual
    
    def destacar_widget(self, campo, color_bg = "IndianRed1", 
                                     color_base = "Orange"):
        """
        Resalta en otro color el widget correspondiente al campo recibido 
        como cadena.
        Si el botón actualizar está activo, resalta el marco. Si no, resalta 
        el fondo.
        Si los dos colores recibidos son None, limpia tanto el marco como el 
        fondo.
        """
        widget = self.widgets_campos[campo]
        if hasattr(widget, "child") and isinstance(widget.child, gtk.Entry):
            widget = widget.child   # Es un combo. Resalto el entry interno.
        if color_bg is None and color_base is None:
            widget.modify_bg(gtk.STATE_NORMAL, color_bg)
            widget.modify_base(gtk.STATE_NORMAL, color_bg)
        else:
            if self.wids['b_actualizar'].get_property("sensitive"):
                if not (isinstance(color_bg, gtk.gdk.Colormap) 
                        or color_bg is None):
                    color_bg = widget.get_colormap().alloc_color(color_bg)
                widget.modify_bg(gtk.STATE_NORMAL, color_bg)
            else:
                if not (isinstance(color_base, gtk.gdk.Colormap)
                        or color_base is None):
                    color_base = widget.get_colormap().alloc_color(color_base)
                widget.modify_base(gtk.STATE_NORMAL, color_base)

    def leer_valor(self, col, nombre_widget = None):
        """
        Lee el valor de la ventana correspondiente al campo 
        "col" y lo trata convenientemente (p.e. convirtiéndolo 
        a float si el tipo de la columna es SOFloatCol) antes 
        de devolverlo.
        Lanza una excepción si ocurre algún error de conversión.
        """
        if nombre_widget == None:
            nombre_widget = col.name
        widget = self.wids[nombre_widget]

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
                        ttt = "ventana_generica::leer_valor -> "\
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
                            ttt = "ventana_generica::leer_valor -> "\
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
                    ttt = "ventana_generica::leer_valor -> Excepción %s "\
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
    
    def rellenar_widgets(self):
        """
        Muestra los valores de cada atributo en el widget
        del campo correspondiente.
        """
        for f, args, kw in self._funcs_actualizacion_extra:
            f(*args, **kw)
        if self.objeto != None:
            for colname in self.clase.sqlmeta.columns:
                col = self.clase.sqlmeta.columns[colname]
                valor_objeto = getattr(self.objeto, col.name)
                self.escribir_valor(col, valor_objeto)
                widget = self.widgets_campos[colname]
                widget.modify_bg(gtk.STATE_NORMAL, None)
                widget.modify_base(gtk.STATE_NORMAL, None)
                    # Por si está en rojo desde el es_diferente.
                try:
                    b_undo = self.wids['b_undo_' + col.name]
                except KeyError:    # No hay botón de deshacer
                    pass
                else:
                    b_undo.set_sensitive(False)
                try:
                    b_save = self.wids['b_save_' + col.name]
                except KeyError:    # No hay botón de guardar el campo
                    pass
                else:
                    b_save.set_sensitive(False)
            for col in self.clase.sqlmeta.joins:
                self.rellenar_tabla(col)
            self.wids['ventana'].set_title("<%s [%d]>\t%s" % (
                self.clase.__name__, 
                self.objeto.id, 
                self.objeto.get_info())) 

    def escribir_valor(self, col, valor = None, nombre_widget = None):
        """
        Muestra el valor "valor" en el widget correspondiente 
        al campo "col", haciendo las transformaciones necesarias
        dependiendo del tipo de datos.
        Si el valor se omite, lo rescata del objeto. 
        El criterio para los valores nulos (NULL en la BD y None en Python) 
        es usar la cadena vacía para representarlos en pantalla. 
        """
        if nombre_widget == None:
            nombre_widget = col.name
        widget = self.wids[nombre_widget]
        if valor == None:
            valor = getattr(self.objeto, col.name)
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

    def ir_a_primero(self, invertir = True):
        """
        Hace activo el primer objeto de la clase si "invertir" es False.
        Si es True (valor por defecto), el activo es el último objeto 
        creado en la tabla.
        """
        anterior = self.objeto
        try:
            if invertir:
                objeto = self.clase.select(orderBy = "-id")[0]
            else:
                objeto = self.clase.select(orderBy = "id")[0]
            # Anulo el aviso de actualización del objeto que deja de ser 
            # activo.
            if self.objeto != None: self.objeto.notificador.desactivar()
            self.objeto = objeto
            # Activo la notificación
            self.objeto.notificador.activar(self.aviso_actualizacion)   
        except IndexError:
            self.objeto = None
        self.activar_widgets(self.objeto != None)
        self.actualizar_ventana(objeto_anterior = anterior)

    def nuevo(self, boton):
        """
        Crea y muestra un nuevo objeto de la clase.
        """
        params = {}
        for colname in self.clase.sqlmeta.columns:
            col = self.clase.sqlmeta.columns[colname]
            params[colname] = get_valor_defecto(col)
        cad_params = ", ".join(["%s = %s" % (param, params[param]) 
                                for param in params])
        self.objeto = eval("self.clase(%s)" % (cad_params))
        self.actualizar_ventana()

    def buscar(self, boton):
        """
        Pide un texto a buscar y hace activo el resultado 
        de la búsqueda.
        """
        from formularios.seeker import Seeker
        # 0.- ¿Qué estamos buscando, sentrañas mías?
        a_buscar = utils.ui.dialogo_entrada(
                    titulo = _("BUSCAR %s" % self.clase.__name__.upper()), 
                    texto = _("Introduzca el texto a buscar:"), 
                    padre = self.wids['ventana'])
        if a_buscar != None:
            # 1.- Uso el propio buscador Seeker aquí:
            buscador = Seeker(clase = self.clase)
            buscador.buscar(a_buscar)
            # 2.- Lo muestro en una ventana de resultados
            if buscador.resultados:
                if len(buscador.resultados) > 1:
                    filas = [(r.puid, r.info) for r in buscador.resultados]
                    puid = utils.ui.dialogo_resultado(filas, 
                            _("SELECCIONE %s" % self.clase.__name__.upper()), 
                            self.wids['ventana'], 
                            ("PUID", "Descripción"))
                else:
                    puid = buscador.resultados[0].puid
                # 3 .- Y hago el objeto activo si no ha cancelado
                try:
                    objeto = pclases.getObjetoPUID(puid)
                except (ValueError, AttributeError):  # Canceló
                    pass
                else:
                    self.ir_a(objeto)
            else:
                utils.ui.dialogo_info(titulo = "NO ENCONTRADO", 
                    texto = "No se encontraron resultados para «{0}»".format(
                        a_buscar), 
                    padre = self.wids['ventana'])

    def guardar(self, boton):
        """
        Guarda los valores de la ventana en los atributos del objeto.
        """
        for colname in self.clase.sqlmeta.columns:
            col = self.clase.sqlmeta.columns[colname]
            valor_anterior = getattr(self.objeto, colname)
            valor_ventana = self.leer_valor(col)
            if valor_ventana == None:   # El usuario ha metido alguna burrada.
                valor_ventana = valor_anterior
            setattr(self.objeto, colname, valor_ventana)
        self.objeto.syncUpdate()
        self.objeto.sync()
        self.objeto.make_swap()
        self.wids['b_guardar'].set_sensitive(False)
        self.actualizar_ventana()

    def borrar(self, boton):
        """
        Elimina el objeto activo en ventana y vuelve al último de la tabla.
        """
        if self.objeto != None:
            if utils.ui.dialogo(
                    titulo = "¿ELIMINAR? · <%s>" % (
                        self.objeto.puid), 
                    texto = "Se intentará borrar %s.\n"
                            "¿Está seguro?" % self.objeto.get_info(),
                    padre = self.wids['ventana']):
                try:
                    self.objeto.destroySelf()
                except:
                    relacionados = []
                    for jcol in self.objeto.sqlmeta.joins:
                        otros = getattr(self.objeto, jcol.joinMethodName)
                        for o in otros:
                            relacionados.append(o)
                    utils.ui.dialogo_info(titulo = "NO SE PUEDE ELIMINAR", 
                        texto = "El objeto está relacionado con los sigui"
                                "entes elementos aún activos.\n"
                                "Desvincúlelos primero:\n\n - " 
                                + "\n - ".join(
                                    ['<span face="monospace">%s</span>' 
                                        % ente.get_info() 
                                     for ente in relacionados]),
                        padre = self.wids['ventana'])
                else:
                    self.ir_a_primero()

    def rellenar_tabla(self, coljoin, coltotal = None, e_total = None, 
                       ocultar_col_relacionada = True):
        """
        Introduce los registro de coljoin relacionados 
        en el modelo del listview construido para él.
        
        @param self
        @param coljoin: "Columna" del objeto principal que guarda la relación 
                        uno a muchos. Sirve para determinar el TreeView a 
                        actualizar.
        @param coltotal: Si es != None debe ser un nombre de columna sobre la 
                        que se hará un sumatorio.
        @param e_total: Si se especifica coltotal, debe pasarse también un 
                        widget de tipo gtk.Entry donde mostrar ese total. 
        """
        mi_propia_clase = coljoin.soClass
        mi_propia_clase_como_campoFK = mi_propia_clase.__name__ + "ID"
        mi_propia_clase_como_campoFK = (
            mi_propia_clase_como_campoFK[0].lower()
            + mi_propia_clase_como_campoFK[1:])
        try:
            tv = self.wids[coljoin.joinMethodName]
        except KeyError:
            return  # Este widget no se muestra. No existe en la ventana.
        vpro = VentanaProgreso(padre = self.wids['ventana'])
        txtpro = "Buscando %s..." % coljoin.joinMethodName
        vpro.set_valor(0.0, txtpro)
        vpro.mostrar()
        model = tv.get_model()
        sqlmetaotherClass = getattr(coljoin.otherClass, "sqlmeta")
        columnas = getattr(sqlmetaotherClass, "columns").keys()
        model.clear()
        if coltotal:
            assert e_total != None, "ventana_generica::rellenar_tabla -> "\
                                    "Debe especificar también un gtk.Entry "\
                                    "donde mostrarlo en el parámetro e_total."
            total = 0.0
        relacionados = getattr(self.objeto, coljoin.joinMethodName)
        tot = len(relacionados)
        i = 0.0
        for registro in relacionados:
            vpro.set_valor(i / tot, txtpro + " (%d)" % registro.id)
            i += 1
            fila = []
            for columna in columnas:
                if (ocultar_col_relacionada 
                    and columna == mi_propia_clase_como_campoFK):
                    continue
                valor = getattr(registro, columna)
                # Primero opero con él.
                if columna == coltotal:
                    try:
                        total += valor
                    except TypeError, te:   # Debe ser un None.
                        ttt = "ventana_generica::rellenar_tabla -> "\
                              "Valor '%s' no válido. Se ignora en el "\
                              "sumatorio.\n\tExcepción: %s" % (valor, te)
                        print ttt
                # Y ahora lo pongo bonico del "to".
                valor = humanizar(valor, registro.sqlmeta.columns[columna])
                fila.append(valor)
            fila.append(registro.get_puid())
            model.append(None, (fila))  # Es un treeview plano que usaré como 
                                    # listview. Por eso el nodo padre es None.
        if coltotal:
            strtotal = utils.numero.float2str(total, autodec = True)
            e_total.set_text(strtotal)
            utils.ui.combo_set_from_db(
                self.wids['cb_total_' + coljoin.joinMethodName], 
                coltotal)
        vpro.ocultar()

    def relacionarme_con(self, boton, tv, coljoin, 
                         func_actualizar_model = GALACTUS, 
                         permitir_crear = False):
        """
        Construye una relación entre un objeto y el actual en el sentido n a 1.
        Aquí se solicita el objeto a relacionar y se instanciará su clave 
        ajena a la primaria del objeto en ventana.
        
        @param tv: TreeView de donde obtener la selección.
        @param coljoin: Columna de la relación uno a muchos entre el objeto y 
                        los de las filas mostradas.
        @param permitir_crear: Si True permitirá crear un objeto nuevo que 
                               relacionar con el presente. Si es False solo 
                               dejará seleccionar alguno de los existentes.
        """
        # 0.- Primero pido el objeto con un diálogo_combo.
        clasedest = coljoin.otherClass
        nombreclasedest = coljoin.otherClassName
        nombre_colID = coljoin._dbNameToPythonName()
        yo = self.objeto
        if pclases.DEBUG:
            print "clasedest", clasedest
            print "nombreclasedest", nombreclasedest
            print "nombre_colID", nombre_colID
            print "yo", yo
        try:
            #FIXME: Esto es rarísimo. Al añadir un resultado a las líneas 
            # de venta no permite seleccionar ninguno porque esta consulta de 
            # abajo no devuelve nada.
            raise AttributeError, "ventana_generica.py -> FIXME"
            items = clasedest.select(
                getattr(clasedest.q, nombre_colID) != yo.id, orderBy = "id")
            if pclases.DEBUG:
                print "1", items.count()
        except AttributeError:  # yo es None.
            items = clasedest.select(orderBy = "id")
            if pclases.DEBUG:
                print "2", items.count()
        opciones = [(item.id, item.get_info()) for item in items]
        if pclases.DEBUG:
            print "len(opciones)", len(opciones)
        if permitir_crear:
            opciones.insert(0, (0, " -> Crear %s" % nombreclasedest))
        id = utils.ui.dialogo_combo(
                            titulo = "SELECCIONE %s" % nombreclasedest.upper(),
                            texto = "Seleccione una opción del desplegable:", 
                            padre = self.wids['ventana'], 
                            opciones = opciones)
        if id != None:
            if yo:
                if isinstance(coljoin, pclases.joins.SORelatedJoin):
                    # Relación muchos a muchos:
                    nombre_func = "add%s" % (coljoin.otherClassName)
                    func = getattr(yo, nombre_func)
                    if id > 0:
                        # Relaciono conmigo:
                        dependiente = clasedest.get(id)
                        func(dependiente)
                    else:
                        # Creo objeto, si hace falta.
                        dependiente = clasedest()
                        func(dependiente)
                        VentanaGenerica(objeto = dependiente, 
                                        usuario = self.__usuario)
                else:   # Relación uno a muchos:
                    # 1.1.- Después relaciono conmigo
                    if id > 0:
                        dependiente = clasedest.get(id)
                        setattr(dependiente, nombre_colID, yo.id)
                    # 1.2.- O bien lo creo nuevo con la clave ajena ya 
                    #       instanciada
                    else:
                        kw = {nombre_colID: yo.id}
                        dependiente = clasedest(**kw)
                        VentanaGenerica(objeto = dependiente, 
                                        usuario = self.__usuario)
                # 2.- Y actualizo
                self.rellenar_tabla(coljoin)

    def build_listview(self, coljoin, ocultar_col_relacionada = True):
        """
        Construye un listview y su modelo para albergar los 
        datos relacionados a través de la columna "uno-a-muchos" «col».
        ocultar_col_realacionada a True oculta la columna que relaciona los 
        registros del ListView con el objeto de la propia ventana donde se 
        van a mostrar las relaciones (el self.objeto, vaya).
        """
        mi_propia_clase = coljoin.soClass
        mi_propia_clase_como_campoFK = mi_propia_clase.__name__ + "ID"
        mi_propia_clase_como_campoFK = (
            mi_propia_clase_como_campoFK[0].lower()
            + mi_propia_clase_como_campoFK[1:])
        otherClass_sqlmeta = getattr(coljoin.otherClass, "sqlmeta")
        columnas = getattr(otherClass_sqlmeta, "columns")
        cols = []
        treeview = gtk.TreeView()
        i = 0
        cols_a_cambiar_por_combo = []
        for colname in columnas:
            if (ocultar_col_relacionada 
                and colname == mi_propia_clase_como_campoFK):
                continue
            nombre = labelize(colname)
            tipo = "gobject.TYPE_STRING"
            # XXX: Si lo dejo todo como cadena (que también funciona) pierdo 
            # la alineación a la derecha. Habría también que descomentar el 
            # humanizar para que al menos el formato fuera amigable.
            if isinstance(columnas[colname], pclases.SOFloatCol):
                tipo = "gobject.TYPE_FLOAT"
            elif isinstance(columnas[colname], pclases.SOIntCol): 
                tipo = "gobject.TYPE_INT"
            elif isinstance(columnas[colname], pclases.SOForeignKey):
                cols_a_cambiar_por_combo.append((i, colname))
            # XXX
            cols.append([nombre, tipo, True, True, False, 
                         self._cambiar_valor_tv, (colname, treeview, i)])
            i += 1
        cols[0][4] = True   # Búsqueda interactiva en la primera columna.
        cols.append(["PUID", "gobject.TYPE_STRING", False, False, False, None])
        # Preparo un TreeView por si en el futuro me interesa añadir 
        # agrupaciones o algo.
        utils.ui.preparar_treeview(treeview, cols, multi = True)
        #utils.ui.preparar_listview(treeview, cols, multi = True)
        treeview.connect("row-activated", _abrir_en_ventana_nueva, 
                         self.__usuario, self.rellenar_tabla, coljoin)
        despl = gtk.ScrolledWindow()
        despl.add(treeview)
        #frame = gtk.Frame(label = coljoin.otherClassName)
        frame = gtk.Expander(label = coljoin.otherClassName)
        contenedor = gtk.VBox()
        frame.add(contenedor)
        botonera = gtk.HButtonBox()
        botonera.set_layout(gtk.BUTTONBOX_SPREAD)
        badd = gtk.Button(stock = gtk.STOCK_ADD)
        bdrop = gtk.Button(stock = gtk.STOCK_REMOVE)
        botonera.add(badd)
        badd.connect("clicked", self.relacionarme_con, treeview, 
                                coljoin, self.rellenar_tabla, True)
        botonera.add(bdrop)
        #bdrop.connect("clicked", self.desrelacionarme_de, treeview, coljoin)
        bdrop.connect("clicked", self.desrelacionarme_de, treeview, coljoin, 
                      True)
        contenedor.add(despl)
        container_botonera = gtk.HBox()
        container_botonera.pack_start(botonera)
        totalizador = self.build_totalizador_treeview(treeview, 
                                                      coljoin, columnas)
        if totalizador:
            container_botonera.pack_start(totalizador, expand = False)
        container_botonera.set_property("name", 
                                        "botonera_" + coljoin.joinMethodName)
        self.wids[container_botonera.name] = container_botonera
        contenedor.pack_start(container_botonera, expand = False)
        frame.show_all()
        for numcol, nombrecol in cols_a_cambiar_por_combo:
            col = columnas[nombrecol]
            other_class = getattr(pclases, 
                            col.foreignName[0].upper() + col.foreignName[1:])
            opts = [(i.get_info(), i.puid) 
                    for i in other_class.select(orderBy = "id")]
            utils.ui.cambiar_por_combo(treeview, numcol, 
                                       opts, nombrecol, 
                                       ventana_padre = self.wids['ventana'])
        return frame, treeview

    def _cambiar_valor_tv(self, 
                          cell, path, nuevo_texto, colname, tv, colnumber):
        model = tv.get_model()
        puid = model[path][-1]
        objeto = pclases.getObjetoPUID(puid)
        col = objeto.sqlmeta.columns[colname]
        try:
            nuevo_valor = casar(nuevo_texto, col)
        except (ValueError, TypeError):
            utils.ui.dialogo_info(titulo = "ERROR DE FORMATO", 
                texto = 
                  "El valor introducido «{0}» no es del tipo correcto.".format(
                    nuevo_texto), 
                padre = self.wids['ventana'])
        else:
            setattr(objeto, colname, nuevo_valor)
            objeto.syncUpdate()
            model[path][colnumber] = humanizar(getattr(objeto, colname), 
                                               objeto.sqlmeta.columns[colname])

    def build_totalizador_treeview(self, tv, coljoin, 
                                   columnas_objeto_relacionado):
        """
        Devuelve un HBox con un ComboBox y un Entry no editable. El ComboBox 
        tiene asociado al evento «changed» una función que hace un sumatorio 
        de la columna seleccionada en el mismo y lo escribe en el entry.
        En el Combo solo estarán las columnas de tipo Float o Int. No tiene 
        sentido sumar textos.
         
        @param 
        @param tv: El TreeView que contiene los datos a sumar.
        @param coljoin: Objeto de SQLObject que representa la unión.
        @param columnas_objeto_relacionado: Diccionado con las columnas de la 
                                            otra clase relacionada.
        """
        totalizador = None
        # TODO: PLAN: Hacer los totales también con horas 
        # (datetime.timedelta = SOTimeCol, creo porque los TimestampCol son 
        # fechas con hora).
        clases_numericas = (pclases.SOBigIntCol, pclases.SOCurrencyCol, 
                            pclases.SODecimalCol, pclases.SOFloatCol, 
                            pclases.SOIntCol, pclases.SOMediumIntCol, 
                            pclases.SOSmallIntCol, pclases.SOTinyIntCol) 
        nombres_colsnumericas = []
        for col in columnas_objeto_relacionado:
            for clase_numerica in clases_numericas:
                if isinstance(columnas_objeto_relacionado[col],clase_numerica):
                    nombres_colsnumericas.append(col)
        if nombres_colsnumericas:
            nombres_colsnumericas.sort()
            combo_total = gtk.combo_box_new_text()
            for nombrecol in nombres_colsnumericas:
                combo_total.append_text(nombrecol)
            entry_total = gtk.Entry()
            entry_total.set_has_frame(False)
            entry_total.set_editable(False)
            combo_total.connect("changed", self.actualizar_total_tv, 
                                           tv, coljoin, entry_total)
            totalizador = gtk.HBox()
            labeler = gtk.Label("Totalizar ")
            labeler.set_alignment(1.0, labeler.get_alignment()[1])
            totalizador.pack_start(labeler)
            totalizador.pack_start(combo_total)
            totalizador.pack_start(entry_total)
            entry_total.set_property("name", 
                                     "e_total_" + coljoin.joinMethodName)
            self.wids[entry_total.name] = entry_total
            combo_total.set_property("name", 
                                     "cb_total_" + coljoin.joinMethodName)
            self.wids[combo_total.name] = combo_total
            labeler.set_property("name", "l_total_" + coljoin.joinMethodName)
            self.wids[labeler.name] = labeler
            totalizador.set_property("name", 
                                     "totalizador_" + coljoin.joinMethodName)
            self.wids[totalizador.name] = totalizador
        return totalizador
    
    def actualizar_total_tv(self, combo, tv, coljoin, e_total):
        """
        Actualiza el TreeView indicado usando el nombre de columna marcado en 
        el combo para hacer la suma.
        """
        coltotal = combo.get_active_text()
        self.rellenar_tabla(coljoin, coltotal, e_total)
    
    def desrelacionarme_de(self, boton, tv, coljoin, borrar_despues = False, 
                           forzar_borrado = False):
        """
        Elimina la relación entre los objetos correspondientes a las filas 
        seleccionadas en el TreeView y el objeto actual de la ventana.
        Después actualiza el model del TreeView para reflejar los cambios.
        
        OJO: Solo elimina la relación. El objeto relacionado no se intenta 
        eliminar de la base de datos a no ser que se reciba borrar_despues 
        a True.
        
        @param self
        @param tv: TreeView de donde obtener la selección.
        @param coljoin: Columna de la relación uno a muchos entre el objeto y 
                        los de las filas mostradas.
        @param borrar_despues: Determina si se debe intentar eliminar el objeto 
                               relacionado después de "desrelacionarlo".
        @param forzar_borrado: Si True y borarr_despues también a True inenta 
                               eliminar en cascada el registro en caso de que 
                               el borrado normal falle.
        """
        sel = tv.get_selection()
        if sel and utils.ui.dialogo(titulo = "¿ESTÁ SEGURO?", 
                            texto = "¿Desea quitar la fila seleccionada?", 
                            padre = self.wids['ventana']):
            model, iters = sel.get_selected_rows()
            for iter in iters:
                puid = model[iter][-1]
                objeto = pclases.getObjetoPUID(puid)
                nombre_colID = coljoin._dbNameToPythonName()
                setattr(objeto, nombre_colID, None)
                objeto.syncUpdate()
                if borrar_despues:
                    try:
                        objeto.destroySelf()
                    except:
                        if forzar_borrado:
                            objeto.destroy_en_cascada()
                            # TODO: Aquí se echa de menos un logger para 
                            # volcar el resultado del borrado, qué usuario lo 
                            # ha hecho, etc.
            if iters:
                self.rellenar_tabla(coljoin)

    def add_campo_calculado(self, getter, etiqueta = None, entry = None, 
                            nombre = None, *args, **kw):
        """
        Crea un HBox con un Label y un Entry para mostrar el valor del campo 
        calculado en la pestaña Datos de la ventana como si fuera un campo 
        más.
        Devuelve la función que actualiza el campo. Generalmente no debería 
        llamarse manualmente porque se incluye de manera automática en el 
        "actualizar_ventana" genérico de la clase.
        getter debe ser la función a la que llamar para obtener el valor a 
        mostrar. Si se necesitan más parámetros, se añadirán al final como 
        args y kw. También puede recibirse como cadena si es una función 
        de self.objeto.
        Si se especifica el gtk.Entry, se asume que ya en el .glade está 
        el gtk.Label y toda la pesca.
        """
        if etiqueta == None:
            if isinstance(getter, str):
                etiqueta = getter
            elif hasattr(getter, __doc__):
                etiqueta = getter.__doc__
            elif hasattr(getter, __name__):
                etiqueta = getter__name__
            else:
                etiqueta = ""
        if not entry:
            hbox = gtk.HBox(spacing = 5)
            label = gtk.Label(etiqueta)
            entry = gtk.Entry()
            entry.set_property("editable", False)
            entry.set_property("has-frame", False)
            hbox.pack_start(label, expand = False, padding = 10)
            hbox.pack_start(entry, padding = 3)
            hbox.show_all()
            self.wids['vbox'].pack_start(hbox)
            if nombre:
                self.wids["hb_%s" % nombre] = hbox
                self.wids["l_%s" % nombre] = label
                self.wids["e_%s" % nombre] = entry
        if isinstance(getter, str):
            func_actualizacion = lambda *args, **kw: \
                entry.set_text(getattr(self.objeto, getter)(*args, **kw))
        else:
            func_actualizacion = lambda *args, **kw: \
                entry.set_text(getter(*args, **kw))
        self._funcs_actualizacion_extra.append((func_actualizacion, args, kw))
        func_actualizacion(*args, **kw) # La primera vez lo llamo yo, porque 
        # como esto se hace DESPUÉS de que el constructor de VentanaGenerica 
        # haya terminado, no da lugar a actualizar el campo calculado hasta 
        # el siguiente rellenar_widgets (que será cuando el usuario lo haga 
        # manualmente o al cambiar de objeto).
        return func_actualizacion


# Utilidades genéricas de widgets
def build_widget(col, label = None, ventana = None, usuario = None):
    """
    A partir de la columna recibida, construye un hbox con 
    dos widgets más. Un label y el widget que mostrará el 
    valor en sí del campo.
    Si "label" es diferente de None, se usará ese como texto, 
    en otro caso se usará el nombre del campo.
    Devuelve el contenedor hbox externo y el widget asociado al campo en sí.
    wigets es un diccionario de widgets existentes. Si se intenta crear uno 
    que ya existe en el XML del glade (se determina por el nombre), en su 
    lugar devolverá el que ya existe.
    """
    # Construyo el widget que contendrá la etiqueta y el valor del campo:
    contenedor_externo, wvalor = buscar_widget(col, ventana.wids)
    if not contenedor_externo:
        contenedor_externo = gtk.HBox()
        if label == None:
            label = labelize(col.name)
        wlabel = gtk.Label(label)
        contenedor_externo.pack_start(wlabel, expand = False, padding = 10)
    # Construyo widget para escribir y leer el valor del campo:
    if not wvalor:
        wvalor, contenedor = build_widget_valor(col, col.name, ventana, 
                                                usuario)
        widget_campo = contenedor != None and contenedor or wvalor
    else:
        widget_campo = wvalor
    if not widget_campo.parent:
        contenedor_externo.pack_start(widget_campo)
    # NUEVO: Botón deshacer justo después del widget con valor del campo:
    padre_widget = wvalor.parent
    if es_widget_editable(wvalor):  # Si no es editable, no hay deshacer.
        boton_deshacer = build_undo_button(col, ventana, wvalor)
        boton_save = build_save_button(col, ventana, wvalor)
        if isinstance(wvalor, gtk.ComboBox):    # Por estética, más que nada.
            padre_widget = wvalor.parent.parent
        try:
            padre_widget.pack_start(boton_deshacer, expand=False, fill=False)
            padre_widget.pack_start(boton_save, expand=False, fill=False)
        except AttributeError:
            padre_widget.add(boton_deshacer)
            padre_widget.add(boton_save)
    pos_wvalor = -1
    _padre_widget = padre_widget 
    while pos_wvalor == -1 and _padre_widget != None:
        pos_wvalor = encontrar_posicion_en_padre(wvalor, padre = _padre_widget)
        _padre_widget = _padre_widget.parent
    try:
        padre_widget.reorder_child(boton_deshacer, pos_wvalor + 1)
        padre_widget.reorder_child(boton_save, pos_wvalor + 1)
    except (AttributeError, UnboundLocalError):
        pass
    # Muestro todo lo que acabo de construir y devuelvo...
    contenedor_externo.show_all()
    # ... el contenedor para incrustarlo en la ventana y el widget para 
    # controlar los cambios, mostrar, guardar, etc.
    return contenedor_externo, wvalor

def es_widget_editable(w):
    """
    Devuelve True si el widget es editable en la ventana.
    """
    # ¿Es un checkbox?
    if isinstance(w, gtk.CheckButton):  # XXX
        res = True
    else:
        try:
            res = w.get_property("editable") 
        except TypeError:   # ¿ComboBox o algo asina? Probemos con sus hijos...
            try:
                res = reduce(lambda v1, v2: v1 or v2, 
                             [es_widget_editable(h) for h in w.get_children()])
            except (TypeError, AttributeError):
                res = False
    return res

def encontrar_posicion_en_padre(w, padre = None):
    """
    Siempre devuelve un entero que será la posición del widget en su 
    contenedor padre comenzando por la posición 0.
    Si padre se especifica, busca la posición de w (o de sus padres) en el 
    padre recibido. Devuelve -1 si no se encentra a w ni a ninguno de sus 
    ascendientes.
    """
    if padre == None:
        padre = w.parent
    i = 0
    for hijo in padre.get_children():
        if hijo is w:
            return i
        i += 1
    if w.parent != None:
        return encontrar_posicion_en_padre(w.parent)
    return -1

def func_deshacer(ventana, col, boton = None, mas_botones = []):
    objeto = ventana.objeto
    try:
        valor_almacenado = getattr(objeto, col.name)
    except AttributeError:  # Objeto es None o ventana no tiene objeto...
        valor_almacenado = None
    ventana.escribir_valor(col, valor_almacenado)
    try:
        boton.set_sensitive(False)
        boton_save = ventana.wids['b_save_' + col.name]
        boton_save.set_sensitive(False)
    except AttributeError:
        pass

def func_guardar(ventana, col, boton = None, mas_botones = []):
    valor_pantalla = ventana.leer_valor(col)
    objeto = ventana.objeto
    try:
        setattr(objeto, col.name, valor_pantalla)
        objeto.syncUpdate()
    except AttributeError:  # Objeto es None o ventana no tiene objeto...
        valor_almacenado = None
    else:
        objeto.make_swap(col.name)
        objeto.sync()
        ventana.escribir_valor(col) 
    try:
        boton.set_sensitive(False)
        boton_undo = ventana.wids['b_undo_' + col.name]
        boton_undo.set_sensitive(False)
    except AttributeError:
        pass

def build_undo_button(col, ventana, wvalor): 
    """
    Recibe una columna de sqlmeta de la clase y devuelve un botón que 
    sustituye el contenido del widget por el valor almacenado en el objeto.
    Almacena el botón (no el contenedor externo) en el diccionario de widgets 
    de la ventana.
    """
    #b_undo = gtk.Button(stock = gtk.STOCK_UNDO)
    b_undo = gtk.Button()
    image = gtk.Image()
    image.set_from_stock(gtk.STOCK_UNDO, gtk.ICON_SIZE_BUTTON)
    b_undo.set_image(image)
    b_undo.set_property("tooltip-text", "Deshacer")
    b_undo.connect("clicked", lambda boton: func_deshacer(ventana, col, boton))
    b_undo.set_property("name", "b_undo_" + col.name)
    ventana.wids[b_undo.name] = b_undo
    b_undo_container = gtk.Alignment(xalign = 0.5, yalign = 0.5)
    b_undo_container.add(b_undo)
    activar_undo = lambda widget_valor, *args, **kw: b_undo.set_sensitive(True)
    try:
        wvalor.connect_after("changed", activar_undo)
    except TypeError: 
        if isinstance(wvalor, gtk.TextView):
            wvalor.connect_after("move-cursor", activar_undo)
        else:   # Es un check de buleano.
            wvalor.connect_after("toggled", activar_undo) 
    b_undo.set_sensitive(False) # Inicia así. No hay cambios en la ventana.
    #b_undo.connect("focus", 
    #               lambda w, dirfocus: w.get_toplevel().child_focus(dirfocus))
    return b_undo_container

def build_save_button(col, ventana, wvalor): 
    """
    Recibe una columna de sqlmeta de la clase y devuelve un botón que 
    sustituye el valor almacenado en el objeto por el contenido del widget.
    Almacena el botón (no el contenedor externo) en el diccionario de widgets 
    de la ventana.
    """
    b_save = gtk.Button()
    image = gtk.Image()
    image.set_from_stock(gtk.STOCK_SAVE, gtk.ICON_SIZE_BUTTON)
    b_save.set_image(image)
    b_save.set_property("tooltip-text", "Guardar")
    b_save.connect("clicked", lambda boton: func_guardar(ventana, col, boton))
    b_save.set_property("name", "b_save_" + col.name)
    ventana.wids[b_save.name] = b_save
    b_save_container = gtk.Alignment(xalign = 0.5, yalign = 0.5)
    b_save_container.add(b_save)
    activar_save = lambda widget_valor, *args, **kw: b_save.set_sensitive(True)
    try:
        wvalor.connect_after("changed", activar_save) 
    except TypeError:   # Es un check de buleano.
        if isinstance(wvalor, gtk.TextView):
            wvalor.connect_after("move-cursor", activar_save)
        else:   # Es un check de buleano.
            wvalor.connect_after("toggled", activar_save)
    b_save.set_sensitive(False) # Inicia así. No hay cambios en la ventana.
    #b_save.connect("focus", 
    #               lambda w, dirfocus: w.get_toplevel().child_focus(dirfocus))
    return b_save_container

def buscar_widget(col, wids):
    """
    Busca y devuelve el widget correspondiente a la columna «col» en los 
    widgets actuales «wids». Lo hace según el nombre de la columna. Si los 
    widgets vienen del XML del glade, deben respetar el formato 
    [tv|e|cb|cbe|l|txt]_nombreColumna
    También incluye el contenedor externo como primer elemento de la lista 
    devuelta o None si está directamente en un contenedor "superior" (ventana, 
    hbox hijo de ventana...).
    Puede devolver también el contenedor y None para que se construya el 
    widget en un gtk.Container cuyo nombre coincida con el del campo.
    """
    contenedor = widget = None
    nombre_col = col.name
    for nombre_w in wids:
        nombre_col_widget = extraer_nombre_col(nombre_w, agregar_id = False)
                                              # agregar_id = "ID" in nombre_col)
        #print nombre_col_widget, nombre_w, nombre_col
        if nombre_col_widget == nombre_col:
            widget = wids[nombre_w]
            if not contenedor:  # Si ya lo he encontrado, mejor ese, que para 
                                # algo lo he puesto explícitamente en el .glade
                contenedor = widget.parent
            if isinstance(widget, gtk.Label):
                contenedor = widget.parent
                widget = None   # Y así el hueco lo ocupará el widget que 
                                # se construya después dinámicamente.
            elif (isinstance(widget, gtk.Container) 
                  and not (isinstance(widget, gtk.TextView)
                           or isinstance(widget, gtk.ComboBox))):
                contenedor = widget
                widget = None
            if ((isinstance(contenedor, gtk.Window) 
                    or contenedor.name == "vbox")):
                #and not isinstance(contenedor, gtk.ScrolledWindow)):
                # vbox es el nombre del Box "abuelo" de campos en la ventana
                # genérica.
                contenedor = None   # No me vale. Que se construya otro.
            # Si es un combo creado, hay que rellenar los valores del model:
            if (isinstance(col, pclases.SOForeignKey) 
                    and isinstance(widget, gtk.ComboBox)):
                model = widget.get_model()
                if not model:
                    model = gtk.ListStore(ENTERO, CADENA)
                    widget.set_model(model)
                    tablajena = col.foreignKey
                    clase_tablajena = getattr(pclases, tablajena)
                    rellenar_lista(widget, clase_tablajena)
            break   # No sigo buscando
    if pclases.DEBUG:
        print "col:", col
        print "nombre_col_widget:", nombre_col_widget
        print "nombre_col:", nombre_col
        print "widget:", widget
        print "contenedor:", contenedor
        print 80*":"
    return contenedor, widget

def extraer_nombre_col(s, agregar_id = False):
    """
    Para s = e_nombreCol, devuelve nombreCol.
    Para nombreCol, devuelve nombreCol.
    Para nombre_col, devuelve nombreCol.
    Para e_nombre_col, devuelve nombreCol.
    Para cualquier otra cosa, devuelve s.
    """
    prefixes = ("tv", "e", "cb", "cbe", "l", "txt")  # Con regex sería más 
        # rápido, pero ya sabemos cómo funcionan las cosas aquí...
        # PLAN: Optimizar con expresiones regulares cuando me dejen respirar...
    for p in prefixes:
        if s.startswith(p + "_"):
            s = s[s.index("_")+1:]
    if agregar_id:
        s += "ID"
    s = camelize(s)
    return s

def cargar_formulario(clase, objeto, usuario = None):
    """
    Intenta cargar el formulario correspondiente a la clase o lanza una 
    excepción del tipo ValueError si no se encuentra.
    """
    if not isinstance(clase, str):
        clase = clase.__name__
    nombre_ventana = decamelize(clase, "_")
    excptTxt = "%s no existe como formulario independiente." % nombre_ventana
    try:
        exec("from formularios import %s" % nombre_ventana)
    except ImportError:
        raise ValueError, excptTxt
    import formularios
    from string import uppercase
    modulo = getattr(formularios, nombre_ventana)
    mancatrl = [0, None]
    # De todas las que he encontrado... ¿cuál será?
    # Atención, ¡se viene el estallido! (en forma de chapuzarl)
    for nombre_atributo in dir(modulo):
        if nombre_atributo[0] in uppercase: # Es una clase. Estándar de facto.
            puntos = comparar_similitud(nombre_ventana, nombre_atributo)
            if puntos > mancatrl[0]:
                mancatrl = [puntos, nombre_atributo]
    if mancatrl[1] is None:
        raise ValueError, excptTxt
    clase_ventana = mancatrl[1]    # Es una cadena todavía.
    ventana = getattr(modulo, clase_ventana)
    ventana(objeto, usuario)

def comparar_similitud(cad1, cad2):
    """
    Compara cuánto se parecen la cadena 2 a la 1 ignorando guiones bajos.
    Es case insensitive y no conmutativa.
    """
    # TODO: Ojo. NO ES CONMUTATIVA. f(cad1, cad2) != f(cad2, cad1) 
    puntos = 0
    pos = 0
    for letra in cad2:
        if pos >= len(cad1):
            break
        if pclases.DEBUG and pclases.VERBOSE:
            print cad1[pos], letra, puntos
        if cad1[pos] == "_":
            pos += 1
        if letra.lower() == cad1[pos]:
            puntos +=1 
            pos += 1
    return puntos

def overrides_glade(clase):
    """
    Si existe un fichero Glade con el nombre de la clase en el directorio 
    devuelve la ruta al fichero (evaluable como VERDADERO).
    En otro caso, devuelve FALSO.
    """
    if not isinstance(clase, str):
        clase = clase.__name__
    static_glade = decamelize(clase, "_") + ".glade"
    if static_glade.startswith("_"):
        static_glade = static_glade[1:]
    if static_glade.endswith("_"):
        static_glade = static_glade[:-1]
    dirs = (os.path.join("formularios", "glades"), 
            "glades", 
            os.path.join("..", "formularios", "glades"))
    res = False
    for d in dirs:
        if os.path.exists(os.path.join(d, static_glade)):
            res = os.path.join(d, static_glade)
            break
    return res

def labelize(colname):
    """
    Devuelve el nombre de columna "adecentado, pintaito y guapo" para que no 
    se vea en CamelCase, con la coletilla "ID", etc.
    """
    nombre = colname.replace("ID", "")
    nombre = decamelize(nombre) #colname[0].upper() + colname[1:]
    nombre = nombre.title()
    return nombre

def camelize(texto, strict = False):
    """
    Cambia algo_como_esto en algoComoEsto.
    Cambia algo_como_ESTO en algoComoESTO.
    Si "strict", entonces cambia algo_como_eSto en algoComoEsto.
    """
    res = ""
    mayusculea = False
    for l in texto:
        if l == "_":
            mayusculea = True
        else:
            if mayusculea:
                res += l.upper()
                mayusculea = False
            else:
                if strict:
                    res += l.lower()
                else:
                    res += l
    return res

def decamelize(texto, carsub = " "):
    """
    Converte "algoComoEsto" en "algo como esto".
    """
    res = ""
    try:
        res = texto[0].lower()
    except IndexError:
        pass    # ¿Decamelize de cadena vacía? Mereces la muerte, pero voy 
                # a ser benévolo y ni siquiera te voy a tirar una excepción.
    for l in texto[1:]:
        if l.isupper():
            res += carsub + l.lower()
        else:
            res += l
    return res

def rellenar_lista(w, clase_tablajena, orden = "id", 
                   formato = FORMATO_DESPLEGABLES_GETINFO):
    func_select = getattr(clase_tablajena, "select")
    if orden == None:
        kworden = {}
    else:
        kworden = {'orderBy': orden}
    datos = []
    for reg in func_select(**kworden):
        if formato == FORMATO_DESPLEGABLES_COMPLETO:
            campos = []
            for nombre_columna in clase_tablajena.sqlmeta.columns:
                valor = getattr(reg, nombre_columna)
                columna = clase_tablajena.sqlmeta.columns[nombre_columna]
                if isinstance(valor, bool):
                    strvalor = labelize(nombre_columna) + ": "
                    if valor:
                        strvalor += "Sí"
                    else:
                        strvalor += "No"
                elif isinstance(columna, pclases.SOForeignKey) and valor:
                    clase = getattr(pclases, columna.foreignKey)
                    objeto_relacionado = clase.get(valor)
                    strvalor = objeto_relacionado.get_info()
                else:
                    strvalor = str(valor)
                if valor:   # Me evito espacios, Nones y cosas así.
                    campos.append(strvalor)
                info = ", ".join(campos) 
        elif formato == FORMATO_DESPLEGABLES_PRIMERACOL:
            firstcol = clase_tablajena.sqlmeta.columnList[0]
            for c in clase_tablajena.sqlmeta.columnList:
                if not isinstance(c, pclases.SOForeignKey):
                    firstcol = c
                    break
            valor_firstcol = getattr(reg, firstcol.name)
            info = humanizar(valor_firstcol, firstcol)
        else:
            info = reg.get_info()
        datos.append((reg.id, info))
    utils.ui.rellenar_lista(w, datos)

def build_widget_valor(col, nombre_campo, ventana = None, usuario = None):
    """
    Recibe un objeto de la familia SOCol y devuelve el 
    widget adecuado para mostrar su valor.
    Si es un texto, entero o float: entry.
    Si es un boolean: checkbutton.
    Si es una fecha: entry con un botón para mostrar el calendario.
    Si es un ForeignKey, usar un ComboBoxEntry con utils.rellenar... con las
    tuplas de la tabla referenciada.
    """
    box = None  # Posible contenedor externo.
    if isinstance(col, pclases.SOStringCol): 
        w = gtk.Entry()
        w.set_name(col.name)
    elif isinstance(col, pclases.SOIntCol):
        w = gtk.Entry()
        w.set_name(col.name)
        w.set_alignment(1.0)
    elif isinstance(col, pclases.SOFloatCol):
        w = gtk.Entry()
        w.set_name(col.name)
        w.set_alignment(1.0)
    elif isinstance(col, pclases.SOBoolCol):
        w = gtk.CheckButton()
        w.set_name(col.name)
    elif isinstance(col, pclases.SODateCol):
        box = gtk.HBox()
        w = gtk.Entry()
        w.connect("focus-out-event", actualizar_fecha, None, ventana, 
                                                       nombre_campo)
        w.set_name(col.name)
        #button = gtk.Button(stock = gtk.STOCK_FIND)
        button = gtk.Button()
        i = gtk.Image()
        i.set_from_stock(gtk.STOCK_FIND, gtk.ICON_SIZE_BUTTON)
        button.set_image(i)
        button.set_property("tooltip-text", "Buscar fecha")
        button.connect("clicked", lambda boton: w.set_text(
            utils.fecha.str_fecha(
                utils.ui.mostrar_calendario(w.get_text())
            )))
        button.set_name("b_%s" % (col.name))
        box.add(w)
        cont_button = gtk.VBox()
        cont_button.pack_start(button, fill = False)
        box.pack_start(cont_button, expand = False)
        w.set_alignment(0.5)
    elif isinstance(col, pclases.SOForeignKey):
        w = gtk.ComboBoxEntry()
        w.set_name(col.name)
        tablajena = col.foreignKey
        clase_tablajena = getattr(pclases, tablajena)
        rellenar_lista(w, clase_tablajena)
        box = gtk.HBox()
        prettybox = gtk.VBox() # Es solo para que quede bonito al maximizar.
        prettybox.set_name("prettybox_" + col.name)
        prettybox.pack_start(w, expand = True, fill = False)
        box.pack_start(prettybox)
        b_nuevo_relacionado = _build_boton_nuevo_relacionado(clase_tablajena, 
                                                             w, usuario)
        b_editar_relacionado = _build_boton_editar_relacionado(clase_tablajena,
                                                               w, usuario)
        b_editar_relacionado.set_property("sensitive", 
                                          utils.ui.combo_get_value(w))
        w.connect("changed", lambda cb: b_editar_relacionado.set_property(
            "sensitive", utils.ui.combo_get_value(w)))
        box.pack_start(b_editar_relacionado, expand = False)
        box.pack_start(b_nuevo_relacionado, expand = False)
    else:
        w = gtk.Entry()
        w.set_name(col.name)
    return w, box

def actualizar_fecha(w, event, valor_fallback = None, 
                     ventana = None, nombre_campo = None):
    """
    Intenta parsear la fecha del entry y la reescribe correctamente.
    """
    if ventana != None and nombre_campo != None:
        valor_fallback = getattr(ventana.objeto, nombre_campo)
    if isinstance(valor_fallback, type("cadena")):
        try:
            valor_fallback = utils.fecha.parse_fecha(valor_fallback)
        except (ValueError, TypeError):
            valor_fallback = None
    if valor_fallback == None:
        valor_fallback = datetime.date.today()
    txt = w.get_text()
    try:
        fecha = utils.fecha.parse_fecha(txt)
    except (ValueError, TypeError):
        fecha = valor_fallback
    w.set_text(utils.fecha.str_fecha(fecha))

def _build_boton_nuevo_relacionado(clase_tablajena, combo, usuario = None):
    """
    Construye un botón que se asocia con la creación de un nuevo objeto 
    de la clase ajena e instancia el combo en ese nuevo objeto.
    """
    #badd = gtk.Button(stock = gtk.STOCK_ADD)
    badd = gtk.Button()
    i = gtk.Image()
    i.set_from_stock(gtk.STOCK_ADD, gtk.ICON_SIZE_BUTTON)
    badd.set_image(i)
    badd.set_property("tooltip-text", "Crear")
    contenedor = gtk.VBox()
    contenedor.pack_start(badd, fill = False)
    badd.connect("clicked", _crear_nuevo_relacionado, clase_tablajena, combo, 
                 usuario)
    return contenedor

def _build_boton_editar_relacionado(clase_tablajena, combo, usuario = None):
    """
    Construye un botón que se asocia con la edición del objeto 
    de la clase ajena.
    """
    #badd = gtk.Button(stock = gtk.STOCK_EDIT)
    badd = gtk.Button()
    i = gtk.Image()
    i.set_from_stock(gtk.STOCK_EDIT, gtk.ICON_SIZE_BUTTON)
    badd.set_image(i)
    badd.set_property("tooltip-text", "Editar en ventana nueva")
    contenedor = gtk.VBox()
    contenedor.pack_start(badd, fill = False)
    badd.connect("clicked", _editar_relacionado, clase_tablajena, combo, 
                 usuario)
    return contenedor

def _crear_nuevo_relacionado(boton, clase, combo, usuario = None):
    """
    Crea un nuevo objeto de la clase recibida y actualiza la lista del combo. 
    """
    nuevo_objeto = clase()
    try:
        cargar_formulario(clase, nuevo_objeto, usuario)
    except ValueError:
        VentanaGenerica(nuevo_objeto, usuario = usuario)
    rellenar_lista(combo, clase, formato = FORMATO_DESPLEGABLES_COMPLETO)
    utils.ui.combo_set_from_db(combo, nuevo_objeto.id)

def _editar_relacionado(boton, clase, combo, usuario = None):
    """
    Edita el objeto relacionado de la clase recibida y actualiza la lista del 
    combo.
    """
    id = utils.ui.combo_get_value(combo)
    objeto = clase.get(id)
    try:
        cargar_formulario(clase, objeto, usuario)
    except ValueError:
        VentanaGenerica(objeto, usuario = usuario)
    rellenar_lista(combo, clase)
    utils.ui.combo_set_from_db(combo, objeto.id)

def _abrir_en_ventana_nueva(tv, path, cv, usuario = None, 
                            func_actualizar_model = GALACTUS, 
                            colname = None):
    model = tv.get_model()
    puid = model[path][-1]
    objeto = pclases.getObjetoPUID(puid)
    try:
        cargar_formulario(clase, objeto, usuario)
    except ValueError:
        VentanaGenerica(objeto, usuario = usuario)
    func_actualizar_model(colname)

def get_valor_defecto(col):
    """
    Devuelve un valor por defecto adecuado al tipo de datos de «col».
    """
    if isinstance(col, pclases.SOStringCol): 
        res = "''"
    elif isinstance(col, pclases.SOIntCol):
        res = "0"
    elif isinstance(col, pclases.SOFloatCol):
        res = "0.0"
    elif isinstance(col, pclases.SOBoolCol):
        res = "False"
    elif isinstance(col, pclases.SODateCol):
        res = "datetime.date.today()"
    elif isinstance(col, pclases.SOForeignKey):
        res = "None"
    else:
        res = "None"
    return res

def casar(valor, columna):
    """
    Intenta "casar" el valor recibido en función del tipo de la columna.
    Devuelve el valor en el tipo correcto o lanzará una excepción TypeError o 
    ValueError.
    """
    if isinstance(columna, pclases.SOStringCol): 
        res = str(valor)
    elif isinstance(columna, pclases.SOIntCol):
        res = utils.numero.parse_int(valor)
    elif isinstance(columna, pclases.SOFloatCol):
        res = utils.numero.parse_formula(valor)
        # parse_formula devuelve un float, que pasa bien por el parse_float.
        # Si no es una fórmula, devuelve el valor original, que también debe 
        # acabar pasando por el parse_float de todas formas.
        res = utils.numero.parse_float(res)
    elif isinstance(columna, pclases.SOBoolCol):
        res = bool(valor)
    elif isinstance(columna, pclases.SODateCol):
        if valor != "":
            res = utils.fecha.parse_fecha(valor)
        else:
            res = None
    elif isinstance(columna, pclases.SOForeignKey):
        res = utils.numero.parse_int(valor) # El ID (entero) debería entrar.
    else:
        txtexcp = "ventana_generica::casar -> %s no es de un tipo válido" % (
                    columna)
        raise TypeError, txtexcp
    return res

def humanizar(valor, columna):
    """
    Devuelve el valor convertido a una cadena legible y amigable para el 
    usuario.
    «columna» se usa solo para mostrar un valor legible en las claves ajenas.
    """
    if isinstance(columna, pclases.SOForeignKey):
        try:
            valor = getattr(pclases, columna.foreignKey).get(valor).get_info()
        except AssertionError:  # valor no es un id. Debe ser None.
            valor = None
    res = valor
    if isinstance(valor, datetime.date):
        res = utils.fecha.str_fecha(valor)
    elif isinstance(valor, datetime.datetime):
        res = utils.fecha.str_fechahora(valor)
    #elif isinstance(valor, float):
    #    res = utils.numero.float2str(valor, 2)
    elif res == None:
        res = ""
    return res

if __name__ == "__main__":
    import sys
    glade = sys.argv[1]
    if not glade.endswith(".glade"):
        glade += ".glade"
    clase = camelize(glade.replace(".glade", "").title())
    VentanaGenerica(clase = clase, run = True, ventana_marco = glade)

