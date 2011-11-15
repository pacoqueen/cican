#!/usr/bin/env python
# -*- coding: utf-8 -*-

from gettext import gettext as _
from framework.configuracion import ConfigConexion

def parse_options():
    """
    Instancia las opciones de arranque (parámetros de línea de comando) para 
    la ventana de la clase invocadora.
    """
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-u", "--usuario", dest = "usuario",
                      help = _("Nombre o identificador del usuario"))
    parser.add_option("-d", "--debug", dest = "debug", 
                      action="store_true", 
                      help = _("Activar información de depuración"))
    parser.add_option("-p", "--puid", dest = "puid", 
                      help = _("Identificador de pclases (puid) "
                               "del objeto a mostrar en ventana inicialmente"))
    parser.add_option("-c", "--config", 
                      dest = "fichconfig", 
                      help = _("Usa una configuración alternativa "
                               "almacenada en FICHERO"), 
                      metavar = "FICHERO")
    parser.add_option("-v", "--verbose", dest = "verbose", 
                      action = "store_true", 
                      help = _("Activar el modo verboso"))
    (options, args) = parser.parse_args()
    params = []
    opt_params = {}
    if len(args) != 0:
        params = args[0]
    # FIXME: Como pclases se importa en ventana_generica y en cualquier otra 
    # ventana (a excepción del menú) antes de poder parsear la opción "-c", no 
    # hay manera -inmediata, se entiende, sin reescribir mucho- de usar una 
    # configuración alternativa que no sea la que está en ginn.conf :(
    fconfig = options.fichconfig
    if fconfig:
        config = ConfigConexion()
        config.set_file(fconfig)
        config.DEBUG = options.debug
        config.VERBOSE = options.verbose
    # Como no se puede cambiar al vuelo la conexión a la BD, el cambio del 
    # fichero de configuración hay que hacerlo ANTES de "cargar" pclases.
    from framework import pclases
    pclases.DEBUG = options.debug
    pclases.VERBOSE = options.verbose
    if options.usuario:
        opt_params["usuario"] = options.usuario
    if options.puid:
        puid = options.puid
        objeto = pclases.getObjetoPUID(puid)
        opt_params["objeto"] = objeto
    return params, opt_params

