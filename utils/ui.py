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

    Algunas utilidades relacionadas con la interfaz de usuario.

'''

import pygtk
pygtk.require('2.0')
import gtk, gobject, os
import fecha, numero
from cadena import eliminar_dobles_espacios
import time, datetime
from gettext import gettext as _
from gettext import bindtextdomain, textdomain                                  
bindtextdomain("cican", 
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "l10n")))
textdomain("cican")


def escribir_barra_estado(wid, texto, logger = None, txt_log = ""):
    """
    Escribe el texto "texto" en la barra de estado "wid".
    Los parámetros adicionales "logger" y "txt_log" son un 
    objeto para volcar a log y un texto adicional. Típicamente el 
    texto adicional incluye información acerca del usuario 
    que ha hecho «login» en el sistema y "logger" vendrá heredado 
    e instanciado desde la clase Ventana y Autenticación 
    respectivamente.
    """
    texto = eliminar_dobles_espacios(texto)
    wid.push(wid.get_context_id(texto), texto)
    if logger != None:
        if "error" in txt_log.lower():
            logger.error("%s: %s" % (txt_log, texto))
        else:
            logger.warning("%s: %s" % (txt_log, texto))

def respuesta_si_no(dialog, response, res):
    res[0] = response == gtk.RESPONSE_YES

def respuesta_si_no_cancel(dialog, response, res):
    if response == gtk.RESPONSE_YES:
        res[0] = True
    elif response == gtk.RESPONSE_NO:
        res[0] = False
    else:
        res[0] = response

def dialogo(texto = '', 
            titulo = '', 
            padre = None, 
            icono = None, 
            cancelar = False, 
            defecto = None, 
            tiempo = None, 
            recordar = False, 
            res_recordar = [False], 
            bloq_temp = []):
    """
    Muestra un diálogo SI/NO.
    Devuelve True si se pulsó SI y False si no.
    OJO: Aquí va primero el texto y después el título para
    guardar la compatibilidad con el código del resto de 
    módulos ya escritos. En el resto de utils el titulo 
    es el primer parámetro.
    Si icon tiene algo != None (debe ser un gtk.STOCK_algo)
    se agrega un icono a la izquierda del texto.
    Si cancelar != False, se añade un botón cancelar que 
    devuelve gtk.RESPONSE_CANCEL cuando se pulsa.
    Si «recordar» es True muestra un checkbox de "No volver a preguntar" que 
    por defecto está a «res_recordar», donde guarda el valor final del 
    checkbox al pulsar Aceptar.
    bloq_temp es una lista de botones que se deshabilitarán durante 3 
    segundos para evitar que al usuario-cowboy se le vaya la mano y forzarlo 
    a leer el texto antes de que haga algo "peligroso" sin querer (al estilo 
    Firefox para instalaciones de plugins y demás). 
    La lista debe contener cadenas de texto de los botones que se desean 
    deshabilitar de manera análoga a como se recibe la respuesta por defecto.
    """
    ## HACK: Los enteros son inmutables, usaré una lista
    res = [None]
    if cancelar:
        de = gtk.Dialog(titulo,
                        padre,
                        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                        (gtk.STOCK_YES, gtk.RESPONSE_YES,
                        gtk.STOCK_NO, gtk.RESPONSE_NO,
                        gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        de.connect("response", respuesta_si_no_cancel, res)
    else: 
        de = gtk.Dialog(titulo,
                        padre,
                        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                        (gtk.STOCK_YES, gtk.RESPONSE_YES,
                        gtk.STOCK_NO, gtk.RESPONSE_NO))
        de.connect("response", respuesta_si_no, res)
    response_defecto = gtk.RESPONSE_YES
    if defecto != None:
        if defecto in ("cancelar", "cancel", "CANCELAR", "CANCEL", 
                       gtk.RESPONSE_CANCEL):
            de.set_default_response(gtk.RESPONSE_CANCEL)
            response_defecto = gtk.RESPONSE_CANCEL
        elif defecto in ("no", "No", "NO", False, gtk.RESPONSE_NO):
            de.set_default_response(gtk.RESPONSE_NO)
            response_defecto = gtk.RESPONSE_NO
        elif defecto in ("si", "Si", "SI", True, gtk.RESPONSE_YES, "yes", 
                         "Yes", "YES", "sí", "Sí", "SÍ"):
            de.set_default_response(gtk.RESPONSE_YES)
            response_defecto = gtk.RESPONSE_YES
    de.response_defecto = response_defecto # I love this dynamic shit!
    txt = gtk.Label("\n    %s    \n" % texto)
    if icono == None:
        icono = gtk.STOCK_DIALOG_QUESTION
    pixbuf = de.render_icon(icono, gtk.ICON_SIZE_MENU)
    de.set_icon(pixbuf)
    imagen = gtk.Image()
    imagen.set_from_stock(icono, gtk.ICON_SIZE_DIALOG)
    hbox = gtk.HBox(spacing = 5)
    hbox.pack_start(imagen)
    hbox.pack_start(txt)
    de.vbox.pack_start(hbox)
    de.vbox.show_all()
    de.set_transient_for(padre)
    de.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
    # Checkbox de no volver a preguntar.
    if recordar:
        txtrecordar = "_Recordar mi respuesta y no volver a preguntar."
        chrecordar = gtk.CheckButton(txtrecordar)
        chrecordar.set_active(bool(res_recordar and res_recordar[0] or False))
        chrecordar.set_property("can-default", False)
        chrecordar.set_property("can-focus", False)
        de.vbox.add(chrecordar)
        chrecordar.show()
        def guardar_recordar(cb, res_recordar):
            try:
                res_recordar[0] = cb.get_active()
            except IndexError:
                res_recordar.append(cb.get_active())
        chrecordar.connect("toggled", guardar_recordar, res_recordar)
    # Tiempo por defecto:
    if tiempo != None:
        tiempo_restante = [tiempo]   # Enteros son inmutables, uso una 
            # lista para poder cambiar el valor dentro del callback.
        label_tiempo = gtk.Label("<small><i>La opción por defecto será aplicada en %d segundos.</i></small>" % tiempo_restante[0])
        label_tiempo.set_use_markup(True)
        def actualizar_tiempo_restante(label, dialogo, tiempo, 
                                       response_defecto):
            tiempo[0] -= 1
            label_tiempo.set_text("<small><i>La opción por defecto será aplicada en %d segundos.</i></small>" % tiempo[0])
            label_tiempo.set_use_markup(True)
            if tiempo[0] <= 0:
                de.response(response_defecto)
            return tiempo[0] > 0
        de.vbox.add(label_tiempo)
        label_tiempo.show()
        gobject.timeout_add(1000, actualizar_tiempo_restante, label_tiempo, 
                            de, tiempo_restante, response_defecto, 
                            priority = gobject.PRIORITY_HIGH)
    # Bloqueo temporal de botones:
    if bloq_temp:
        # 0.- Diccionario de botones
        area = de.action_area
        pares = zip(("sí", "no", "cancelar"), 
                    area.get_children()[::-1])   # Siempre mismo orden.
        dbotones = dict(pares)
    for strb in bloq_temp:
        # 1.- Determinar a qué botón se refiere:
        if strb in ("cancelar", "cancel", "CANCELAR", "CANCEL", 
                       gtk.RESPONSE_CANCEL):
            try:
                boton = dbotones["cancelar"]
            except KeyError:
                continue # No hay botón de cancelar.
        elif strb in ("no", "No", "NO", False, gtk.RESPONSE_NO):
            boton = dbotones["no"]
        elif strb in ("si", "Si", "SI", True, gtk.RESPONSE_YES, "yes", 
                         "Yes", "YES", "sí", "Sí", "SÍ"):
            boton = dbotones["sí"]
        else:
            continue
        # 2.- Instalo la cuenta atrás.
        boton.set_sensitive(False)
        tiempo_restante = [3]   # Enteros son inmutables, uso una 
            # lista para poder cambiar el valor dentro del callback.
        label = boton.get_children()[0].get_child().get_children()[1]
        str_label = label.get_text()
        if "(" in str_label:
            str_label = str_label.split("(")[0][:-1]
        strtiempo = str_label + "<small> (%d)</small>" % tiempo_restante[0]
        label.set_text(strtiempo)
        label.set_use_markup(True)
        def actualizar_tiempo_restante(boton, tiempo, dialogo, botones):
            tiempo[0] -= 1
            boton.set_sensitive(tiempo[0] <= 0)
            try:
                label = boton.get_children()[0].get_child().get_children()[1]
            except IndexError:  # El diálogo se ha cerrado ya.
                return False
            str_label = label.get_text()
            if "(" in str_label:
                str_label = str_label.split("(")[0][:-1]
            if tiempo[0] > 0:
                strtiempo = str_label + "<small> (%d)</small>" % tiempo[0]
            else:
                strtiempo = str_label
                if dialogo.response_defecto == gtk.RESPONSE_YES:
                    dbotones["sí"].grab_focus()
                elif dialogo.response_defecto == gtk.RESPONSE_NO:
                    dbotones["no"].grab_focus()
                elif dialogo.response_defecto == gtk.RESPONSE_CANCEL:
                    dbotones["cancelar"].grab_focus()
            label.set_text(strtiempo)
            label.set_use_markup(True)
            return tiempo[0] > 0
        gobject.timeout_add(1000, actualizar_tiempo_restante, 
                            boton, tiempo_restante, de, dbotones, 
                            priority = gobject.PRIORITY_HIGH)
    de.run()
    de.destroy()
    return res[0]

def respuesta_ok_cancel(dialog, response, res):
    if response == gtk.RESPONSE_OK:
        try:
            res[0] = dialog.vbox.get_children()[1].get_text()
        except:
            buf = dialog.vbox.get_children()[1].get_buffer()
            res[0] = buf.get_text(buf.get_start_iter(), buf.get_end_iter())
    else:
        res[0] = False

def set_unset_urgency_hint(window, activar_hint):
    if gtk.gtk_version >= (2, 8, 0) and gtk.pygtk_version >= (2, 8, 0):
        if activar_hint > 0:
            window.props.urgency_hint = True
        else:
            window.props.urgency_hint = False

def dialogo_info(titulo='', texto='', padre=None):
    """
    Muestra un diálogo simple de información, con un único
    botón de aceptación.
    OJO: Al loro. Si el título de la ventana es "ACTUALIZAR" no 
    se muestra. En cambio se activa el hint que hace parpadear
    la ventana padre. El urgency_hint se desactivará cuando
    pulse en Actualizar o en Guardar (es decir, cuando se 
    invoque actualizar_ventana). NOTA: Esto se hace aquí para
    evitar cambiar una por una las docenas de ventanas de diálogo 
    de actualización que hay repartidas por cada formulario.
    """
    if titulo == "ACTUALIZAR":
        if padre != None:
            set_unset_urgency_hint(padre, True)
    else:
        dialog = gtk.Dialog(titulo,
                            padre,
                            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                            (gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        info = gtk.Label("\n    %s    \n" % texto)
        info.set_use_markup(True)
        hbox = gtk.HBox(spacing = 5)
        icono = gtk.Image()
        icono.set_from_stock(gtk.STOCK_DIALOG_INFO, gtk.ICON_SIZE_DIALOG)
        hbox.pack_start(icono)
        hbox.pack_start(info)
        dialog.vbox.pack_start(hbox)
        hbox.show_all()
        dialog.set_transient_for(padre)
        dialog.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
        insertar_boton_copiar_al_portapapeles(dialog, texto)
        dialog.set_default_response(gtk.RESPONSE_ACCEPT)
        dialog.run()
        dialog.destroy()

def insertar_boton_copiar_al_portapapeles(dialog, texto):
    """
    Inserta en el diálogo el botón para copiar al portapapeles el texto 
    recibido.
    """
    #boton_copiar = gtk.Button(stock = gtk.STOCK_COPY)
    boton_copiar = gtk.Button()
    i = gtk.Image()
    i.set_from_stock(gtk.STOCK_COPY, gtk.ICON_SIZE_BUTTON)
    boton_copiar.set_image(i)
    boton_copiar.set_property("tooltip-text", _("Copiar al portapapeles"))
    boton_copiar.show()
    a = dialog.get_action_area()
    a.pack_start(boton_copiar)
    a.reorder_child(boton_copiar, 0)
    boton_copiar.connect("clicked", 
                         lambda boton: copiar_al_portapapeles(texto))
 

def dialogo_entrada(texto= '', 
                    titulo = 'ENTRADA DE DATOS', 
                    valor_por_defecto = '', 
                    padre = None, 
                    pwd = False, 
                    modal = True, 
                    textview = False, 
                    opciones = {}):
    """
    Muestra un diálogo modal con un textbox.
    Devuelve el texto introducido o None si se
    pulsó Cancelar.
    valor_por_defecto debe ser un string.
    Si pwd == True, es un diálogo para pedir contraseña
    y ocultará lo que se introduzca.
    Si textview es True usa un TextView en lugar de un TextEntry.
    opciones: Se añadirán tantos checkboxes a la ventana como elementos 
              se reciban en este parámetros. Cada clave será el texto a usar 
              en los checkboxes y los valores serán los valores por defecto. 
              En ese mismo diccionario se almacenarán los valores 
              seleccionados en el diálogo tras darle a Aceptar.
    """
    if not isinstance(valor_por_defecto, str):
        valor_por_defecto = str(valor_por_defecto)
    ## HACK: Los enteros son inmutables, usaré una lista
    res = [None]
    if modal:
        de = gtk.Dialog(titulo,
                        padre,
                        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                        (gtk.STOCK_OK, gtk.RESPONSE_OK,
                         gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
    else:
        de = gtk.Dialog(titulo,
                        padre,
                        gtk.DIALOG_DESTROY_WITH_PARENT,
                        (gtk.STOCK_OK, gtk.RESPONSE_OK,
                         gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
    de.connect("response", respuesta_ok_cancel, res)
    txt = gtk.Label("\n    %s    \n" % texto)
    txt.set_use_markup(True)
    hbox = gtk.HBox(spacing = 5)
    icono = gtk.Image()
    icono.set_from_stock(gtk.STOCK_DIALOG_QUESTION, gtk.ICON_SIZE_DIALOG)
    hbox.pack_start(icono)
    hbox.pack_start(txt)
    de.vbox.pack_start(hbox)
    vboxopciones = gtk.VBox()
    #------------------------------------------------------------------------#
    def set_opcion(cb, claveopcion, opciones):                               #
        opciones[claveopcion] = cb.get_active()                              #
    #------------------------------------------------------------------------#
    for txtopcion in opciones:
        chbox = gtk.CheckButton(txtopcion)
        chbox.set_active(opciones[txtopcion])
        chbox.connect("toggled", set_opcion, txtopcion, opciones)
        vboxopciones.add(chbox)
    vboxopciones.show_all()
    de.vbox.pack_end(vboxopciones)
    hbox.show_all()
    if not textview:
        input = gtk.Entry()
        input.set_visibility(not pwd)
        #-----------------------------------------------------------#
        def pasar_foco(widget, event):                              #
            if event.keyval == 65293 or event.keyval == 65421:      #
                de.action_area.get_children()[1].grab_focus()       #
        #-----------------------------------------------------------#
        input.connect("key_press_event", pasar_foco)
    else:
        input = gtk.TextView()
    de.vbox.pack_start(input)
    input.show()
    if not textview:
        input.set_text(valor_por_defecto)
    else:
        input.get_buffer().set_text(valor_por_defecto)
    if len(titulo)<20:
        width = 100
    elif len(titulo)<60:
        width = len(titulo)*10
    else:
        width = 600
    de.resize(width, 80)
    de.set_transient_for(padre)
    de.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
    de.run()
    de.destroy()
    if res[0]==False:
        return None
    return res[0]

def dialogo_combo(titulo='Seleccione una opción', 
                  texto='', 
                  opciones=[(0, 'Sin opciones')], 
                  padre=None, 
                  valor_por_defecto = None):
    """
    Muestra un diálogo modal con un combobox con las opciones
    pasadas.
    Las opciones deben ser (int, str)
    Devuelve el elemento seleccionado[0] -el entero de la 
    opción- o None si se cancela.
    Si valor_por_defecto != None, debe ser un entero de la lista.
    """
    ## HACK: Los enteros son inmutables, usaré una lista
    res = [None]
    de = gtk.Dialog(titulo,
                    padre,
                    gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                    (gtk.STOCK_OK, gtk.RESPONSE_OK,
                     gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
    #-------------------------------------------------------------------#
    def respuesta_ok_cancel_combo(dialog, response, res):               #
        if response == gtk.RESPONSE_OK:                                 #
            res[0] = combo_get_value(dialog.vbox.get_children()[1])     #
        else:                                                           #
            res[0] = False                                              #
    #-------------------------------------------------------------------#
    def pasar_foco(completion, model, iter):                            #
        de.action_area.get_children()[1].grab_focus()                   #
    #-------------------------------------------------------------------#
    de.connect("response", respuesta_ok_cancel_combo, res)
    txt = gtk.Label("\n    %s    \n" % texto)
    combo = gtk.ComboBoxEntry()
    rellenar_lista(combo, opciones)
    if valor_por_defecto != None and isinstance(valor_por_defecto, int) and valor_por_defecto in [o[0] for o in opciones]:
        model = combo.get_model()
        iter = model.get_iter_first()
        while (iter != None and 
               model[model.get_path(iter)][0] != valor_por_defecto):
            iter = model.iter_next(iter)
        combo.set_active_iter(iter)
    input = combo.child.get_completion()
    input.connect("match_selected", pasar_foco)
    hbox = gtk.HBox(spacing = 5)
    icono = gtk.Image()
    icono.set_from_stock(gtk.STOCK_DIALOG_QUESTION, gtk.ICON_SIZE_DIALOG)
    hbox.pack_start(icono)
    hbox.pack_start(txt)
    hbox.show_all()
    de.vbox.pack_start(hbox)
    combo.show()
    de.vbox.pack_start(combo)
    de.set_transient_for(padre)
    de.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
    de.run()
    de.destroy()
    if res[0] is False:
        res = None
    else:
        res = res[0]
    return res

def dialogo_radio(titulo='Seleccione una opción', 
                  texto='', 
                  ops=[(0, 'Sin opciones')], 
                  padre=None, 
                  valor_por_defecto = None):
    """
    Muestra un diálogo modal con un grupo de radiobuttons con las opciones 
    pasadas.
    Las opciones deben ser (int, str)
    Devuelve el elemento seleccionado[0] -el entero de la 
    opción- o None si se cancela.
    Si valor_por_defecto != None, debe ser un entero de la lista.
    """
    ## HACK: Los enteros son inmutables, usaré una lista
    res = [None]
    de = gtk.Dialog(titulo,
                    padre,
                    gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                    (gtk.STOCK_OK, gtk.RESPONSE_OK,
                     gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
    #-------------------------------------------------------------------#
    def respuesta_ok_cancel_radio(dialog, response, res, dicseleccion):
        res[0] = False
        if response == gtk.RESPONSE_OK:
            for numop in dicseleccion:
                if dicseleccion[numop].get_active():
                    res[0] = numop
                    break
    #-------------------------------------------------------------------#
    txt = gtk.Label("\n    %s    \n" % texto)
    vradio = gtk.VBox()
    dicseleccion = {}
    grupo = None
    for numop, txtop in ops:
        rb = gtk.RadioButton(grupo, label = txtop)
        if grupo == None:
            grupo = rb
        vradio.add(rb)
        dicseleccion[numop] = rb
    if (valor_por_defecto != None 
        and isinstance(valor_por_defecto, int) 
        and valor_por_defecto in [o[0] for o in ops]):
        dicseleccion[valor_por_defecto].set_active(True)
    de.connect("response", respuesta_ok_cancel_radio, res, dicseleccion)
    hbox = gtk.HBox(spacing = 5)
    icono = gtk.Image()
    icono.set_from_stock(gtk.STOCK_DIALOG_QUESTION, gtk.ICON_SIZE_DIALOG)
    hbox.pack_start(icono)
    hbox.pack_start(txt)
    hbox.show_all()
    de.vbox.pack_start(hbox)
    vradio.show_all()
    de.vbox.pack_start(vradio)
    de.set_transient_for(padre)
    de.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
    de.run()
    de.destroy()
    if res[0] is False:
        res = None
    else:
        res = res[0]
    return res

def dialogo_entrada_combo(titulo='Seleccione una opción', 
                          texto='', 
                          ops=[(0, 'Sin opciones')], 
                          padre=None, 
                          valor_por_defecto = None):
    """
    Muestra un diálogo modal con un combobox con las opciones
    pasadas.
    Las opciones deben ser (int, str)
    Devuelve el par seleccionado de las opciones, (None, None) si
    se cancela o (None, "texto escrito") si se ha tecleado algo
    que no está en las opciones y se ha pulsado Aceptar.
    Si valor_por_defecto != None, debe ser un entero de la lista.
    """
    ## HACK: Los enteros son inmutables, usaré una lista
    res = [None, None]
    de = gtk.Dialog(titulo,
                    padre,
                    gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                    (gtk.STOCK_OK, gtk.RESPONSE_OK,
                     gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
    #-------------------------------------------------------------------#
    def respuesta_ok_cancel_combo(dialog, response, res):
        if response == gtk.RESPONSE_OK:
            combo = dialog.vbox.get_children()[1]
            res[0] = combo_get_value(combo)
            res[1] = combo.child.get_text()
        else:
            res[0] = False
            res[1] = None
    #-------------------------------------------------------------------#
    def pasar_foco(completion, model, iter):                            #
        de.action_area.get_children()[1].grab_focus()                   #
    #-------------------------------------------------------------------#
    de.connect("response", respuesta_ok_cancel_combo, res)
    txt = gtk.Label("\n    %s    \n" % texto)
    combo = gtk.ComboBoxEntry()
    rellenar_lista(combo, ops)
    if valor_por_defecto != None \
       and isinstance(valor_por_defecto, int) \
       and valor_por_defecto in [o[0] for o in ops]:
        model = combo.get_model()
        iter = model.get_iter_first()
        while iter != None \
              and model[model.get_path(iter)][0] != valor_por_defecto:
            iter = model.iter_next()
        combo.set_active_iter(iter)
    input = combo.child.get_completion()
    input.connect("match_selected", pasar_foco)
    hbox = gtk.HBox(spacing = 5)
    icono = gtk.Image()
    icono.set_from_stock(gtk.STOCK_DIALOG_QUESTION, gtk.ICON_SIZE_DIALOG)
    hbox.pack_start(icono)
    hbox.pack_start(txt)
    hbox.show_all()
    de.vbox.pack_start(hbox)
    combo.show()
    de.vbox.pack_start(combo)
    de.set_transient_for(padre)
    de.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
    de.run()
    de.destroy()
    if res[0] is False:
        res[0] = None
    return res

def combo_get_value(widget):
    """
    Devuelve el valor actual de la primera columna
    del elemento del model que se corresponde con 
    el activo en el widget.
    Si el model está vacío o no hay elemento
    activo, devuelve None.
    """
    list_model = widget.get_model()
    iter = widget.get_active_iter()
    try:
        return list_model.get_value(iter, 0)
    except TypeError:  # iter es None en vez de un GtkTreeIter
        return None

def rellenar_lista(wid, textos):
    """ 
    Crea, rellena y asocia al model de un combobox
    el ListStore que se creará a partir de una lista o
    tupla de (enteros, cadenas). La cadena que se mostrará
    en el combo es la columna 1. La columna 0 es un 
    entero y -generalmente- será el id del elemento en 
    la BD.
    Versión castiza y con autocompletado -si el combo
    lo permite y tiene un .child entry- de la
    función anterior.
    """
    model = gtk.ListStore(int, str)
    for t in textos:
        model.append(t)
    cb = wid
    cb.set_model(model)
    if type(cb) is gtk.ComboBoxEntry:
        # HACK: Para evitar un "assert - GtkWarning" en posteriores llamadas.
        if cb.get_text_column()==-1:    
            cb.set_text_column(1)
        completion = gtk.EntryCompletion()
        completion.set_model(model)
        wid.child.set_completion(completion)
        #-------------------------------------------------------#
        # Assumes that the func_data is set to the number of    #
        # the text column in the model.                         #
        def match_func(completion, key, iter, (column, entry)): #
            model = completion.get_model()                      #
            text = model.get_value(iter, column)                #
            # if text.startswith(key):                          #
            #     return True                                   #
            # return False                                      #
            if text == None:                                    #
                return False                                    #
            key = entry.get_text()                              #
            try:                                                #
                key = unicode(key, "utf").lower()               #
            except:                                             #
                key = key.lower()                               #
            try:                                                #
                text = unicode(text, "utf").lower()             #
            except:                                             #
                text = text.lower()                             #
            try:                                                #
                return key in text                              #
            except:                                             #
                # Error de codificación casi seguro.            #
                print key                                       #
                print text                                      #
                return False                                    #
        #-------------------------------------------------------#
        completion.set_text_column(1)
        completion.set_match_func(match_func, (1, wid.child))
        # completion.set_minimum_key_length(2)
        # completion.set_inline_completion(True)
        #---------------------------------------------------#
        def iter_seleccionado(completion, model, iter):     #
            combo_set_from_db(wid, model[iter][0])          #
        #---------------------------------------------------#
        completion.connect('match-selected', iter_seleccionado)
    elif type(cb) is gtk.ComboBox:
        cb.clear()  # Limpia posibles cells anteriores por si se ha llamado 
                    # a rellenar_lista más de una vez en el mismo widget..
        cell = gtk.CellRendererText()
        cb.pack_start(cell, True)
        cb.add_attribute(cell, 'text', 1)

def combo_set_from_db(combo_widget, db_item, numcol_a_comparar = 0):
    """
    Establece como elemento activo de un widget
    el elemento del model correspondiente con 
    el db_item. Para las comparaciones usa la
    primera columna del model, el db_item por
    tanto debe ser el valor en la BD del campo
    que se corresponda con esa columna (por lo 
    general debería ser un id).
    NO acepta tuplas completas.
    """
    list_model = combo_widget.get_model()
    iter = list_model.get_iter_first()
    while (iter != None 
            and list_model.get_value(iter, numcol_a_comparar) != db_item):
        iter = list_model.iter_next(iter)
    if iter == None: # No estaba el db_item en el model.
        combo_widget.set_active(-1)     # Por si es un comboBoxEntry
        try:
            combo_widget.child.set_text("")
        except:
            pass
    else:
        combo_widget.set_active_iter(iter)

def preparar_treeview(tv, cols, multi = False):
    """
    Prepara el model con las columnas recibidas y 
    lo asocia al treeview mediante una TREESTORE.
    Las columnas deben tener el formato:
    (('Nombre', 'gobject.tipo', editable, ordenable, buscable, funcion, 
      parámetros adicionales a la función), ... )
    Sólo puede haber una columna buscable.
    Si editable == True, función no debe ser None y será conectada.
    Si multi es True (por defecto no lo es) el TreeView será de selección 
    múltiple.
    Al gobject de cada columna le asigna una clave propia llamada 'q_ncol' 
    que guarda la columna (comenzando por 0) que le corresponde en el model.
    Estoy completamente seguro de que pygtk debe tener algo parecido, pero 
    llevo toda la mañana buceando en la documentación y el código fuente y no 
    lo encuentro. La utilidad fundamental es que si el usuario reordena las 
    columnas, siempre puedo saber la posición original de los datos del model 
    que se están mostrando. En otro caso, el orden de los datos de las 
    columnas en el model y en el TreeView no coinciden y no encontraría la 
    manera de saber quién es quién.
    """
    tipos = [c[1].replace("TYPE_FLOAT", "TYPE_DOUBLE") for c in cols]
    model = eval('gtk.TreeStore(%s)' % ','.join(tipos)) 
    # No encuentro otra forma de hacerlo. Sorry.
    tv.set_model(model)
    # Quito la columna que no hay que mostrar:
    cols = cols[:-1]
    columns = []
    for header in [c[0] for c in cols]:
        columns.append(gtk.TreeViewColumn(header))
    for c in columns:
        # Experimental
        #c.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        c.set_resizable(True)
        c.set_reorderable(True)
        # EOExperimental
        tv.append_column(c)
    i = 0
    #for t, e, o, b, f in [(c[1:]) for c in cols]:
    for col in [(c[1:]) for c in cols]:
        try:
            t, e, o, b, f, func_params = col
            if not isinstance(func_params, (list, tuple)):
                func_params = [func_params]
        except ValueError: 
            t, e, o, b, f = col
            func_params = []
        if t == 'gobject.TYPE_BOOLEAN':
            cell = gtk.CellRendererToggle()
            cell.set_property("activatable", e)
            columns[i].pack_start(cell, True)
            columns[i].add_attribute(cell, 'active', i)
            if e and f!=None:
                cell.connect("toggled", f, *func_params)
            if o:
                columns[i].set_sort_column_id(i)
            if b:
                tv.set_search_column(i)
        elif t == 'gobject.TYPE_FLOAT' or t == 'gobject.TYPE_DOUBLE':
            cell = gtk.CellRendererText()
            cell.set_property("editable", e) 
            columns[i].pack_start(cell, True)
            columns[i].add_attribute(cell, 'text', i)
            columns[i].set_cell_data_func(cell, 
                redondear_flotante_en_cell_cuando_sea_posible, i)
            cell.set_property('xalign', 1.0)
            if e and f!=None:
                cell.connect("edited", f, *func_params)
            if o:
                columns[i].set_sort_column_id(i)
            if b:
                tv.set_search_column(i)
        else:
            cell = gtk.CellRendererText()
            cell.set_property("editable", e)
            columns[i].pack_start(cell, True)
            columns[i].add_attribute(cell, 'text', i)
            if e and f!=None:
                cell.connect("edited", f, *func_params)
            if o:
                model.set_sort_func(i, funcion_orden, i)
                columns[i].set_sort_column_id(i)
            if b:
                tv.set_search_column(i)
            if t == 'gobject.TYPE_INT' or t == 'gobject.TYPE_INT64':
                cell.set_property('xalign', 1.0)
        columns[i].set_data("q_ncol", i)
        i += 1
    for c in columns:
        # Experimental
        #c.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        c.set_resizable(True)
        c.set_reorderable(True)
        # EOExperimental
    if multi:
        tv.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
    else:
        tv.get_selection().set_mode(gtk.SELECTION_SINGLE)

def preparar_listview(tv, cols, multi = False):
    """
    Prepara el model con las columnas recibidas y 
    lo asocia al treeview mediante una LISTSTORE.
    Las columnas deben tener el formato:
    (('Nombre', 'gobject.tipo', editable, ordenable, buscable, funcion, 
      parámetros), ... )
    Sólo puede haber una columna buscable.
    Si editable == True, función no debe ser None y será conectada.
    Si «multi» es True hace el TreeView de selección multiple.
    Al gobject de cada columna le asigna una clave propia llamada 'q_ncol' 
    que guarda la columna (comenzando por 0) que le corresponde en el model.
    Estoy completamente seguro de que pygtk debe tener algo parecido, pero 
    llevo toda la mañana buceando en la documentación y el código fuente y no 
    lo encuentro. La utilidad fundamental es que si el usuario reordena las 
    columnas, siempre puedo saber la posición original de los datos del model 
    que se están mostrando. En otro caso, el orden de los datos de las 
    columnas en el model y en el TreeView no coinciden y no encontraría la 
    manera de saber quién es quién.
    """
    tipos = [c[1].replace("TYPE_FLOAT", "TYPE_DOUBLE") for c in cols]
    model = eval('gtk.ListStore(%s)' % ','.join(tipos)) 
    # No encuentro otra forma de hacerlo. Sorry.
    tv.set_model(model)
    # Quito la columna que no hay que mostrar:
    cols = cols[:-1]
    columns = [None] * len(cols)
    i = 0
    for col in cols:
        try:
            h, t, e, o, b, f, func_params = col
            if not isinstance(func_params, (list, tuple)):
                func_params = [func_params]
        except ValueError: 
            h, t, e, o, b, f = col
            func_params = []
        if t == 'gobject.TYPE_BOOLEAN':
            cell = gtk.CellRendererToggle()
            cell.set_property("activatable", e)
            columns[i] = gtk.TreeViewColumn(h, cell) 
            columns[i].add_attribute(cell, 'active', i)
            if e and f!=None:
                cell.connect("toggled", f, *func_params)
            if o:
                columns[i].set_sort_column_id(i)
            if b:
                tv.set_search_column(i)
            tv.insert_column(columns[i], -1)
        elif t == 'gobject.TYPE_FLOAT' or t == 'gobject.TYPE_DOUBLE':
            cell = gtk.CellRendererText()
            cell.set_property("editable", e) 
            columns[i] = gtk.TreeViewColumn(h, cell, text = i) 
            if e and f!=None:
                cell.connect("edited", f, *func_params)
            if b:
                tv.set_search_column(i)
            cell.set_property('text', i)
            tv.insert_column_with_data_func(
                -1, h, cell, 
                redondear_flotante_en_cell_cuando_sea_posible, i)
            cell.set_property('xalign', 1.0)
            if o:
                columns[i].set_sort_column_id(i)
        else:
            cell = gtk.CellRendererText()
            cell.set_property("editable", e)
            columns[i] = gtk.TreeViewColumn(h, cell) 
            columns[i].add_attribute(cell, 'text', i)
            if e and f != None:
                cell.connect("edited", f, *func_params)
            if o:
                model.set_sort_func(i, funcion_orden, i)
                columns[i].set_sort_column_id(i)
            if b:
                tv.set_search_column(i)
            if t == 'gobject.TYPE_INT' or t == 'gobject.TYPE_INT64':
                cell.set_property('xalign', 1.0)
            tv.insert_column(columns[i], -1)
        columns[i].set_data("q_ncol", i)
        i += 1
    for c in columns:
        # Experimental
        #c.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        c.set_resizable(True)
        c.set_reorderable(True)
        # EOExperimental
    if multi:
        tv.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
    else:
        tv.get_selection().set_mode(gtk.SELECTION_SINGLE)

def redondear_flotante_en_cell_cuando_sea_posible(column, 
                                                  cell, 
                                                  model, 
                                                  iter, 
                                                  data):
    if isinstance(data, int):
        i = data
        numdecimales = 2
    else:
        i, numdecimales = data
    contenido = model[iter][i]
    if isinstance(contenido, float):
        expresion = "%%.%df" % numdecimales
        numredondo = numero.float2str(expresion % contenido, numdecimales)
        cell.set_property('text', numredondo)

def funcion_orden(model, iter1, iter2, columna):
    """
    Función para ordenar la columna "columna" de un TreeView.
    Si es fecha ordena por día/mes/año. 
    Si es número, compara como número -acepta enteros y flotantes-.
    Si no es fecha (no contiene dos '/') ni número usa el orden 
    predefinido por python para cadenas.
    """
    dato1 = model[iter1][columna]
    dato2 = model[iter2][columna]
    if es_interpretable_como_numero(dato1) and es_interpretable_como_numero(dato2):
        res = comparar_como_numeros(dato1, dato2)
    elif es_interpretable_como_fecha(dato1) and es_interpretable_como_fecha(dato2):
        res = fecha.comparar_como_fechas(dato1, dato2)
    elif es_interpretable_como_fechahora(dato1) and es_interpretable_como_fechahora(dato2):
        res = fecha.comparar_como_fechahora(dato1, dato2)
    elif isinstance(dato1, str) and isinstance(dato2, str):
        res = (dato1.upper() < dato2.upper() and -1) or (dato1.upper() > dato2.upper() and 1) or 0
    else:
        if dato1 < dato2:
            res = -1
        elif dato1 > dato2:
            res = 1
        else:
            res = 0
    return res

def es_interpretable_como_numero(n):
    """
    Devuelve True si "n" se puede interpretar como número.
    """
    if numero.convertir_a_numero(n) != None:
        res = True
    else:
        res = False
    return res

def es_interpretable_como_fechahora(f):
    """
    Devuelve True si f se puede convertir a fecha.
    """
    if fecha.convertir_a_fechahora(f) != None:
        res = True
    else:
        res = False
    return res

def es_interpretable_como_fecha(f):
    """
    Devuelve True si f se puede convertir a fecha.
    """
    if fecha.convertir_a_fecha(f) != None:
        res = True
    else:
        res = False
    return res

def dialogo_resultado(filas, 
                      titulo='', 
                      padre=None, 
                      cabeceras=['Id', 'Código', 'Descripción'], 
                      multi=False,
                      func_change=lambda *args, **kwargs: None, 
                      maximizar = False, 
                      defecto = []):
    """
    Muestra un cuadro de diálogo modal con una tabla. En
    la tabla se mostrarán tantas filas como items pasados
    en el parámetro filas.
    Devuelve el índice de la fila a la que se haga clic
    (en realidad, valor de la primera columna)
    con el ratón o -1 si se pulsó Cancelar.
    Devuelve -2 si filas no es una lista de resultados.
    En las cabeceras de las columnas se mostrará el texto de 
    la lista que se pase en el parámetro "cabeceras" de forma
    consecutiva. Si la longitud de "cabeceras" es menor que el
    número de columnas de la lista de filas, las TreeViewColumns
    restantes se quedarán con una descripción en blanco ('').
    La columna de búsqueda será siempre -de momento- la 
    segunda (elemento 1 de columns).
    Si multi es True, el TreeView del diálogo será de selección
    múltiple (gtk.SELECTION_MULTIPLE) y devolverá una lista de 
    índices seleccionados o una lista cuyo primer elemento es 
    -1 si ha cancelado.
    func_change es una función que se ejecutará cada vez que 
    el cursor cambie de fila activa en el treeview de resultados. 
    Debe estar preparada para recibir el TreeView como parámetro.
    defecto es una lista de índices por defecto que aparecerán 
    marcados. Si multi es False, solo se tendrá en cuenta el primero 
    de ellos (si lo hay). Los índices se refieren a la lista de valores
    recibidos en el parámetro "filas", que coinciden con el orden de 
    las filas en el model del TreeView. 
    """
    # DONE: No sé si pasa solo en el equipo de desarrollo o también en 
    #       producción. No me he dado cuenta hasta ahora. El valor 
    #       que devuelve normalmente es un ID y debería ser de tipo entero. 
    #       Sin embargo devuelve el número como string. ¿Por qué?
    #       -> Ve al construir tabla y de ahí al tipo_gobject y lee los 
    #       comentarios. Se hace así porque a veces vienen textos y cadenas 
    #       en la misma columna y petaba. Como todo entra bien por un string 
    #       a la hora de mostrar datos en el TreeView, uso string incluso 
    #       para columnas de enteros y dejo después que se haga el cast donde 
    #       caiga.
    res = [-1]
    numero.el_reparador_magico_de_representacion_de_flotantes_de_doraemon(filas)
    tabla, contenedor, de = construir_tabla(titulo, padre, filas, cabeceras)
    if tabla == -2: 
        return -2    # FIXME: Cosa más fea, I can do better. 
    ## ----------- Si el Tree debe ser de selcción múltiple:
    if multi:
        tabla.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
    ## ----------- Asocio el evento "row-activated" (doble clic sobre una fila)
    #---------------------------------------------------------------#
    def obtener_id_fila(treeview, path, columna, res):              
        """
        Guarda en res[0] el contenido de la primera columna 
        de la fila correspondiente al path (presumiblemente 
        un id de registro).
        """
        # FIXME: Si es de selección múltiple solo va a devolver cuando se 
        # pulse ENTER la fila que se ha seleccionado por último, no todas las 
        # seleccionadas.
        # OJO: Si es de selección simple, el valor se devuelve al final de la 
        #      función pero el diálogo se destruye aquí.
        res[0] = treeview.get_model()[path][0] 
        de.destroy()
    #---------------------------------------------------------------#
    tabla.connect("row-activated", obtener_id_fila, res)
    tabla.connect("cursor-changed", func_change)
    ## ------------ Empaqueto la tabla en el diálogo
    contenedor.show()
    tabla.show()
    #de.vbox.pack_start(tabla)
    de.vbox.pack_start(contenedor)
    de.resize(800, 600) 
    if maximizar:
        de.maximize()   
        # El maximize no funciona bien con beryl en Ubuntu. 
        # Redimensiono antes para que conserve el tamaño si no puede maximizar.
        # De otra forma se queda con el tamaño mínimo posible de la ventana al 
        # intentar maximizar.
    if not defecto:
        iter = tabla.get_model().get_iter_first()
        if iter:
            tabla.get_selection().select_iter(iter)
            #tabla.grab_focus()
    else:
        model = tabla.get_model()
        for indice_fila in defecto[::-1]:
            try:
                iter = model[indice_fila].iter
            except:
                iter = None
            if iter:
                tabla.get_selection().select_iter(iter)
    de.get_children()[-1].get_children()[-1].get_children()[1].grab_focus()
    ## ------------ Ejecuto el diálogo, lo destruyo y devuelvo el resultado:
    response = de.run()
    if response == gtk.RESPONSE_CANCEL:
        res[0] = -1     # -1 es Cancelar. Ver la docstring de la función. 
    elif response == gtk.RESPONSE_ACCEPT:
        model, paths = tabla.get_selection().get_selected_rows()
        # paths es la lista de rutas. Recorro la lista de rutas 
        # devolviendo una lista de la columna 0 (id) de cada una
        # de ellas en el model:
        res = [model[path][0] for path in paths]
        # Si no hay absolutamente nada seleccionado, devuelvo 
        # el mismo valor que si hubiera cancelado:
        if res == []:
            res = [-1]
    de.destroy()
    if not multi:
        # NOTA: Para preservar la compatibilidad con el interfaz que se ha
        # estado usando hasta ahora, si el TreeView no es de selección 
        # múltiple se devuelve un únido id.
        return res[0]
    else:
        # NOTA: Si es de selección múltiple devuelvo una lista de ids.
        return res

def comparar_enteros(n, m):
    """
    Compara n y m como enteros y devuelve 
    -1 si n es menor que m, 1 si es al contrario 
    o 0 si son iguales.
    OJO: Si ALGUNO de los dos no es entero (harto improbable estando en la misma columna)
    usará la comparación a nivel de registro de memoria, me parece, y a saber el orden
    que saldrá.
    """
    if isinstance(n, int) and isinstance(m, int):
        return n - m
    else:
        if n < m:
            return -1
        elif n > m:
            return 1
        else:
            return 0

def comparar_como_numeros(n, m):
    """
    Compara n y m como números (entero o flotante) y 
    devuelve -1, 0 ó 1 tal y como espera la función .sort.
    """
    n = numero.convertir_a_numero(n)
    m = numero.convertir_a_numero(m)
    if n < m:
        return -1
    elif n > m:
        return 1
    else:
        return 0

def construir_tabla(titulo, padre, filas, cabeceras):
    """
    A partir de los datos que recibe el dialogo_resultado
    construye la tabla y el contenedor y los devuelve.
    Si las filas son incorrectas, devuelve -2 tal y como 
    se especifica en la función invocadora.
    """
    ## ------------ Construyo el diálogo:
    de = gtk.Dialog(titulo,
                    padre,
                    gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                    (gtk.STOCK_OK, gtk.RESPONSE_ACCEPT,
                     gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
    ## ------------ Construyo el model: (patrón MVC)
    model = construir_modelo(filas, cabeceras)
    if model == -2: 
        return -2, None, None
    ## ------------ Añado datos al model (capa "modelo")
    for f in filas:
        try:
            model.append(f)
        except TypeError, msg:
            print "utils.py::construir_tabla -> model.append(%s): TypeError: %s" % (f, msg)
    tabla = gtk.TreeView(model)
    ## ------------ ScrolledWindow:
    contenedor = gtk.ScrolledWindow()
    contenedor.add(tabla)
    ## ------------ Defino las columnas de la capa "vista"
    columns = definir_columnas(filas, cabeceras)
    ## ------------ Añado las columnas a la tabla:
    for c in columns:
        tabla.append_column(c)
        c.connect("clicked", cambiar_columna_busqueda, tabla)
    ## ------------ Creo los "renders" para las celdas, los añado a 
    ## ------------ las columnas y los asocio: (capa "controlador")
    cells = []
    for i in xrange(len(columns)):
        if (model.get_column_type(i) == gobject.TYPE_BOOLEAN 
           or isinstance(model.get_column_type(i), bool)):
            cells.append(gtk.CellRendererToggle())
            propiedad = "active"
        else:
            cells.append(gtk.CellRendererText())
            propiedad = "text"
        columns[i].pack_start(cells[i], True)
        columns[i].add_attribute(cells[i], propiedad, i)
    ## ------------ Defino la columna de búsqueda:
    if len(columns) >= 4:
        tabla.set_search_column(3)    
        # Generalmente la 4ª es la de descripciones.
    else:  
        # Si no tiene 4 columnas, que la última sea la de búsqueda por 
        # defecto (se cambiará si hace clic en alguna cabecera).
        tabla.set_search_column(len(columns)-1)
    ## ------------ Y hago que se pueda ordenar por código o descripción:
    for i in xrange(len(columns)):
        model.set_sort_func(i, funcion_orden, i)
        # model.set_sort_column_id(i)
        # columns[i].set_sort_func(i, funcion_orden, i)
        columns[i].set_sort_column_id(i)
    return tabla, contenedor, de

def construir_modelo(filas, cabeceras = None):
    """
    Devuelve un modelo listo para ser usado en un TreeView a
    partir de las filas recibidas.
    """
    try:
        fila = filas[0]
        tipos = []
        for col in fila: 
            tipos.append(tipo_gobject(col))
        model = eval('gtk.ListStore(%s)' % ','.join(tipos))
    except IndexError:     # No hay resultados
        # Pongo el modelo por defecto que he estado usando hasta ahora con 
        # el número de columnas de la cabecera si ésta no es None.
        if not cabeceras:
            model = gtk.ListStore(gobject.TYPE_INT64, 
                                  gobject.TYPE_STRING, 
                                  gobject.TYPE_STRING)
        else:
            tipos = [gobject.TYPE_INT64] + \
                    ([gobject.TYPE_STRING] * (len(cabeceras) - 1))
            model = gtk.ListStore(*tipos)
    except TypeError, ex:    # ¡No hay filas! (filas es None o no es una lista/tupla
        print "ERROR Diálogo resultados (utils.py):", ex
        return -2        # No puedo hacer nada. Cierro la ventana.
    return model
    
def tipo_gobject(valor):
    """
    A partir de un valor devuelve el tipo correspondiente
    según las constantes gobject.
    El tipo lo devuelve como cadena para poder montar el
    model a partir de un eval del constructor. (No hay
    forma de añadir columnas una vez el constructor del 
    ListStore ha sido llamado, así que no veo otra 
    manera de hacerlo que no sea con un eval y cadenas).
    """
    tipo = "gobject.TYPE_STRING"
    # En el peor de los casos, devuelvo un tipo cadena. Todo se puede representar con cadenas.
    if isinstance(valor, bool):     # Esto primero, porque da la casualidad de que bool es subclase de int.
        tipo = 'gobject.TYPE_BOOLEAN'
    elif isinstance(valor, int):
        #return 'gobject.TYPE_INT64'    #Ya tengo (mala) experiencia en enteros que se me pasan de rango. Me curo en salud.
        tipo = 'gobject.TYPE_STRING'    # Hay veces que la primera fila es entero, en el model se crea como entero y en 
            # alguna fila posterior me viene un float o una cadena vacía. Para que no falle, devuelvo tipo cadena para 
            # que construya el model. Cualquier cosa "entra" bien en un tipo cadena.
    elif isinstance(valor, str):
        tipo = 'gobject.TYPE_STRING'
    elif isinstance(valor, type(None)):
        tipo = 'gobject.TYPE_NONE'
    elif isinstance(valor, float):
        # return 'gobject.TYPE_FLOAT'
        tipo = 'gobject.TYPE_DOUBLE'    # Tiene más precisión. Acuérdate del caso 39672.83
    return tipo

def definir_columnas(filas, cabeceras):
    """
    A partir de las filas devuelve una lista
    de columnas adecuadas para usar en un 
    TreeView. Cada columna llevará como 
    cabecera el ítem correspondiente de la
    lista de cabeceras.
    """
    columns = []
    # Uso la primera fila como referencia para el número de columnas
    try:
        n_columnas = len(filas[0])
    except TypeError: #len() of unsized object
        n_columnas = len(cabeceras)
        # cabeceras al menos tendrá 3 elementos a no ser que se especifique
        # lo contrario, en cuyo caso imagino que tendré las luces suficientes
        # como para no intentar mostrar un diálogo de resultados sin columnas.
    except IndexError: #Índice fuera de rango. No hay filas[0]
        n_columnas = len(cabeceras)
    for i in xrange(n_columnas):
        try:
            columns.append(gtk.TreeViewColumn(cabeceras[i]))
        except IndexError:
            columns.append(gtk.TreeViewColumn(''))
    return columns

def cambiar_columna_busqueda(treeviewcolumn, tabla): 
    """
    Cambia la columna de búsqueda interactiva del TreeView "tabla" a 
    la columna TreeViewColumn recibida.
    """
    cols = tabla.get_columns()
    numcols = len(cols)
    numcolumn = 0
    col = tabla.get_column(0)
    while numcolumn < numcols and col != treeviewcolumn:
        numcolumn += 1
        col = tabla.get_column(numcolumn)
    tabla.set_search_column(numcolumn)

def mostrar_calendario(fecha_defecto = time.localtime()[:3][::-1], 
                       padre = None, titulo = 'SELECCIONE FECHA'):
    """
    Muestra y devuelve la fecha seleccioada con un clic.
    SIEMPRE devuelve una fecha como lista de [dd, mm, aaaa]
    aunque cierre la ventana sin seleccionarla con clic.
    La fecha por defecto debe venir en formato d/m/aaaa y
    en forma de lista o tupla.
    """
    if isinstance(fecha_defecto, str):
        try:
            fecha_defecto = fecha.parse_fecha(fecha_defecto)
            fecha_defecto = fecha_defecto.timetuple()[:3][::-1]
        except:
            fecha_defecto = time.localtime()[:3][::-1]
    elif isinstance(fecha_defecto, (tuple, list)) and len(fecha_defecto) < 3:
        fecha_defecto = fecha_defecto[:3]
    elif not fecha_defecto:
        fecha_defecto = time.localtime()[:3][::-1]
    cal = gtk.Calendar()
    cal.set_display_options(gtk.CALENDAR_SHOW_HEADING |
                            gtk.CALENDAR_SHOW_DAY_NAMES |
                            gtk.CALENDAR_WEEK_START_MONDAY)
    if isinstance(fecha_defecto, datetime.date):
        factual = [fecha_defecto.day, fecha_defecto.month, fecha_defecto.year]
    else:
        factual = fecha_defecto     # Fecha en formato d/m/aaaa
    cal.select_month(factual[1]-1, factual[2])  # Enero es el mes 0, no el 1.
    cal.select_day(factual[0])
    cal.mark_day(time.localtime()[2])
    dialog = gtk.Dialog(titulo, 
                        padre, 
                        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, 
                        (gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
    dialog.set_transient_for(padre)
    dialog.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
    dialog.vbox.pack_start(cal)
    cal.show()
    dialog.run()
    dialog.destroy()
    res = cal.get_date()
    res = tuple([res[0], res[1]+1, res[2]]) 
    return res[::-1]    # Para que quede como dd/mm/aaaa


#########################################
#### Utilidades con cadenas de texto ####
#########################################

def eliminar_dobles_espacios(cad):
    """
    Devuelve la cadena "cad" asegurando que no quedan dos espacios consecutivos 
    en ninguna posición.
    """
    if cad:
        return reduce(lambda x, y: x[-1] == " " and y == " " and x or x+y, cad)
    return cad

def corregir_mayusculas_despues_de_punto(cad):
    """
    Devuelve la cadena "cad" con mayúscula siempre después de punto 
    (aunque sea una falta de ortografía si el punto corresponde a una 
    abreviatura).
    """
    res = []
    for subcad in cad.split("."):
        # res.append(subcad.strip().capitalize())   
            # OJO porque al parecer capitalize me jode el encoding y el 
            # reportlab+python2.3+MSWindows después se quejan al pasarlo a 
            # cp1252
        if len(subcad.strip()) > 1:
            res.append(subcad.strip()[0].upper() + subcad.strip()[1:])
    res = ". ".join(res)
    return res 

def update_preview_image(filechooser, preview_image):
    filename = filechooser.get_filename()
    pixbuf = None
    try:
        pixbuf = gtk.gdk.pixbuf_new_from_file(filename)
    except:
        pass
    if pixbuf == None:
        preview_image.set_from_pixbuf(None)
        return
    pixbuf_width = pixbuf.get_width()
    pixbuf_height = pixbuf.get_height()
    if pixbuf_width > 120:
        new_pixbuf_width = 120
        new_pixbuf_height = pixbuf_height*120/pixbuf_width
        pixbuf = pixbuf.scale_simple(new_pixbuf_width, 
                                     new_pixbuf_height, 
                                     gtk.gdk.INTERP_BILINEAR)
    preview_image.set_from_pixbuf(pixbuf)

def dialogo_abrir(titulo = "ABRIR FICHERO", 
                  filtro_imagenes = False, 
                  padre = None, 
                  dir = None):
    """
    Muestra un diálogo de abrir y devuelve el archivo seleccionado 
    o None.
    Si filtro_imagenes es True, añade al diálogo un filtro de imágenes
    a los archivos que se pueden elegir.
    """
    file_open = gtk.FileChooserDialog(title = titulo,
                                      parent = padre,
                                      action = gtk.FILE_CHOOSER_ACTION_OPEN, 
                                      buttons = (gtk.STOCK_CANCEL, 
                                                 gtk.RESPONSE_CANCEL,
                                                 gtk.STOCK_OPEN,
                                                 gtk.RESPONSE_OK))
    if dir != None:
        file_open.set_current_folder(dir)
    if filtro_imagenes:
        """Crear y añadir el filtro de imágenes"""
        filter = gtk.FileFilter()
        filter.set_name("Imágenes")
        filter.add_mime_type("image/png")
        filter.add_mime_type("image/jpeg")
        filter.add_mime_type("image/gif")
        filter.add_pattern("*.png")
        filter.add_pattern("*.jpg")
        filter.add_pattern("*.gif")
        file_open.add_filter(filter)
        # Añadir preview de imágenes.
        browse_preview_image = gtk.Image()
        browse_preview_image.set_size_request(120, -1)
        file_open.set_preview_widget(browse_preview_image)
        file_open.connect("update-preview", update_preview_image, 
                                            browse_preview_image)

    """Crear y añadir el filtro de "todos los archivos"."""
    filter = gtk.FileFilter()
    filter.set_name("Todos los ficheros")
    filter.add_pattern("*")
    file_open.add_filter(filter)
    """Valor devuelto"""
    result = None
    if file_open.run() == gtk.RESPONSE_OK:
        result = file_open.get_filename()
    file_open.destroy()
    return result

def dialogo_guardar_adjunto(documento, padre = None):
    """
    Muestra una ventana de diálogo para guardar el documento adjunto recibido.
    """
    dialog = gtk.FileChooserDialog("GUARDAR DOCUMENTO ADJUNTO",
                                   None,
                                   gtk.FILE_CHOOSER_ACTION_SAVE,
                                   (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                    gtk.STOCK_SAVE, gtk.RESPONSE_ACCEPT))
    dialog.set_default_response(gtk.RESPONSE_OK)
    try:
        home = os.environ['HOME']
    except KeyError:
        try:
            home = os.environ['HOMEPATH']
        except KeyError:
            from tempfile import gettempdir
            home = gettempdir()
            print "WARNING: No se pudo obtener el «home» del usuario"
    if os.path.exists(os.path.join(home, 'tmp')):
        dialog.set_current_folder(os.path.join(home, 'tmp'))
    else:
        dialog.set_current_folder(home)
    dialog.set_current_name(documento.nombre)

    if dialog.run() == gtk.RESPONSE_ACCEPT:
        nomarchivo = dialog.get_filename()
        res = documento.copiar_a(nomarchivo)
        if not res:
            dialogo_info(titulo = "NO SE PUDO GUARDAR", 
                         texto = "Ocurrió un error al guardar el archivo.\n"\
                                 "Pruebe a seleccionar un destino diferente.", 
                         padre = padre)
    dialog.destroy()

def dialogo_adjuntar(titulo, objeto, padre = None):
    """
    Muestra un diálogo y adjunta un fichero a un objeto.
    """
    from os import getenv
    fichero = dialogo_abrir(titulo, 
                            padre = padre, 
                            dir = getenv("HOME", 
                            os.getenv("SystemDrive")))
    if fichero:
        nombre = dialogo_entrada(titulo = "NOMBRE DOCUMENTO", 
                texto = "Introduzca un nombre descriptivo para el documento:", 
                valor_por_defecto = os.path.split(fichero)[-1], 
                padre = padre)
        if nombre:
            from framework import pclases
            pclases.Adjunto.adjuntar(fichero, objeto, nombre)

def cargar_icono_mime(ruta):
    """
    Devuelve el icono que el gestor de ventanas asocie con el archivo 
    recibido. No está relacionado exactamente con el icono MIME porque se 
    usan otros mecanismos para determinar el tipo de archivo, pero me suena 
    más familiar así.
    """
    ruta_generic_icon = os.path.join(
        os.path.dirname(__file__), "..", 'imagenes', 'unknown.png')
    try:
        import gio
    except ImportError:     # Estamos en Windows. Mal asunto.
        res = gtk.gdk.pixbuf_new_from_file(ruta_generic_icon)
    else:
        file_ = gio.File(ruta)
        icon = file_.query_info("standard::icon").get_icon()
        if isinstance(icon, gio.ThemedIcon):
            theme = gtk.icon_theme_get_default()
            try:
                res = theme.choose_icon(icon.get_names(), 16, 0).load_icon()
            except AttributeError:
                res = gtk.gdk.pixbuf_new_from_file(ruta_generic_icon)
        elif isinstance(icon, gio.FileIcon):
            iconpath = icon.get_file().get_path()
            res = gtk.gdk.pixbuf_new_from_file(iconpath)
    return res

def guardar_grafica(grafica, nomfichero):
    #grafica = self.wids['event_box_chart'].get_child()
    ancho, alto = grafica.window.get_geometry()[2:4]
    #i = gtk.gdk.Image(gtk.gdk.IMAGE_FASTEST, grafica.window.get_visual(), 
    #                  ancho, alto)
    #pb = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, True, 8, ancho, alto)
    #i = grafica.window.copy_to_image(i, src_x = 0, src_y = 0, 
    #                                 dest_x = ancho, dest_y = alto, 
    #                                 width = ancho, height = alto)
    #pb = gtk.gdk.Pixbuf.get_from_image(i, src_x = 0, src_y = 0, 
    #                                   dest_x = 0, dest_y = 0, 
    #                                   width = ancho, height = alto)
    pb = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, True, 8, ancho, alto) 
    pb = pb.get_from_drawable(grafica.window, 
                              cmap = grafica.window.get_colormap(), 
                              src_x = 0, src_y = 0, 
                              dest_x = 0, dest_y = 0, 
                              width = ancho, height = alto)
    pb.save(nomfichero, "png")
    
def launch_browser_mailer(dialogo, uri, tipo, ventana_padre = None):
    if tipo == 'email':
        if not mailto(uri):
            dialogo_info('NO IMPLEMENTADO', 
                         'Funcionalidad no implementada.\nDebe lanzar '
                         'manualmente su cliente de correo.\nCorreo-e '
                         'seleccionado: %s' % uri,
                         padre = ventana_padre)
    elif tipo == 'web':
        if not mopen(uri):
            dialogo_info('NO IMPLEMENTADO', 
                         'Funcionalidad no implementada.\n'
                         'Debe lanzar manualmente su navegador web.'
                         '\nURL seleccionada: %s' % uri, 
                         padre = ventana_padre)

def escalar_a(ancho, alto, pixbuf):
    """
    Devuelve un pixbuf escalado en proporción para que como máximo tenga 
    de ancho y alto las medidas recibidas.
    """
    if pixbuf.get_width() > ancho:
        nuevo_ancho = ancho
        nuevo_alto = int(pixbuf.get_height() 
                         * ((1.0 * ancho) / pixbuf.get_width()))
        colorspace = pixbuf.get_property("colorspace")
        has_alpha = pixbuf.get_property("has_alpha")
        bits_per_sample = pixbuf.get_property("bits_per_sample")
        pixbuf2 = gtk.gdk.Pixbuf(colorspace, 
                                 has_alpha, 
                                 bits_per_sample, 
                                 nuevo_ancho, 
                                 nuevo_alto)
        pixbuf.scale(pixbuf2, 
                     0, 0, 
                     nuevo_ancho, nuevo_alto, 
                     0, 0,
                     (1.0 * nuevo_ancho) / pixbuf.get_width(), 
                     (1.0 * nuevo_alto) / pixbuf.get_height(), 
                     gtk.gdk.INTERP_BILINEAR)
        pixbuf = pixbuf2
    if pixbuf.get_height() > alto:
        nuevo_alto = alto
        nuevo_ancho = int(pixbuf.get_width() 
                          * ((1.0 * alto) / pixbuf.get_height()))
        colorspace = pixbuf.get_property("colorspace")
        has_alpha = pixbuf.get_property("has_alpha")
        bits_per_sample = pixbuf.get_property("bits_per_sample")
        pixbuf2 = gtk.gdk.Pixbuf(colorspace, 
                                 has_alpha, 
                                 bits_per_sample, 
                                 nuevo_ancho, 
                                 nuevo_alto)
        pixbuf.scale(pixbuf2, 
                     0, 0, 
                     nuevo_ancho, nuevo_alto, 
                     0, 0,
                     (1.0 * nuevo_ancho) / pixbuf.get_width(), 
                     (1.0 * nuevo_alto) / pixbuf.get_height(), 
                     gtk.gdk.INTERP_BILINEAR)
        pixbuf = pixbuf2
    return pixbuf

def image2pixbuf(image):
    """
    http://www.daa.com.au/pipermail/pygtk/2003-June/005268.html
    """
    #import pygtk
    #pygtk.require("2.0")
    #import gtk
    import StringIO
    #import Image
    file = StringIO.StringIO()
    try:
        image.save(file, 'ppm')
        formato = "pnm"
    except IOError:
        image.save(file, 'png')
        formato = "png"
    contents = file.getvalue()
    file.close()
    loader = gtk.gdk.PixbufLoader(formato)
    loader.write(contents, len (contents))
    pixbuf = loader.get_pixbuf()
    loader.close()
    return pixbuf

def copiar_al_portapapeles(texto):
    """
    Copia el contenido de "texto" al portapapeles.
    """
    c = gtk.Clipboard()
    c.set_text(texto)

def cambiar_por_combo(tv, numcol, opts, campo, ventana_padre = None):
    """
    Cambia el cell de la columna «numcoll» del TreeView «tv» por un combo con 
    las opciones recibidas en «opts», que deben respetar el formato 
    (texto, PUID) -ver get_puid y getObjetoPUID de pclases-.
    También se encarga de crear el callback para guardar los cambios.
    «campo» es el campo como texto que se va a actualizar. Es decir, el que 
    representa la clave ajena.
    «ventana_padre» servirá como ventana padre para la ventana modal de los 
    posibles avisos de error al guardar los valores seleccionados en el combo.
    """
    from framework.pclases import getObjetoPUID
    # Elimino columna actual
    column = tv.get_column(numcol)
    column.clear()
    # Creo model para el CellCombo
    model = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_STRING)
    for opt in opts:
        model.append(opt)
    # Creo CellCombo
    cellcombo = gtk.CellRendererCombo()
    cellcombo.set_property("model", model)
    cellcombo.set_property("text-column", 0)
    cellcombo.set_property("editable", True)
    cellcombo.set_property("has-entry", False)
    # Función callback para la señal "editado"
    def guardar_combo(cell, path, text, model_tv, numcol, model_combo):
        # Es lento, pero no encuentro otra cosa:
        idct = None
        for i in xrange(len(model_combo)):
            texto, id = model_combo[i]
            if texto == text:
                idct = id
                break
        if idct == None:
            dialogo_info(titulo = "ERROR COMBO", 
                texto = "Ocurrió un error inesperado guardando el valor.\n\n"
                        "Contacte con los desarrolladores de la aplicación\n"
                        "(Vea el diálogo «Acerca de...» desde el menú "
                        "principal.)", 
                padre = ventana_padre)
        else:
            valor = getObjetoPUID(idct)
            model_tv[path][numcol] = text
            objeto_a_actualizar = getObjetoPUID(model_tv[path][-1])
            setattr(objeto_a_actualizar, campo, valor)
            objeto_a_actualizar.sync()
            #self.actualizar_ventana()
    cellcombo.connect("edited", guardar_combo, tv.get_model(), numcol, model)
    column.pack_start(cellcombo)
    column.set_attributes(cellcombo, text = numcol)

def sqltype2gobject(col):
    """
    Devuelve una cadena de texto con el tipo que le correspondería en gobject 
    al que tiene la columna col en sqlobject.
    """
    from framework.pclases import SOStringCol as SQLObjectStringCol
    from framework.pclases import SOBoolCol as SQLObjectBoolCol
    from framework.pclases import SODateCol as SQLObjectDateCol
    from framework.pclases import SODateTimeCol as SQLObjectDateTimeCol
    from framework.pclases import SOBigIntCol as SQLObjectBigIntCol
    from framework.pclases import SOFloatCol as SQLObjectFloatCol
    from framework.pclases import SOIntCol as SQLObjectIntCol
    from framework.pclases import SOSmallIntCol as SQLObjectSmallIntCol
    from framework.pclases import SOTimeCol as SQLObjectTimeCol
    from framework.pclases import SOTimestampCol as SQLObjectTimestampCol
    from framework.pclases import SOTinyIntCol as SQLObjectTinyIntCol
    from framework.pclases import SOUnicodeCol as SQLObjectUnicodeCol
    equivalencia = {'gobject.TYPE_BOOLEAN': (SQLObjectBoolCol, ), 
                    'gobject.TYPE_FLOAT': (SQLObjectFloatCol, ), 
                    'gobject.TYPE_DOUBLE': (), 
                    'gobject.TYPE_STRING': (SQLObjectStringCol, 
                                            SQLObjectDateCol, 
                                            SQLObjectDateTimeCol, 
                                            SQLObjectTimeCol, 
                                            SQLObjectTimestampCol, 
                                            SQLObjectUnicodeCol), 
                    'gobject.TYPE_INT': (SQLObjectIntCol, 
                                         SQLObjectSmallIntCol, 
                                         SQLObjectTinyIntCol), 
                    'gobject.TYPE_INT64': (SQLObjectBigIntCol, )}
    default = "gobject.TYPE_STRING"
    tipo = type(col)
    for k in equivalencia:
        for v in equivalencia[k]:
            if v == tipo:
                return k
    return default

def set_fecha(entry):
    """
    Muestra el diálogo de selección de fecha y escribe en el «entry» la 
    fecha seleccionada.
    """
    texto = entry.get_text()
    try:
        defecto = fecha.parse_fecha(texto)
    except ValueError:
        defecto = datetime.date.today()
    ventana_padre = None
    padre = entry.parent
    while padre != None:
        padre = padre.parent
    date = mostrar_calendario(fecha_defecto = defecto, padre = ventana_padre)
    entry.set_text(fecha.str_fecha(date))

