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
Created on 24/01/2011

@author: bogado

    Algunas utilidades relacionadas con el correo electrónico.
    El genial nombre del módulo hay que agradecérselo a la RAE.

'''

def enviar_correoe(remitente, 
                   destinos, 
                   asunto, 
                   texto, 
                   adjuntos = [], 
                   servidor = "localhost", 
                   usuario = None, 
                   password = None, 
                   ssl = False):
    """
    Envía un correo electrónico a las direcciones contenidas en la lista 
    "destinos" con los adjuntos de la lista y a través del servidor "servidor".
    Si usuario y contraseña != None, se usarán para hacer login en el 
    servidor SMTP.
    Devuelve True si se envió el correo electrónico sin problemas.
    AL LORO: El viruscan de los windows de los ordenadores de oficina 
    BLOQUEA las conexiones salientes al puerto 25.
    OJO: Si el servidor es gmail, como solo admite autenticación por SSL, se 
    machaca el valor del parámetro «ssl» a True.
    """
    GMAIL = servidor.endswith("gmail.com") or servidor.endswith("google.com")
    if GMAIL:
        ssl = True
    #print "remitente", remitente
    #print "destinos", destinos
    #print "asunto", asunto
    #print "texto", texto
    #print "adjuntos", adjuntos
    #print "servidor", servidor
    #print "usuario", usuario
    #print "password", password
    import smtplib
    import os
    from email.mime.multipart import MIMEMultipart
    from email.mime.base import MIMEBase
    from email.mime.text import MIMEText
    from email.utils import COMMASPACE, formatdate
    from email import encoders

    assert type(destinos) is list or type(destinos) is tuple
    assert type(adjuntos) is list or type(adjuntos) is tuple

    ok = False

    msg = MIMEMultipart()
    # XXX
    msg.set_charset("8859")
    # XXX
    msg['From'] = remitente
    msg['To'] = COMMASPACE.join(destinos)
    msg['Date'] = formatdate(localtime = True)
    # XXX
    try:
        asunto = asunto.decode("utf8")
    except:
        pass
    try:
        texto = texto.decode("utf8").encode("8859")
    except:
        pass
    # XXX
    msg['Subject'] = asunto

    msg.attach(MIMEText(texto))

    for file in adjuntos:
        #print file
        part = MIMEBase('application', "octet-stream")
        part.set_payload(open(file,"rb").read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', 
                        'attachment; filename="%s"' % os.path.basename(file))
        msg.attach(part)
        #print part
    try:
        from socket import error as socket_error
        if not GMAIL:
            smtp = smtplib.SMTP(servidor)
        else:
            smtp = smtplib.SMTP(servidor, 587)
    except socket_error, msg:
        debug_info(titulo = "ERROR CONECTANDO A SERVIDOR SMTP", 
                   texto = "Ocurrió el siguiente error al conectar al "
                           "servidor de correo saliente:\n%s\n\n"
                           "Probablemente se deba a la configuración de su "
                           "firewall\no a que su antivirus está bloqueando"
                           " las conexiones salientes al puerto 25." % (msg))
        ok = False
    else:
        if ssl:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
        try:
            if usuario and password:
                smtp.login(usuario, password)
            response = smtp.sendmail(remitente, destinos, msg.as_string())
            ok = True
        except smtplib.SMTPAuthenticationError, msg:
            debug_info(titulo = "ERROR AUTENTICACIÓN", 
                       texto = "Ocurrió un error al intentar la "
                               "autentificación en el servidor:\n\n%s" % (msg))
            ok = False
        except (smtplib.SMTPRecipientsRefused, smtplib.SMTPSenderRefused), msg:
            print "cibercorreo.py (enviar_correoe) -> Excepción: %s" % (msg)
            ok = False
        except (smtplib.SMTPServerDisconnected), msg:
            print "cibercorreo.py (enviar_correoe) -> "\
                  "Desconectado. ¿Timeout? Excepción: %s" % (msg)
            ok = False
        smtp.close()
    return ok

def debug_info(*args, **kw):
    """
    TEMP: Es solo para quitarme de en medio el dialogo_info del enviar_correoe 
    original. Aquí no voy a permitir que se rompa la separación de capas 
    abriendo ventanas donde no corresponde.
    """
    import sys
    sys.stderr.write(str(args))
    sys.stderr.write("\n")
    sys.stderr.write(str(kw))
    sys.stderr.write("\n")


if __name__ == "__main__":
    # Un pequeño test.
    remitente = raw_input("Cuenta de correo gmail: ")
    passwd = raw_input("Contraseña: ")
    destino = raw_input("Dirección de destino: ")
    enviar_correoe(remitente, 
                   [destino, ], 
                   "Prueba cibercorreo", 
                   "Esto es una prueba.\n\nTal y pam.\n\n", 
                   adjuntos = ["./cibercorreo.py"], 
                   servidor = "smtp.gmail.com", 
                   usuario = remitente, 
                   password = passwd) 

