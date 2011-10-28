#!/usr/bin/env python
# -*- coding: utf-8 -*-

# TODO: PORASQUI: BUG: Cerrar la ventana no detiene el GMapCatcher y se queda 
# como un proceso de fondo en espera bloqueante... Ni atiende al Ctrl+C 
# siquiera.

import sys, os.path
dirfichero = os.path.realpath(os.path.dirname(__file__))
if os.path.realpath(os.path.curdir) == dirfichero:
    os.chdir("..")
if ("utils" in os.listdir(os.path.curdir) 
    and os.path.abspath(os.path.curdir) not in sys.path):
    sys.path.insert(0, ".")
from utils.googlemaps import GoogleMaps, GoogleMapsError
try:
# XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
    # raise ImportError   # XXX: Solo para probar... BORRAR DESPUÉS
# XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
    import osmgpsmap    # Third dependency. No está en el árbol local.
    from utils.mapviewer import DummyLayer, imdir
    OSMGPSMAP = True
except ImportError, msg:
    OSMGPSMAP = False
    os.chdir(os.path.abspath(
        os.path.join(dirfichero, "..", "utils", "gmapcatcher")))
    import maps as gmc
    os.chdir(os.path.join(dirfichero, ".."))
import gtk

APIFILENAME = "gg_api_key.txt"

class Mapa():
    def __init__(self, apifile = None):
        if not apifile:
            mydir = os.path.dirname(os.path.abspath(__file__))
            apifile = os.path.join(mydir, APIFILENAME)
        fapi = open(apifile)
        self.__ggapi = fapi.read()
        fapi.close()
        self.ggmap = GoogleMaps(self.__ggapi)
        self.init_mapa()

    def init_mapa(self):
        if OSMGPSMAP:
            self.osm = osmgpsmap.GpsMap()
            self.osm.layer_add(osmgpsmap.GpsMapOsd(show_dpad = True,
                                                   show_zoom = True))
            self.osm.layer_add(
                        DummyLayer())
            self.osm.connect('button_release_event', self.map_clicked)
            self.osm.set_zoom(13)   # Zoom por defecto
        else:
            logging_path = conf_path = None   # Es la conf. por defecto. Ver 
                                # utils/gmapatcher/map.py para más detalles.
            gmc.mapLogging.init_logging(logging_path)
            gmc.log.info("Starting %s version %s." % (gmc.NAME, gmc.VERSION))
            self.gmcw = gmc.MainWindow(config_path = conf_path)
            self.gmcw.do_zoom(4)   # Zoom por defecto. 
            # TODO: PORASQUI: Hacer un traslado de escala entre el zoom de 
            # GMC que va -creo- desde -2 (cerca) a más de 10 (lejos) al de 
            # OSM, que va al contrario y 13 es cerca. Ver las "constantes"
            # definidas en cada caso (MAX_ZOOM_no_sé_qué en GMC).
            self.osm = self.gmcw.container

    def map_clicked(self, osm, event):
        if OSMGPSMAP:
            lat, lon = self.osm.get_event_location(event).get_degrees()
        else:
            lat, lon = 0, 0 # PORASQUI
        if event.button == 1:
            #self.latlon_entry.set_text(
            #    'Map Centre: latitude %s longitude %s' % (
            #        self.osm.props.latitude,
            #        self.osm.props.longitude
            #    )
            #)
            pass
        elif event.button == 2:
            if OSMGPSMAP:
                self.osm.gps_add(lat, lon, heading = osmgpsmap.INVALID);
            else:
                pass    # PORASQUI
        elif event.button == 3:
            if OSMGPSMAP:
                pb = gtk.gdk.pixbuf_new_from_file_at_size(
                    os.path.join(imdir, "poi.png"), 24,24)
                self.osm.image_add(lat,lon,pb)
            else:
                pass    # PORASQUI

    def centrar_mapa(self, lat, lon, zoom = None, track = True, flag = False):
        """
        @param track Indica si se debe marcar el punto con un círculo y el 
                     "track" de recorrido.
        @param flag Indica si se debe marcar con una bandera el punto.
        """
        if lat == None: 
            raise ValueError, "Mapa.centrar_mapa -> Latitud incorrecta"
        if lon == None:
            raise ValueError, "Mapa.centrar_mapa -> Longitud incorrecta"
        if zoom is None:
            if OSMGPSMAP:
                self.osm.set_center(lat, lon)
            else:
                self.gmcw.confirm_clicked(None, None, lat, lon) 
        else:
            if OSMGPSMAP:
                self.osm.set_center_and_zoom(lat, lon, zoom)
            else:
                self.gmcw.confirm_clicked(None, None, lat, lon) 
                self.gmcw.do_zoom(zoom) 
        if track:
            if OSMGPSMAP:
                self.osm.gps_add(lat, lon, heading = osmgpsmap.INVALID);
            else:
                self.gmcw.confirm_clicked(None, None, lat, lon) 
                # PORASQUI: No support for the moment...
        if flag:
            if OSMGPSMAP:
                pb = gtk.gdk.pixbuf_new_from_file_at_size(
                    os.path.join(imdir, "poi.png"), 24, 24)
                self.osm.image_add(lat, lon, pb)
            else:
                self.gmcw.confirm_clicked(None, None, lat, lon) 
                # PORASQUI: No support for the moment...

    def put_mapa(self, container):
        #m = self.wids['mapa_container']
        m = container
        m.add(self.osm)
        m.show_all()
        if not OSMGPSMAP:   # Hay que ocultar algunas cosillas...
            for w in (self.gmcw.export_panel, 
                      self.gmcw.top_panel, 
                      self.gmcw.status_bar):
                try:
                    w.set_visible(False)
                except AttributeError:
                    w.set_property("visible", False)

    @property
    def zoom(self):
        """Nivel actual de zoom en el mapa."""
        if OSMGPSMAP:
            return self.osm.props.zoom
        else:
            return self.gmcw.get_zoom()

    def get_latlon(self, direccion):
        """
        Devuelve la latitud y longitud como flotantes correspondiente a la 
        dirección recibida. Si no se encuentra en Google Maps, devuelve 
        (None, None).
        """
        try:
            res = self.ggmap.address_to_latlng(direccion)
        except GoogleMapsError:
            res = (None, None)
        return res


def test():
    w = gtk.Window()
    m = Mapa()
    m.put_mapa(w)
    #w.show_all()
    w.connect("destroy", lambda *a, **kw: gtk.main_quit())
    gtk.main()


if __name__ == "__main__":
    test()

