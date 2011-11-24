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

"""
    menu.py - Menú de acceso a módulos y ventanas.
"""

import pygtk
pygtk.require('2.0')
import gtk, gtk.glade, gobject 
import os, sys, traceback, datetime, signal
if os.path.realpath(os.path.curdir).split(os.path.sep)[-1] == "formularios":
    os.chdir("..")
sys.path.append(".")
from gettext import gettext as _
from gettext import bindtextdomain, textdomain
bindtextdomain("cican", 
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "l10n")))
textdomain("cican")
import gtkexcepthook
import utils
from framework.configuracion import ConfigConexion
from multi_open import mailto, open as mopen

__version__ = '0.9.2'
__version_info__ = tuple(
    [int(num) for num in __version__.split()[0].split('.')] + 
    [txt.replace("(", "").replace(")", "") for txt in __version__.split()[1:]]
    )

class MetaF:
    """
    "Metafichero" para almacenar la salida de errores y poder 
    enviar informes de error.
    """
    def __init__(self):
        self.t = ''

    def write(self, t):
        if ("GtkWarning" not in t and 
            "with become" not in t and 
            "PangoWarning" not in t and 
            "main loop already active" not in t):
            try:
                self.t += t
            except TypeError:
                self.t += str(t)
        try:
            sys.__stdout__.write(t)
            sys.__stdout__.flush()
        except IOError: # Windowless, no tengo salida estándar. 
            print t

    def flush(self):
        sys.__stdout__.flush()

    def __repr__(self):
        return self.t

    def __str__(self):
        return self.t

    def __get__(self):
        return self.t

    def vacio(self):
        return len(self.t) == 0


def import_pclases():
    """
    Importa y devuelve el módulo pclases.
    """
    ############################################################
    # Importo pclases. No lo hago directamente en la cabecera 
    # para esperar a ver si se ha pasado al main un fichero de 
    # configuración diferente.
    try:
        import pclases
    except ImportError:
        from framework import pclases
    ############################################################
    return pclases

class Menu:
    def __init__(self, user = None, passwd = None):
        """
        user: Usuario. Si es None se solicitará en la ventana de 
        autentificación.
        passwd: Contraseña. Si es None, se solicitaré en la ventana de 
        autentificación.
        Si user y passwd son distintos a None, no se mostrará la ventana de 
        autentificación a no ser que sean incorrectos.
        """
        #import gestor_mensajes, autenticacion
        from formularios import autenticacion
        login = autenticacion.Autenticacion(user, passwd)
        pclases = import_pclases()
        if pclases.VERBOSE:
            print _("Cargando gestor de mensajes...")
        self.logger = login.logger
        if not login.loginvalido():
            sys.exit(1)
        self.__usuario = login.loginvalido()
        # Configuración del correo para informes de error:
        if self.__usuario.cuenta:
            gtkexcepthook.feedback = self.__usuario.cuenta
            gtkexcepthook.password = self.__usuario.cpass
            gtkexcepthook.smtphost = self.__usuario.smtpserver
            gtkexcepthook.ssl = False
            gtkexcepthook.port = 25
            gtkexcepthook.devs_to = "frbogado@novaweb.es"
            gtkexcepthook.usuario_aplicacion = self.__usuario.usuario
        # Continúo con el gestor de mensajes y resto de ventana menú.
        #self.__gm = gestor_mensajes.GestorMensajes(self.__usuario)
        # DONE: Dividir la ventana en expansores con los módulos del programa 
        # (categorías) y dentro de ellos un IconView con los iconos de cada 
        # ventana. Poner también en lo alto del VBox el icono de la aplicación.
        # (Ya va siendo hora de un poquito de eyecandy).
        if pclases.VERBOSE:
            print _("Cargando menú principal...")
        self.construir_ventana()
        utils.ui.escribir_barra_estado(self.statusbar, 
                                       _("Menú iniciado"), 
                                       self.logger, 
                                       self.__usuario.usuario)

    def get_usuario(self):
        return self.__usuario

    def salir(self, 
              boton, 
              event = None, 
              mostrar_ventana = True, 
              ventana = None):
        """
        Muestra una ventana de confirmación y 
        sale de la ventana cerrando el bucle
        local de gtk_main.
        Si mostrar_ventana es False, sale directamente
        sin preguntar al usuario.
        """
        res = False
        if event == None:
            # Me ha invocado el botón
            if (not mostrar_ventana 
                or utils.ui.dialogo(_('¿Desea cerrar el menú principal?'), 
                                    _('SALIR'), 
                                    padre = ventana, 
                                    icono = gtk.STOCK_QUIT)):
                ventana.destroy()
                self.logger.warning("LOGOUT: %s" % (self.__usuario.usuario))
                res = False
            else:
                res = True
        else:
            res = (not mostrar_ventana 
                   or not utils.ui.dialogo(
                                        _('¿Desea cerrar el menú principal?'), 
                                        _('SALIR'), 
                                        padre = ventana, 
                                        icono = gtk.STOCK_QUIT))
            if not res: 
                self.logger.warning("LOGOUT: %s" % (self.__usuario.usuario))
        return res

    def construir_ventana(self):
        self.statusbar = gtk.Statusbar()
        self.ventana = gtk.Window()
        self.ventana.set_position(gtk.WIN_POS_CENTER)
        self.ventana.resize(800, 600)
        self.ventana.set_title(
            _('CICAN - Menú principal'))
        ruta_logo = os.path.join("imagenes", 'logo.xpm')
        self.ventana.set_icon(gtk.gdk.pixbuf_new_from_file(ruta_logo))
        self.ventana.set_border_width(10)
        self.ventana.connect("delete_event", self.salir, True, self.ventana)
        self.caja = gtk.VBox()
        self.caja.set_spacing(5)
        self.ventana.add(self.caja)
        self.cabecera = gtk.HBox()
        imagen = gtk.Image()
        config = ConfigConexion()
        pixbuf_logo = gtk.gdk.pixbuf_new_from_file(
            os.path.join('imagenes', config.get_logo()))
        pixbuf_logo = escalar_a(300, 200, pixbuf_logo)
        imagen.set_from_pixbuf(pixbuf_logo)
        self.cabecera.pack_start(imagen, fill=True, expand=False)
        texto = gtk.Label("""
        <big><big><big><b>%s</b></big>        

        <u>Menú de acceso a módulos de la aplicación</u></big>        

        <i>v.%s</i></big>        
        """ % (config.get_title(), __version__))
        texto.set_justify(gtk.JUSTIFY_CENTER)
        texto.set_use_markup(True)
        event_box = gtk.EventBox()
            # Porque el gtk.Label no permite cambiar el background.
        event_box.add(texto)
        event_box.modify_bg(gtk.STATE_NORMAL, 
                            event_box.get_colormap().alloc_color("white"))
        self.cabecera.pack_start(event_box)
        self.caja.pack_start(self.cabecera, fill=True, expand=False)
        self.current_frame = None
        cuerpo_central = self.create_menu()
        self.caja.pack_start(cuerpo_central)
        self.caja.pack_start(self.statusbar, False, True)
        
    def create_menu(self):
        pclases = import_pclases()
        model = gtk.ListStore(str, gtk.gdk.Pixbuf)
        modulos = {}
        usuario = self.get_usuario()
        if pclases.VERBOSE:
            print _("Analizando permisos (1/2)...")
        if pclases.VERBOSE:
            i = 0
            tot = pclases.Modulo.select().count()
        for m in pclases.Modulo.select(orderBy = "nombre"):
            if pclases.VERBOSE:
                i += 1
                print _("Analizando permisos (1/2)... ({0:d}/{1:d})") % (i, tot)
            modulos[m] = []
        if pclases.VERBOSE:
            i = 0
            tot = pclases.Permiso.select(
                pclases.Permiso.q.usuarioID == usuario.id).count()
        if pclases.VERBOSE:
            print _("Analizando permisos (2/2)...")
        for permusu in usuario.permisos:
            if pclases.VERBOSE:
                i += 1
                print _("Analizando permisos (2/2)... ({0:d}/{1:d})") % (i, tot)
            if permusu.permiso:
                v = permusu.ventana
                m = v.modulo
                if m != None:
                    modulos[m].append(v)
        modulos_sorted = modulos.keys()
        def fsortalfabeticamente(m1, m2):
            if m1.nombre < m2.nombre:
                return -1
            if m1.nombre > m2.nombre:
                return 1
            return 0
        modulos_sorted.sort(fsortalfabeticamente)
        for modulo in modulos_sorted:
            if modulos[modulo]:
                fichicono = os.path.join('imagenes', modulo.icono)
                pixbuf = gtk.gdk.pixbuf_new_from_file(fichicono)
                model.append([modulo.nombre, pixbuf])
        # Módulo favoritos
        pixbuf = gtk.gdk.pixbuf_new_from_file(
            os.path.join('imagenes', "favoritos.png"))
        iterfav = model.append((_("Favoritos"), pixbuf))
        
        contenedor = gtk.ScrolledWindow()
        icon_view = gtk.IconView(model)
        icon_view.set_text_column(0)
        icon_view.set_pixbuf_column(1)
        icon_view.set_orientation(gtk.ORIENTATION_VERTICAL)
        icon_view.set_selection_mode(gtk.SELECTION_SINGLE)
        icon_view.connect('selection-changed', self.on_select, model)
        icon_view.set_columns(1)
        icon_view.set_item_width(110)
        icon_view.set_size_request(140, -1)
        
        contenedor.add(icon_view)
        self.content_box = gtk.HBox(False)
        self.content_box.pack_start(contenedor, fill=True, expand=False)
        #icon_view.select_path((0,)) 
        icon_view.select_path(model.get_path(iterfav))
            # Al seleccionar una categoría se creará el frame 
        # Sanity check. 
        if hasattr(icon_view, "scroll_to_path"):    # Si pygtk >= 2.8
            icon_view.scroll_to_path(model.get_path(iterfav), False, 0, 0)
        else:
            # ¿No hay equivalente en pyGTK 2.6?
            pass
        return self.content_box 
 
    def on_select(self, icon_view, model=None):
        pclases = import_pclases()
        selected = icon_view.get_selected_items()
        if len(selected) == 0: return
        i = selected[0][0]
        category = model[i][0]
        if self.current_frame is not None:
            self.content_box.remove(self.current_frame)
            self.current_frame.destroy()
            self.current_frame = None
        if category != _("Favoritos"):
            modulo = pclases.Modulo.select(
                pclases.Modulo.q.nombre == category)[0]
        else:
            modulo = _("Favoritos")
        self.current_frame = self.create_frame(modulo)
        utils.ui.escribir_barra_estado(self.statusbar, category, self.logger, 
                                       self.__usuario.usuario)
        self.content_box.pack_end(self.current_frame, fill=True, expand=True)
        self.ventana.show_all()
        
    def create_frame(self, modulo):
        if modulo != _("Favoritos"):
            frame = gtk.Frame(modulo.descripcion)
            frame.add(self.construir_modulo(modulo.descripcion, 
                            [p.ventana for p in self.get_usuario().permisos 
                             if p.permiso and p.ventana.modulo == modulo]))
        else:
            frame = gtk.Frame(_("Ventanas más usadas"))
            pclases = import_pclases()
            usuario = self.get_usuario()
            stats = pclases.Estadistica.select(
             pclases.Estadistica.q.usuarioID == usuario.id, orderBy = "-veces")
            # Se filtran las ventanas en las que ya no tiene permisos aunque 
            # estén en favoritos.
            stats = [s for s in stats 
                     if usuario.get_permisos(s.ventana) 
                         and usuario.get_permisos(s.ventana).permiso][:6]
            stats.sort(lambda s1, s2: (s1.ultimaVez > s2.ultimaVez and -1) 
                                      or (s1.ultimaVez < s2.ultimaVez and 1) 
                                      or 0)
            ventanas = [s.ventana for s in stats]
            frame.add(self.construir_modulo(_("Ventanas más usadas"), 
                                            ventanas, 
                                            False))
        return frame        
        
    def cutmaister(self, texto, MAX = 20):
        """
        Si el texto tiene una longitud superior a 20 caracteres de ancho lo
        corta en varias líneas.
        """
        if len(texto) > MAX:
            palabras = texto.split(' ')
            t = ''
            l = ''
            for p in palabras:
                if len(l) + len(p) + 1 < MAX:
                    l += "%s " % p
                else:
                    t += "%s\n" % l
                    l = "%s " % p
                if len(l) > MAX:    # Se ha colado una palabra de más del MAX
                    tmp = l
                    while len(tmp) > MAX:
                        t += "%s-\n" % tmp[:MAX]
                        tmp = tmp[MAX:]
                    l = tmp
                # print t.replace("\n", "|"), "--", l, "--", p
            t += l
            res = t
        else:
            res = texto
        res = "\n".join([s.center(MAX) for s in res.split("\n")])
        return res
    
    def construir_modulo(self, nombre, ventanas, ordenar = True):
        """
        Crea un IconView con las
        ventanas que contiene el módulo.
        Recibe una lista de objetos ventana de pclases.
        Si «ordenar» es False usa el orden de la lista de ventanas 
        recibidas. En otro caso las organiza por orden alfabético.
        """
        model = gtk.ListStore(str, gtk.gdk.Pixbuf, str, str)
        # ventanas.sort(key=lambda v: v.descripcion)
        # En Python2.3 parece ser que no estaba la opción de especificar 
        # la clave de ordenación.
        if ordenar:
            ventanas.sort(lambda s1, s2: 
                            (s1.descripcion>s2.descripcion and 1) or 
                            (s1.descripcion<s2.descripcion and -1) or 0)
        for ventana in ventanas:
            try:
                pixbuf = gtk.gdk.pixbuf_new_from_file(
                            os.path.join('imagenes', ventana.icono))
            except (gobject.GError, AttributeError, TypeError):  # Icono es "" o None (NULL en la tabla).
                pixbuf = gtk.gdk.pixbuf_new_from_file(
                            os.path.join('imagenes', 'dorsia.png'))
            model.append((self.cutmaister(ventana.descripcion), pixbuf, 
                          ventana.fichero, ventana.clase))
            # El model tiene: nombre (descripción), icono, archivo, clase, descripción detallada (hint)
            # NOTA: No se pueden mostrar hints en el IconView (al menos yo no sé cómo), así que ahora 
            #       lo que tiene es el icono.
        contenedor = gtk.ScrolledWindow()
        iview = gtk.IconView(model)
        iview.set_text_column(0)
        iview.set_pixbuf_column(1)
        iview.set_item_width(180)
        iview.connect('item-activated', self.abrir, model)
        iview.connect('selection-changed', self.mostrar_item_seleccionado, 
                      model)
        contenedor.add(iview)
        return contenedor

    def mostrar_item_seleccionado(self, icon_view, model):
        selected = icon_view.get_selected_items()
        if len(selected) == 0: return
        i = selected[0][0]
        descripcion_icono_seleccionado = model[i][0]
        descripcion_icono_seleccionado = descripcion_icono_seleccionado.replace('\n', ' ')
        utils.ui.escribir_barra_estado(self.statusbar, 
                                       descripcion_icono_seleccionado, 
                                       self.logger, 
                                       self.__usuario.usuario)

    def volver_a_cursor_original(self):
        # print "Patrick Bateman sabe que es una chapuza y que no hay que"\
        #       " hacer suposiciones de tiempo."
        self.ventana.window.set_cursor(None)
        return False

    def abrir(self, iview, path, model):
        clase = model[path][3]
        archivo = model[path][2]
        pclases = import_pclases()
        pclases.Estadistica.incrementar(self.__usuario, archivo)
        self.abrir_ventana(archivo, clase)

    def abrir_ventana(self, archivo, clase):
        if archivo.endswith('.py'):  # Al importar no hay que indicar extensión
            archivo = archivo[:archivo.rfind('.py')]
        if clase == 'acerca_de' and archivo == 'acerca_de':
            utils.ui.escribir_barra_estado(self.statusbar, 
                                           _('Abrir: "acerca de..."'), 
                                           self.logger, 
                                           self.__usuario.usuario)
            self.acerca_de()
        elif "pruebas_periodicas" in clase:
            utils.ui.escribir_barra_estado(self.statusbar, 
                                        _("Pruebas de coherencia de datos"), 
                                        self.logger, 
                                        self.__usuario.usuario)
            self.abrir_pruebas_coherencia()
        else:
            utils.ui.escribir_barra_estado(self.statusbar, 
                                        _("Cargar: %s.py") % archivo, 
                                        self.logger, 
                                        self.__usuario.usuario)
            self.abrir_ventana_modulo_python(archivo, clase)

    def abrir_ventana_modulo_python(self, archivo, clase):
        try:
            self.ventana.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
            while gtk.events_pending(): gtk.main_iteration(False)
            # HACK: Debe haber una forma mejor de hacerlo. De momento me 
            #       aprovecho de que el mainloop no va a atender al 
            #       timeout aunque se cumpla el tiempo, ya que está 
            #       ocupado en abrir la ventana, con lo que el cursor 
            #       sale del "busy" justo cuando debe, al abrirse la 
            #       ventana.
            v = None 
            pclases = import_pclases()
            gobject.timeout_add(200, self.volver_a_cursor_original)
            try:
                self.lanzar_ventana(archivo)
                if pclases.DEBUG:
                    print _("¡El lanzador multiproceso de Doraemon! (%s)") % (
                        archivo)
            except Exception, e:
                sys.stderr.write(`e`)
                self._lanzar_ventana(archivo, clase)
                if pclases.DEBUG:
                    print _("¡El lanzador bloqueante de Nobita! (%s)") % (
                        archivo)
        except:
            self.ventana.window.set_cursor(None)
            utils.ui.escribir_barra_estado(self.statusbar, 
                _("Error detectado. Iniciando informe por correo."), 
                self.logger, 
                self.__usuario.usuario)
            self.enviar_correo_error_ventana()

    def _lanzar_ventana(self, archivo, clase):
        """
        DEPRECATED
        """
        # No puede mandar más parámetros como la configuración, PUID y 
        # demás ventajas que sí tiene el otro lanzador.
        exec "import %s" % archivo
        v = eval('%s.%s' % (archivo, clase))
        v(usuario = self.get_usuario())
        # Podría incluso guardar los objetos ventana que se van 
        # abriendo para controlar... no sé, algo, contar las ventanas 
        # abiertas o qué se yo.

    def _importar_e_instanciar(self, archivo, clase):
        exec "import %s" % archivo
        v = eval('%s.%s' % (archivo, clase))
        v(usuario = self.get_usuario())

    def lanzar_ventana(self, archivo):
        """
        EXPERIMENTAL
        """
        from subprocess import Popen
        usuario = self.get_usuario()
        if os.path.basename(os.path.abspath(os.curdir)) == "formularios":
            ruta = os.path.abspath(os.path.join(".", archivo+".py"))
        else:
            ruta = os.path.abspath(
                    os.path.join(".", "formularios", archivo+".py"))
        pclases = import_pclases()
        if pclases.DEBUG:
            print _("Lanzando..."), ruta,
            print _("¿Existe?"), os.path.exists(ruta)
        # FIXME: Esto no funciona en el W2003 Server de CICAN. Dice que...
        # WindowsError: [Error 193] %1 no es una aplicación Win32 válida.
        # Creo que es porque sin ponerle un "start" delante ni nada a la ruta, 
        # no sabe con qué abrirlo. Es como si desde el cmd escribiera algo.txt.
        # No se ejecuta. Necesita ponerse delante el nombre del programa que 
        # abre el archivo o usar "start" para que lo haga con el 
        # predeterminado. Otra opción sería usar el multi-open. Investigaré.
        if os.name == "nt":
            bin_params = ["start {0}".format(ruta)]
        else:
            bin_params = [ruta]
        if usuario:
            idusuario = usuario.id
            bin_params.append("--usuario=%s" % idusuario)
        config = ConfigConexion()
        fconfig = config.get_file()
        if fconfig:
            bin_params.append("--config=%s" % fconfig)
            fconfig_original = replace_fconfig(fconfig)
        Popen(bin_params)
        if fconfig:
            # TODO: FIXME: No restaura el contenido original. ¿Tal vez lo 
            # hago demasiado rápido? ¿Debería sincronizarme con señales? ¿Y 
            # qué pasa con las máquinas windows donde ni el fork ni las 
            # señales funcionan en condiciones? Y si lo hago nada más lanzar 
            # el menú y restauro al salir, ¿qué pasa si se me cuelga y tengo 
            # que cerrar a capón? Me quedo sin el original. Merde.
            restore_fconfig(fconfig_original)

    def enviar_correo_error_ventana(self):
        print _("Se ha detectado un error")
        texto = ''
        for e in sys.exc_info():
            texto += "%s\n" % e
        tb = sys.exc_info()[2]
        texto += _("Línea %s\n") % tb.tb_lineno
        info = MetaF() 
        traceback.print_tb(tb, file = info)
        texto += "%s\n" % info
        enviar_correo(texto, self.get_usuario())
    
    def abrir_pruebas_coherencia(self):
        if os.name == 'posix':
            w = gtk.Window()
            w.set_title(_("SALIDA CHECKLIST WINDOW"))
            scroll = gtk.ScrolledWindow()
            w.add(scroll)
            tv = gtk.TextView()
            scroll.add(tv)
            def forzar_iter_gtk(*args, **kw):
                while gtk.events_pending(): 
                    gtk.main_iteration(False)
            def printstdout(msg):
                tv.get_buffer().insert_at_cursor(msg)
                forzar_iter_gtk()
            w.show_all()
            forzar_iter_gtk()
            import runapp
            # pid = os.spawnl(os.P_NOWAIT, "gajim.py")
            # Inexplicablemente -juraría que antes funcionaba- el spawnl ya no rula.
            # SOLO PARA NOSTROMO:
            #os.system("./checklist_window.py 2>&1 | tee > ../../fixes/salida_check_`date +%Y_%m_%d_%H_%M`.txt &")
            comando = "./checklist_window.py 2>&1 | tee > ../../fixes/salida_check_`date +%Y_%m_%d_%H_%M`.txt &"
            runapp.runapp(comando, printstdout)
            #os.system("./checklist_window.py 2>&1 | tee > salida_check_`date +%Y_%m_%d_%H_%M`.txt &")
        elif os.name == 'nt':
            os.startfile("checklist_window.py") 
        else:
            utils.ui.dialogo_info(titulo = _("PLATAFORMA NO SOPORTADA"),
                texto = _("Pruebas de coherencia solo funcionan en "
                        "arquitecturas con plataformas POSIX o NT\n"
                        "(GNU/Linux, MS-Windows, *BSD...)."),
                padre = self.ventana)

    def mostrar(self):
        self.ventana.show_all()
        self.ventana.connect('destroy', gtk.main_quit)
        gtk.main()

    def acerca_de(self):
        gtk.about_dialog_set_email_hook(utils.ui.launch_browser_mailer,'email')
        gtk.about_dialog_set_url_hook(utils.ui.launch_browser_mailer, 'web')
        vacerca = gtk.AboutDialog()
        vacerca.set_name('CICAN')
        vacerca.set_version(__version__)
        vacerca.set_comments(_('Software de gestión del Centro de Investigadión de Carreteras de ANdalucía'))
        vacerca.set_authors(
            ['Francisco José Rodríguez Bogado <frbogado@novaweb.es>', 
             _('Algunas partes del código por:') 
                + ' Diego Muñoz Escalante <escalant3@gmail.com>'])
        config = ConfigConexion()
        logo = gtk.gdk.pixbuf_new_from_file(
            os.path.join('imagenes', config.get_logo()))
        vacerca.set_logo(logo)
        fichero_licencia = os.path.join(
                            os.path.dirname(__file__), "..", 'COPYING')
        try:
            content_licencia = open(fichero_licencia).read()
        except IOError:
            content_licencia = open("COPYING").read()
        vacerca.set_license(content_licencia)
        vacerca.set_website('http://informatica.novaweb.es')
        vacerca.set_artists([_('Iconos gartoon por') 
            + ' Kuswanto (a.k.a. Zeus) <zeussama@gmail.com>'])
        vacerca.set_copyright(
            'Copyright 2009-2011  Francisco José Rodríguez Bogado.')
        vacerca.run()
        vacerca.destroy()


def construir_y_enviar(w, ventana, remitente, observaciones, texto, usuario):
    import ventana_progreso
    from utils.cibercorreo import enviar_correoe
    rte = remitente.get_text()
    buffer = observaciones.get_buffer()
    obs = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter()) 
    if usuario == None:
        contra = ''
    else:
        contra = usuario.cpass
    pwd = utils.ui.dialogo_entrada(titulo = _('CONTRASEÑA'), texto = """ 
    Introduzca la contraseña de su cuenta de correo.       
    No se almacenará.
    
    """, pwd = True, valor_por_defecto = contra)
    if pwd != None and pwd != "":
        vpro = ventana_progreso.VentanaProgreso()
        vpro.tiempo = 25
        vpro.mostrar()
        vpro.set_valor(0.0, _("Enviando correo desde %s...") % rte)
        texto = _("OBSERVACIONES: ") + obs + "\n\n\n" + texto 
        tos = ('frbogado@novaweb.es', )
        i = 0
        if not enviar_correoe(usuario and usuario.email or rte, tos, 
                _("ERROR CICAN. Capturada excepción no contemplada "
                  "({0}).").format(usuario and usuario.usuario or ""),
                texto, 
                servidor = usuario and usuario.smtpserver or "gea21.es", 
                usuario = rte, 
                password = pwd):
            guardar_error_a_disco(rte, obs, texto)
        vpro.ocultar()
        utils.ui.dialogo_info(titulo = _('CORREO ENVIADO'), 
            texto = _('Informe de error enviado por correo electrónico.')) 
        ventana.destroy()

def mostrar_dialogo_y_guardar(txt):
    dialog = gtk.FileChooserDialog(_("GUARDAR TRAZA/DEBUG"),
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
            home = "."
            print _("WARNING: No se pudo obtener el «home» del usuario")
    if os.path.exists(os.path.join(home, 'tmp')):
        dialog.set_current_folder(os.path.join(home, 'tmp'))
    else:
        dialog.set_current_folder(home)
    filter = gtk.FileFilter()
    filter.set_name(_("Archivos de traza-depuración texto plano ginn"))
    filter.add_pattern("*.qdg")
    filter.add_pattern("*.QDG")
    filter.add_pattern("*.Qdg")

    dialog.add_filter(filter)
    filter = gtk.FileFilter()
    filter.set_name(_("Todos"))
    filter.add_pattern("*")
    dialog.add_filter(filter)

    dialog.set_current_name("%s.qdg" % (datetime.date.today().strftime("%d_%m_%Y")))

    if dialog.run() == gtk.RESPONSE_ACCEPT:
        nomarchivo = dialog.get_filename()
        try:
            if nomarchivo[:nomarchivo.rindex(".")] not in ("qdg", "QDG", "Qdg"):
                nomarchivo = nomarchivo + ".qdg"
        except:
            nomarchivo = nomarchivo + ".qdg"
        save_to_file(nomarchivo, txt)
    dialog.destroy()

def save_to_file(nombre, texto):
    """
    Abre el archivo "nombre" y guarda el texto en él. Si ya existe, lo añade.
    """
    try:
        f = open(nombre, 'a')
        f.write(texto)
        f.close()
        utils.ui.dialogo_info(titulo = _("TRAZA GUARDADA"),
            texto = _("La información de depuración se ha guardado "
                      "correctamente en %s.\nCierre la ventana y reinicie "
                      "el programa completo.") % (nombre))
    except IOError:
        utils.ui.dialogo_info(titulo = _("NO TIENE PERMISO"), 
            texto = _("No tiene permiso para guardar el archivo. Pruebe en "
                      "otro directorio."))

def guardar_error_a_disco(remitente, observaciones, texto):
    """
    Pregunta si guardar el error en disco como archivo de texto.
    """
    if utils.ui.dialogo(titulo = _("¿GUARDAR A DISCO?"),
        texto = _("Si no puede enviar el informe de error o no tiene conexión"
                  " a Internet\npuede guardar la información en un fichero de"
                  " texto para que sea revisada más tarde.\n\n¿Quiere guardar"
                  " la traza de depuración en disco ahora?")):
        txt = _("REMITENTE: {0:s}\n\nOBSERVACIONES: {1:s}\n\nTEXTO: \n{2:s}\n"
               ).format(remitente, observaciones, texto)
        mostrar_dialogo_y_guardar(txt)
 
def crear_ventana(titulo, texto, usuario):
    # PLAN: ¿Meto un "recordar contraseña"?
    ventana = gtk.Window()
    ventana.set_title(titulo)
    ventana.set_modal(True)
    ventana.set_position(gtk.WIN_POS_CENTER_ALWAYS)
    tabla = gtk.Table(5, 2)
    imagen = gtk.Image()
    imagen.set_from_file(os.path.join('imagenes', 'emblem-mail.png'))
    info = gtk.Label(_('Se produjo un error mientras usaba la aplicación\n'
        'Es recomendable enviar un informe a los desarrolladores.\nDebe '
        'contar con una cuenta de correo electrónico para poder hacerlo.'))
    tabla.attach(imagen, 0, 1, 0, 1, xpadding = 5, ypadding = 5)
    tabla.attach(info, 1, 2, 0, 1, xpadding = 5, ypadding = 5)
    tabla.attach(gtk.Label(_('Cuenta: ')), 0, 1, 1, 2, xpadding = 5, 
                 ypadding = 5)
    remitente = gtk.Entry()
    if usuario != None:
        remitente.set_text(usuario.cuenta)
    tabla.attach(remitente, 1, 2, 1, 2, xpadding = 5, ypadding = 5)
    tabla.attach(gtk.Label(_('Observaciones: ')), 0, 1, 2, 3, xpadding = 5, 
                 ypadding = 5)
    observaciones = gtk.TextView()
    tabla.attach(observaciones, 1, 2, 2, 3, xpadding = 5, ypadding = 5)
    expander = gtk.Expander("Ver...")
    tabla.attach(expander, 0, 2, 4, 5, xpadding = 5, ypadding = 5)
    hb_error = gtk.HBox()
    expander.add(hb_error)
    hb_error.pack_start(gtk.Label(_('Error capturado: ')))
    hb_error.pack_start(gtk.Label(texto))
    #tabla.attach(gtk.Label(_('Error capturado: ')), 0, 1, 4, 5, xpadding = 5, 
    #             ypadding = 5)
    #tabla.attach(gtk.Label(texto), 1, 2, 4, 5, xpadding = 5, ypadding = 5)
    boton = gtk.Button(stock = gtk.STOCK_OK)
    tabla.attach(boton, 1, 2, 3, 4, xpadding = 5, ypadding = 5)
    ventana.add(tabla)
    ventana.show_all()
    return ventana, boton, remitente, observaciones

def enviar_correo(texto, usuario = None):
    ventana, boton, remitente, observaciones = crear_ventana(
        _('ENVIAR INFORME DE ERROR'), texto, usuario)
    ventana.connect('destroy', gtk.main_quit)
    boton.connect('clicked', construir_y_enviar, ventana, remitente, 
                                                 observaciones, texto, usuario)
    gtk.main()

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

def main():
    fconfig = None
    user = None
    passwd = None
    if len(sys.argv) > 1:
        from optparse import OptionParser
        usage = _("uso: %prog [opciones] usuario contraseña")
        parser = OptionParser()#usage = usage)
        parser.add_option("-c", "--config", 
                          dest = "fichconfig", 
                          help = _("Usa una configuración alternativa "
                                   "almacenada en FICHERO"), 
                          metavar = "FICHERO")
        (options, args) = parser.parse_args()
        fconfig = options.fichconfig
        if len(args) >= 1:
            user = args[0]
        if len(args) >= 2:
            passwd = args[1]
        # HACK
        if fconfig:
            config = ConfigConexion()
            config.set_file(fconfig)
            print "Usando configuración de {0}".format(fconfig)
        # Lo hago así porque en todos sitios se llama al constructor sin 
        # parámetros, y quiero instanciar al singleton por primera vez aquí. 
        # Después pongo la configuración correcta en el archivo y en sucesivas 
        # llamadas al constructor va a devolver el objeto que acabo de crear y 
        # con la configuración que le acabo de asignar. En caso de no recibir 
        # fichero de configuración, la siguiente llamada al constructor será 
        # la que cree el objeto y establezca la configuración del programa. 
        # OJO: Dos llamadas al constructor con parámetros diferentes crean 
        # objetos diferentes.
    #salida = MetaF()
    #sys.stdout = salida
    errores = MetaF()
    sys.stderr = errores

    m = Menu(user, passwd)
    m.mostrar()

    if 0:   # TODO: FIXME: XXX: ¡Quitar cuando arregle/funcione el bugreport!
    # if not errores.vacio():
        print >> sys.stderr, _("Se han detectado algunos errores en "
                               "segundo plano durante la ejecución.")
        enviar_correo(_('Errores en segundo plano. La stderr contiene:\n%s') 
                        % (errores), 
                      m.get_usuario())

def replace_fconfig(nuevo):
    """
    Cambia físicamente el fichero de configuración por defecto 
    (framework/ginn.conf) por el de la ruta recibida.
    El original lo guarda en una copia temporal y devuelve el nombre de la 
    misma.
    """
    import tempfile, shutil
    dirframework = os.path.abspath(os.path.join(os.path.dirname(__file__), 
                                              "..", "framework"))
    original = os.path.join(dirframework, "ginn.conf")
    fd, pathtemp = tempfile.mkstemp()
    #shutil.copy(original, pathtemp)
    o = open(original)
    t = open(pathtemp, "w")
    t.write(o.read())
    o.close()
    t.close()
    #shutil.copy(nuevo, original)
    o = open(original, "w")
    n = open(nuevo)
    o.write(n.read())
    o.close()
    n.close()
    return pathtemp

def restore_fconfig(original):
    import tempfile, shutil
    dirframework = os.path.abspath(os.path.join(os.path.dirname(__file__), 
                                              "..", "framework"))
    bastardo = os.path.join(dirframework, "ginn.conf")
    #shutil.copy(original, bastardo)
    o = open(original, "w")
    b = open(bastardo)
    o.write(b.read())
    o.close()
    b.close()
    

if __name__ == '__main__':
    # Import Psyco if available
    try:
        import psyco
        psyco.full()
        #psyco.log()
        #psyco.profile()
    except ImportError:
        print _("Optimizaciones no disponibles.")
    main()
    # Si se ha usado el GMapCatcher, habrá por ahí algún que otro hilo 
    # medio zombi. Suicidio en tres, dos, uno...
    pid = os.getpid()
    # send ourselves sigquit, particularly necessary in posix as
    # download threads may be holding system resources - python
    # signals in windows implemented in python 2.7
    #if os.name == 'posix':
    try:
        os.kill(pid, signal.SIGQUIT)
    except AttributeError:  # Python <2.7
        import ctypes
        def kill(pid):
            """kill function for Win32"""
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.OpenProcess(1, 0, pid)
            return (0 != kernel32.TerminateProcess(handle, 0))
        kill(pid)

