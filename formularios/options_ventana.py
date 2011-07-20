#!/usr/bin/env python
# -*- coding: utf-8 -*-

from framework import pclases

def parse_options():
    """
    Instancia las opciones de arranque (parámetros de línea de comando) para 
    la ventana de la clase invocadora.
    """
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-u", "--usuario", dest = "usuario",
                      help = "Nombre o identificador del usuario")
    parser.add_option("-d", "--debug", dest = "debug", 
                      action="store_true", 
                      help = "Activar información de depuración")
    parser.add_option("-p", "--puid", dest = "puid", 
                      help = "Identificador de pclases (puid) "
                             "del objeto a mostrar en ventana inicialmente")
    (options, args) = parser.parse_args()
    pclases.DEBUG = options.debug
    params = []
    opt_params = {}
    if len(args) != 0:
        params = args[0]
    if options.usuario:
        opt_params["usuario"] = options.usuario
    if options.puid:
        puid = options.puid
        objeto = pclases.getObjetoPUID(puid)
        opt_params["objeto"] = objeto
    return params, opt_params

