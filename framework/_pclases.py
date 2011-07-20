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

    Catálogo de clases persistentes.
'''

##########
## TODO: Tengo que buscar algo cómodo en plan decorador para guardar el usuario 
## que ha creado, modificado o accedido a un objeto de pclases y la hora.
##########


DEBUG = False
#DEBUG = True   # Se puede activar desde ipython después de importar con 
                # pclases.DEBUG = True
VERBOSE = False
#VERBOSE = True  # Activar para mostrar por pantalla progreso al cargar clases.

if DEBUG or VERBOSE:
    print "IMPORTANDO PCLASES"

import os
from sqlobject import * 
import threading, datetime
from select import select
from configuracion import ConfigConexion
import notificacion
try:
    import utils
except ImportError:
    if os.path.realpath(os.path.curdir).split(os.path.sep)[-1] == "utils":
        sys.path.append("..")
    root, dirs, files = os.walk(".").next()
    if "utils" in dirs:
        sys.path.insert(0, ".")


config = ConfigConexion()

# HACK: No reconoce el puerto en el URI y lo toma como parte del host. Lo 
# añado detrás y colará en el dsn cuando lo parsee. 
conn = '%s://%s:%s@%s/%s port=%s' % (config.get_tipobd(), 
                                     config.get_user(), 
                                     config.get_pass(), 
                                     config.get_host(), 
                                     config.get_dbname(), 
                                     config.get_puerto()) 

sqlhub.processConnection = connectionForURI(conn)

# HACK:
# Hago todas las consultas case-insensitive machacando la función de 
# sqlbuilder:
_CONTAINSSTRING = sqlbuilder.CONTAINSSTRING
def CONTAINSSTRING(expr, pattern):
    try:
        nombre_clase = SQLObject.sqlmeta.style.dbTableToPythonClass(
                        expr.tableName)
        clase = globals()[nombre_clase]
        columna = clase.sqlmeta.columns[expr.fieldName]
    except (AttributeError, KeyError):
        return _CONTAINSSTRING(expr, pattern)
    if isinstance(columna, (SOStringCol, SOUnicodeCol)):
        op = sqlbuilder.SQLOp("ILIKE", expr, 
                                '%' + sqlbuilder._LikeQuoted(pattern) + '%')
    elif isinstance(columna, (SOFloatCol, SOIntCol, SODecimalCol, 
                              SOMediumIntCol, SOSmallIntCol, SOTinyIntCol)):
        try:
            pattern = str(float(pattern))
        except ValueError:
            pattern = None
        if not pattern:
            op = sqlbuilder.SQLOp("IS NOT", expr, None)
        else:
            op = sqlbuilder.SQLOp("=", expr, 
                                    sqlbuilder._LikeQuoted(pattern))
    else:
        op = sqlbuilder.SQLOp("LIKE", expr, 
                                '%' + sqlbuilder._LikeQuoted(pattern) + '%')
    return op
sqlbuilder.CONTAINSSTRING = CONTAINSSTRING


class SQLtuple(tuple):
    """
    Básicamente una tupla, pero con la función .count() para hacerla 
    "compatible" con los SelectResults de SQLObject.
    """
    def __init__(self, *args, **kw):
        self.elbicho = tuple(*args, **kw)
        tuple.__init__(*args, **kw)
    #def __new__(self, *args, **kw):
    #    self.elbicho = tuple(*args, **kw)
    #    tuple.__new__(*args, **kw)
    def count(self):
        return len(self)
    def sumFloat(self, campo):
        res = 0.0
        for item in self.elbicho:
            res += getattr(item, campo)
        return res
    def sum(self, campo):
        return self.sumFloat(campo)


class SQLlist(list):
    """
    Básicamemte una lista, pero con la función .count() para hacerla 
    "compatible" con los SelectResults de SQLObject.
    """
    def __init__(self, *args, **kw):
        self.rocio = list(*args, **kw)
        list.__init__(self, *args, **kw)
    def count(self):
        return len(self.rocio)
    # DISCLAIMER: Paso de otra clase base para solo 2 funciones que se repiten.
    def sumFloat(self, campo):
        res = 0.0
        for item in self.rocio:
            res += getattr(item, campo)
        return res
    def sum(self, campo):
        return self.sumFloat(campo)
    def append(self, *args, **kw):
        raise TypeError, "No se pueden añadir elementos a un SelectResults"
    def extend(self, *args, **kw):
        raise TypeError, "No se puede extender un SelectResults."
    def insert(self, *args, **kw):
        raise TypeError, "No se pueden insertar elementos en un SelectResults."
    def pop(self, *args, **kw):
        raise TypeError, "No se pueden eliminar elementos de un SelectResults."
    def remove(self, *args, **kw):
        raise TypeError, "No se pueden eliminar elementos de un SelectResults."


class SQLObjectChanged(Exception):
    """ User-defined exception para ampliar la funcionalidad
    de SQLObject y que soporte objetos persistentes."""
    def __init__(self, value):
        Exception.__init__(self)
        self.value = value

    def __str__(self):
        return repr(self.value)


class PRPCTOO:
    """ 
    Clase base para heredar y no repetir código.
    Únicamente implementa los métodos para iniciar un hilo de 
    sincronización y para detenerlo cuando ya no sea necesario.
    Ningún objeto de esta clase tiene utilidad "per se".
    """
    # El nombre viene de todo lo que NO hace pero para lo que es útil:
    # PersistentRemoteProcessComunicatorThreadingObservadorObservado. TOOOOOMA.
    def __init__(self, nombre_clase_derivada = ''):
        """
        El nombre de la clase derivada pasado al 
        constructor es para la metainformación 
        del hilo.
        """
        self.__oderivado = nombre_clase_derivada
        self.swap = {}

    def abrir_conexion(self):
        """
        Abre una conexión con la BD y la asigna al 
        atributo conexión de la clase.
        No sale del método hasta que consigue la
        conexión.
        """
        while 1:
            try:
                self.conexion = self._connection.getConnection()
                if DEBUG: print " --> Conexión abierta."
                return
            except:
                print "ERROR estableciendo conexión secundaria para IPC. Vuelvo a intentar"
    
    def abrir_cursor(self):
        self.cursor = self.conexion.cursor()
        if DEBUG: print [self.cursor!=None and self.cursor or "El cursor devuelto es None."][0], self.conexion, len(self.conexion.cursors)

    def make_swap(self):
        # Antes del sync voy a copiar los datos a un swap temporal, para 
        # poder comparar:
        for campo in self.sqlmeta.columns:
            self.swap[campo] = getattr(self, campo)
        
    def comparar_swap(self):
        """
        Lanza una excepción propia para indicar que algún valor ha cambiado 
        remotamente en el objeto, comparando la caché en memoria local con 
        los valores de la BD. Como mensaje de la excepción devuelve el nombre 
        del campo que ha cambiado.
        Si han cambiado varios, saltará con el primero de ellos.
        """
        # Y ahora sincronizo:
        self.sync()
        # y comparo:
        for campo in self.sqlmeta.columns:
            if DEBUG: print self.swap[campo], eval('self.%s' % campo) 
            if self.swap[campo] != getattr(self, campo): 
                raise SQLObjectChanged(self)

    def cerrar_cursor(self):
        self.cursor.close()

    def cerrar_conexion(self):
        self.conexion.close()
        if DEBUG: print " <-- Conexión cerrada."

    ## Código del hilo:
    def esperarNotificacion(self, nomnot, funcion=lambda: None):
        """
        Código del hilo que vigila la notificación.
        self -> Objeto al que pertenece el hilo.
        nomnot es el nombre de la notificación a esperar.
        funcion es una función opcional que será llamada cuando se
        produzca la notificación.
        """
        if DEBUG: print "Inicia ejecución hilo"
        while self != None and self.continuar_hilo:
            if DEBUG: print "Entra en la espera bloqueante: %s" % nomnot
            self.abrir_cursor()
            self.cursor.execute("LISTEN %s;" % nomnot)
            self.conexion.commit()
            if select.select([self.cursor], [], [])!=([], [], []):
                if DEBUG: print "Notificación recibida"
                try:
                    self.comparar_swap()
                except SQLObjectChanged:
                    if DEBUG: 
                        print "pclases::esperarNotificacion -> Objeto cambiado"
                    funcion()
                except SQLObjectNotFound:
                    if DEBUG: print "Registro borrado"
                    funcion()
                # self.cerrar_cursor()
        else:
            if DEBUG: print "Hilo no se ejecuta"
        if DEBUG: print "Termina ejecución hilo"

    def chequear_cambios(self):
        try:
            self.comparar_swap()
            # print "NO CAMBIA"
        except SQLObjectChanged:
            # print "CAMBIA"
            if DEBUG: print "pclases::chequear_cambios -> Objeto cambiado",
            if DEBUG: print self.notificador
            self.notificador.run()
        except SQLObjectNotFound:
            if DEBUG: print "Registro borrado"
            self.notificador.run()

    def ejecutar_hilo(self):
        ## ---- Código para los hilos:
        self.abrir_conexion()
        self.continuar_hilo = True
        nombre_clase = self.__oderivado
        self.th_espera = threading.Thread(target = self.esperarNotificacion, 
                    args = ("IPC_%s" % nombre_clase, self.notificador.run), 
                    name="Hilo-%s" % nombre_clase)
        self.th_espera.setDaemon(1)
        self.th_espera.start()

    def parar_hilo(self):
        self.continuar_hilo = False
        if DEBUG: print "Parando hilo..."
        self.cerrar_conexion()

    def destroy_en_cascada(self):
        """
        Destruye recursivamente los objetos que dependientes y 
        finalmente al objeto en sí.
        OJO: Es potencialmente peligroso y no ha sido probado en profundidad.
             Puede llegar a provocar un RuntimeError por alcanzar la 
             profundidad máxima de recursividad intentando eliminarse en 
             cascada a sí mismo por haber ciclos en la BD. 
        """
        for join in self.sqlmeta.joins:
            lista = join.joinMethodName
            for dependiente in getattr(self, lista):
            # for dependiente in eval("self.%s" % (lista)):
                if DEBUG:
                    print "Eliminando %s..." % dependiente
                dependiente.destroy_en_cascada()
        self.destroySelf()

    def copyto(self, obj, eliminar = False):
        """
        Copia en obj los datos del objeto actual que en obj sean 
        nulos.
        Enlaza también las relaciones uno a muchos para evitar 
        violaciones de claves ajenas, ya que antes de terminar, 
        si "eliminar" es True se borra el registro de la BD.
        PRECONDICIÓN: "obj" debe ser del mismo tipo que "self".
        POSTCONDICIÓN: si "eliminar", self debe quedar eliminado.
        """
        DEBUG = False
        assert type(obj) == type(self) and obj != None, "Los objetos deben pertenecer a la misma clase y no ser nulos."
        for nombre_col in self.sqlmeta.columns:
            valor = getattr(obj, nombre_col)
            if valor == None or (isinstance(valor, str) and valor.strip() == ""):
                if DEBUG:
                    print "Cambiando valor de columna %s en objeto destino." % (nombre_col)
                setattr(obj, nombre_col, getattr(self, nombre_col))
        for col in self.sqlmeta.joins:
            atributo_lista = col.joinMethodName
            lista_muchos = getattr(self, atributo_lista)
            nombre_clave_ajena = repr(self.__class__).replace("'", ".").split(".")[-2] + "ID" # HACK (y de los feos)
            nombre_clave_ajena = nombre_clave_ajena[0].lower() + nombre_clave_ajena[1:]       # HACK (y de los feos)
            for propagado in lista_muchos:
                if DEBUG:
                    print "Cambiando valor de columna %s en objeto destino." % (nombre_clave_ajena)
                    print "   >>> Antes: ", getattr(propagado, nombre_clave_ajena)
                setattr(propagado, nombre_clave_ajena, obj.id)
                if DEBUG:
                    print "   >>> Después: ", getattr(propagado, nombre_clave_ajena)
        if eliminar:
            try:
                self.destroySelf()
            except:     # No debería. Pero aún así, me aseguro de que quede 
                        # eliminado (POSTCONDICIÓN).
                self.destroy_en_cascada()

    def clone(self, *args, **kw):
        """
        Crea y devuelve un objeto idéntico al actual.
        Si se pasa algún parámetro adicional se intentará enviar 
        tal cual al constructor de la clase ignorando los 
        valores del objeto actual para esos parámetros.
        """
        parametros = {}
        for campo in self.sqlmeta.columns:
            valor = getattr(self, campo)
            parametros[campo] = valor
        for campo in kw:
            valor = kw[campo]
            parametros[campo] = valor
        nuevo = self.__class__(**parametros)
        return nuevo

    # PLAN: Hacer un full_clone() que además de los atributos, clone también 
    # los registros relacionados.

    def get_info(self):
        """
        Devuelve información básica (str) acerca del objeto. Por ejemplo, 
        si es un pedido de venta, devolverá el número de pedido, fecha y 
        cliente.
        Este método se hereda por todas las clases y debería ser redefinido.
        """
        res = "%s ID %d (PUID %s)" % (self.sqlmeta.table, self.id, 
                                      self.get_puid())
        return res

    def get_puid(self):
        """
        Devuelve un identificador único (¿único? I don't think so) para toda 
        la base de datos.
        Las clases pueden redefinir este método. Y de hecho deberían de acorde 
        a la lógica de negocio.
        """
        pre = self.__class__.__name__
        id = self.id
        puid = "%s:%d" % (pre, id)
        return puid

    puid = property(get_puid)


def starter(objeto, *args, **kw):
    """
    Método que se ejecutará en el constructor de todas las 
    clases persistentes.
    Inicializa el hilo y la conexión secundaria para IPC, 
    así como llama al constructor de la clase padre SQLObject.
    """
    objeto.continuar_hilo = False
    objeto.notificador = notificacion.Notificacion(objeto)
    SQLObject._init(objeto, *args, **kw)
    PRPCTOO.__init__(objeto, objeto.sqlmeta.table)
    objeto.make_swap()  # Al crear el objeto hago la primera caché de datos, 
                        # por si acaso la ventana se demora mucho e intenta 
                        # compararla antes de crearla.

def getObjetoPUID(puid):
    """
    Intenta determinar la clase del objeto a partir de la primera parte del 
    PUID y devuelve el objeto en sí o lanzará una excepción.
    """
    tipo, id = puid.split(":")
    try:
        clase = eval(tipo)
    except:
        txtve = "pclases::getObjetoPUID -> La primera parte del PUID debe "\
                "ser una clase de pclases."
        raise ValueError, txtve
    id = int(id)
    objeto = clase.get(id)
    return objeto

#### Funciones auxiliares ####################################################
def orden_por_campo_o_id(objeto1, objeto2, campo):
    """
    Ordena por el campo recibido e ID. «campo» tiene preferencia.
    objeto1 < objeto2 si objeto1 tiene valor de campo o su ID es menor.
    """
    if hasattr(objeto1, campo) and getattr(objeto1, campo) != None and \
       hasattr(objeto2, campo) and getattr(objeto2, campo) != None:
        if getattr(objeto1, campo) < getattr(objeto2, campo):
            return -1
        if getattr(objeto1, campo) > getattr(objeto2, campo):
            return 1
        return 0
    elif hasattr(objeto1, campo) and getattr(objeto1, campo) != None and \
         hasattr(objeto2, campo) and getattr(objeto2, campo) == None:
        return -1
    elif hasattr(objeto1, campo) and getattr(objeto1, campo) == None and \
         hasattr(objeto2, campo) and getattr(objeto2, campo) != None:
        return 1
    elif hasattr(objeto1, campo) and getattr(objeto1, campo) == None and \
         hasattr(objeto2, campo) and getattr(objeto2, campo) == None:
        if objeto1.id < objeto2.id:
            return -1
        elif objeto1.id > objeto2.id:
            return 1
        return 0
    return 0


#### Clases auxiliares #######################################################
class Modulo(SQLObject, PRPCTOO):
    _connection = conn
    _fromDatabase = True
    ventanas = MultipleJoin('Ventana')

    class sqlmeta:
        fromDatabase = True

    def _init(self, *args, **kw):
        starter(self, *args, **kw)


class Ventana(SQLObject, PRPCTOO):
    permisos = MultipleJoin('Permiso')
    class sqlmeta:
        fromDatabase = True
    
    def _init(self, *args, **kw):
        starter(self, *args, **kw)


class Permiso(SQLObject, PRPCTOO):
    class sqlmeta:
        fromDatabase = True

    def _init(self, *args, **kw):
        starter(self, *args, **kw)


class Usuario(SQLObject, PRPCTOO):
    permisos = MultipleJoin('Permiso')
    alertas = MultipleJoin("Alerta")
    class sqlmeta:
        fromDatabase = True

    def _init(self, *args, **kw):
        starter(self, *args, **kw)

    def get_permisos(self, ventana):
        """
        Devuelve el registro permiso del usuario sobre 
        la ventana "ventana" o None si no se encuentra.
        """
        try:
            # return [p for p in self.permisos if p.ventana == ventana][0]
            query = """
                    SELECT id FROM permiso 
                    WHERE ventana_id = %d AND usuario_id = %d;
                    """ % (ventana.id, self.id)
            id = self.__class__._connection.queryOne(query)[0]
            permiso = Permiso.get(id)
            return permiso
        except (IndexError, TypeError):
            return None
    
    def set_permisos(self, ventana, cadena = "", 
                                   permiso = True, 
                                   lectura = False, 
                                   escritura = False, 
                                   nuevo = False):
        """
        Actualiza o crea los permisos del usuario para la ventana recibida.
        Los permisos se pueden recibir como cadena -tiene prioridad sobre el 
        resto de parámetros- en «permiso» o como booleanos en:
        «permiso» -> Si True, aparece en el menú del usuario. Implícito 
                     siempre a True si alguno de los otros 3 permisos se 
                     especifica.
        «lectura» -> Si True el usuario puede buscar registros en la ventana.
        «escritura» -> Si True puede modificar registros.
        «nuevo» -> Si True, puede crear registros.
        En «cadena» se pueden recibir los permisos como una combinación de las 
        letras "r", "w" y "x"; representando lectura, escritura y nuevo.
        """
        cadena = cadena.lower()
        lectura = lectura or "r" in cadena
        escritura = escritura or "w" in cadena
        nuevo = nuevo or "x" in cadena
        permiso = permiso or (lectura or escritura or nuevo)
        try:
            p = Permiso.select(AND(Permiso.q.usuario == self, 
                                   Permiso.q.ventana == ventana))[0]
        except IndexError:
            p = Permiso(usuario = self, ventana = ventana)
        p.permiso = permiso
        p.lectura = lectura
        p.escritura = escritura
        p.nuevo = nuevo
        p.syncUpdate()

    def cambiar_password(self, nueva):
        """
        Cambia la contraseña por la nueva recibida.
        """
        from hashlib import md5
        self.passwd = md5(nueva).hexdigest()
        self.syncUpdate()

    def enviar_mensaje(self, texto, permitir_duplicado = False):
        """
        Envía un nuevo mensaje al usuario creando una 
        alerta pendiente para el mismo.
        Si permitir_duplicado es False, se buscan los mensajes 
        con el mismo texto que se intenta enviar. En caso de 
        que exista, solo se actualizará la hora de la alerta 
        y se pondrá el campo "entregado" a False.
        Si es True, se envía el nuevo mensaje aunque pudiera 
        estar duplicado.
        """
        mensajes = Alerta.select(AND(Alerta.q.mensaje == texto, 
                                     Alerta.q.usuarioID == self.id))
        if not permitir_duplicado:
            for m in mensajes:
                m.destroySelf()
        a = Alerta(usuario = self, mensaje = texto, entregado = False)

    def get_info(self):
        res = self.usuario
        if self.nombre:
            res += " (" + self.nombre + ")"
        return res


class Estadistica(PRPCTOO, SQLObject):
    """
     # PyUML: Do not remove this line! # XMI_ID:_XWRUQ-5DEd-QvZvwvxUy6Q
    """
    class sqlmeta:
        fromDatabase = True

    def _init(self, *args, **kw):
        starter(self, *args, **kw)

    def incrementar(usuario, ventana):
        if isinstance(usuario, int):
            usuario_id = usuario
        else:
            usuario_id = usuario.id
        if isinstance(ventana, int):
            ventana_id = ventana
        elif isinstance(ventana, str):
            try:
                ventana = Ventana.selectBy(fichero = ventana)[0]
                ventana_id = ventana.id
            except Exception, msg:
                print "pclases::Estadistica::incrementar -> Ventana '%s' no encontrada. Excepción: %s" % (ventana, msg)
                return
        else:
            ventana_id = ventana.id
        st = Estadistica.select(AND(Estadistica.q.usuario == usuario_id, Estadistica.q.ventana == ventana_id))
        if not st.count():
            st = Estadistica(usuario = usuario_id, 
                             ventana = ventana_id)
        else:
            if st.count() > 1:
                sts = list(st)
                st = sts[0]
                for s in sts[1:]:
                    st.veces += s.veces
                    s.destroySelf()
            st = st[0]
        st.ultimaVez = datetime.datetime.now()
        st.veces += 1
        st.sync()

    incrementar = staticmethod(incrementar)

#### Clases del ORM en sí ####################################################
class Empleado(SQLObject, PRPCTOO):
    muestras = MultipleJoin("Muestra")   
    fotos = MultipleJoin("Foto")
    adjuntos = MultipleJoin("Adjunto")
    class sqlmeta:
        fromDatabase = True

    def _init(self, *args, **kw):
        starter(self, *args, **kw)

    def get_nombre_completo(self, apellidos_primero = False):
        """
        Devuelve el nombre completo del empleado en la forma Nombre Apellidos.
        @param apellidos_primero: Si es True, pues al contrario y con una coma.
        """
        res = self.nombre
        if res: 
            if self.apellidos:
                if apellidos_primero:
                    res = self.apellidos + ", " + res
                else:
                    res += " " + self.apellidos
        else:
            res = self.apellidos
        if not res:
            res = super(Empleado, self).get_info()
        return res


class Solicitante(SQLObject, PRPCTOO):
    solicitantes = MultipleJoin("AlbaranEntrada")   
    class sqlmeta:
        fromDatabase = True

    def _init(self, *args, **kw):
        starter(self, *args, **kw)

    def get_nombre_completo(self, apellidos_primero = False):
        """
        Devuelve el nombre completo del empleado en la forma Nombre Apellidos.
        @param apellidos_primero: Si es True, pues al contrario y con una coma.
        """
        res = self.nombre
        if res: 
            if self.apellidos:
                if apellidos_primero:
                    res = self.apellidos + ", " + res
                else:
                    res += " " + self.apellidos
        else:
            res = self.apellidos
        if not res:
            res = super(Empleado, self).get_info()
        return res


class Cliente(SQLObject, PRPCTOO):
    obras = MultipleJoin("Obra")
    pedidosVenta = MultipleJoin("PedidoVenta")
    class sqlmeta:
        fromDatabase = True

    def _init(self, *args, **kw):
        starter(self, *args, **kw)


class Obra(SQLObject, PRPCTOO):
    muestras = MultipleJoin("Muestra")
    class sqlmeta:
        fromDatabase = True

    def _init(self, *args, **kw):
        starter(self, *args, **kw)


class AlbaranEntrada(SQLObject, PRPCTOO):
    muestras = MultipleJoin("Muestra")
    class sqlmeta:
        fromDatabase = True

    def _init(self, *args, **kw):
        starter(self, *args, **kw)


class LibroRegistro(SQLObject, PRPCTOO):
    muestras = MultipleJoin("Muestra")
    class sqlmeta:
        fromDatabase = True

    def _init(self, *args, **kw):
        starter(self, *args, **kw)


class CentroTrabajo(SQLObject, PRPCTOO):
    muestras = MultipleJoin("Muestra")
    class sqlmeta:
        fromDatabase = True

    def _init(self, *args, **kw):
        starter(self, *args, **kw)


class Material(SQLObject, PRPCTOO):
    muestras = MultipleJoin("Muestra")
    ensayos= MultipleJoin("Ensayo")
    class sqlmeta:
        fromDatabase = True

    def _init(self, *args, **kw):
        starter(self, *args, **kw)

    def get_info(self):
        return self.nombre

class Muestra(SQLObject, PRPCTOO):
    resultados = MultipleJoin("Resultado")
    class sqlmeta:
        fromDatabase = True

    def _init(self, *args, **kw):
        starter(self, *args, **kw)
    
    def get_info(self):
        if self.codigo and self.codigo.strip():
            res = "Muestra código %s" % self.codigo
        else:
            res = "Muestra %d" % self.id
        if self.empleado:
            res += " recogida por %s" % self.empleado.get_nombre_completo()
        return res

class Ensayo(SQLObject, PRPCTOO):
    resultados = MultipleJoin("Resultado")
    class sqlmeta:
        fromDatabase = True

    def _init(self, *args, **kw):
        starter(self, *args, **kw)

    def get_info(self):
        return "%d: %s" % (self.codigo, self.nombre)


class Resultado(SQLObject, PRPCTOO):
    adjuntos = MultipleJoin("Adjunto")
    class sqlmeta:
        fromDatabase = True
    
    def _init(self, *args, **kw):
        starter(self, *args, **kw)
    
    def get_info(self):
        return "%s (%d)" % (utils.fecha.str_fecha(self.fecha), self.id)
        
            
class Capitulo(SQLObject, PRPCTOO):
    subcapitulos = MultipleJoin("Capitulo")
    ensayos = MultipleJoin("Ensayo")
    class sqlmeta:
        fromDatabase = True
    
    def _init(self, *args, **kw):
        starter(self, *args, **kw)
        
        
class DatosDeLaEmpresa(SQLObject, PRPCTOO):
    
    class sqlmeta:
        fromDatabase = True

    def _init(self, *args, **kw):
        starter(self, *args, **kw)

    def get_ruta_completa_logo(self):
        """
        Devuelve la ruta completa al logotipo de datos de la empresa.
        Si no tiene logo, devuelve None.
        """
        im = os.path.join("..", "imagenes", self.logo)
        return os.path.abspath(im)

    def get_propia_empresa_como_cliente(clase): 
        """
        Devuelve el registro cliente de la BD que se corresponde 
        con la empresa atendiendo a los datos del registro DatosDeLaEmpresa
        o None si no se encuentra.
        """
        nombre_propia_empresa = clase.select()[0].nombre
        clientes = Cliente.select(Cliente.q.nombre == nombre_propia_empresa)
        if clientes.count() == 0:
            cliente = None
        elif clientes.count() == 1:
            cliente = clientes[0]
        else:   # >= 2
            print "pclases.py: DatosDeLaEmpresa::get_propia_empresa_como_cliente: Más de un posible cliente encontrado. Selecciono el primero."
            cliente = clientes[0]
        return cliente
    get_propia_empresa_como_cliente = staticmethod(get_propia_empresa_como_cliente)

    def get_propia_empresa_como_proveedor(clase): 
        """
        Devuelve el registro proveedor que se corresponde con la 
        empresa atendiendo a los datos del registro DatosDeLaEmpresa 
        o None si no se encuentra.
        """
        # TODO: Todavía no tengo proveedores en esta versión.
        #nombre_propia_empresa = clase.select()[0].nombre
        #proveedores = Proveedor.select(Proveedor.q.nombre == nombre_propia_empresa)
        proveedores = SQLtuple()
        if proveedores.count() == 0:
            proveedor = None
        elif proveedores.count() == 1:
            proveedor = proveedores[0]
        else:   # >= 2
            print "pclases.py: DatosDeLaEmpresa::get_propia_empresa_como_proveedor: Más de un posible proveedor encontrado. Selecciono el primero."
            proveedor = proveedores[0]
        return proveedor
    get_propia_empresa_como_proveedor = staticmethod(get_propia_empresa_como_proveedor)
    
    get_cliente = staticmethod(get_propia_empresa_como_cliente)
    get_proveedor = staticmethod(get_propia_empresa_como_proveedor)

    def str_cif_o_nif(self):
        """
        Devuelve la cadena "N.I.F." o "C.I.F." dependiendo de si el atributo 
        «cif» de la empresa es un N.I.F. (aplicable a personas) o C.I.F. 
        (aplicable a empresas).
        """
        try:
            return self.cif[0].isalpha() and "C.I.F." or "N.I.F."
        except IndexError:
            return ""


class Adjunto(SQLObject, PRPCTOO):
    
    class sqlmeta:
        fromDatabase = True

    def _init(self, *args, **kw):
        starter(self, *args, **kw)

    def get_info(self):
        """
        Devuelve ID, nombre y ruta del documento.
        """
        return "Adjunto ID %d: %s (%s)" % (self.id, self.nombre, self.ruta)

    def get_ruta_base():
        """
        Devuelve la ruta del directorio que contiene los documentos adjuntos.
        Se asegura cada vez que es consultada que el directorio existe.
        """
        # Siempre se trabaja en un subdirectorio del raíz del programa. 
        # Normalmente formularios o framework.
        # Por tanto lo primero que hago es salir del subdirectorio para 
        # buscar el de documentos adjuntos.
        from utils.fichero import get_raiz_como_ruta_relativa
        RUTA_BASE = config.get_dir_adjuntos()
        RUTA_BASE = os.path.join(get_raiz_como_ruta_relativa(), RUTA_BASE)
        try:
            assert os.path.exists(RUTA_BASE)
        except AssertionError:
            os.mkdir(RUTA_BASE)
        return RUTA_BASE
    get_ruta_base = staticmethod(get_ruta_base)
    
    ruta_base = get_ruta_base = staticmethod(get_ruta_base)

    def get_ruta_completa(self):
        """
        Devuelve la ruta completa al fichero: directorio base + nombre 
        del fichero.
        """
        return os.path.join(Adjunto.get_ruta_base(), self.nombreFichero)

    def copiar_a_diradjuntos(ruta):
        """
        Copia el fichero de la ruta al directorio de adjuntos.
        """
        import shutil
        try:
            shutil.copy(ruta, Adjunto.get_ruta_base())
            res = True
        except Exception, msg:
            print "pclases::Adjunto::copiar_a_diradjuntos -> Excepción %s"\
                   % msg
            res = False
        return res

    copiar_a_diradjuntos = staticmethod(copiar_a_diradjuntos)

    def adjuntar(ruta, objeto, nombre = ""):
        """
        Adjunta el fichero del que recibe la ruta con el objeto
        del segundo parámetro.
        Si no puede determinar la clase del objeto o no está 
        soportado en la relación, no crea el registro documento
        y devuelve None.
        En otro caso devuelve el objeto Adjunto recién creado.
        """
        res = None
        if objeto != None and os.path.exists(ruta):
            objeto_relacionado = None
            param_clase = objeto.__class__.__name__
            param_clase = param_clase[0].lower() + param_clase[1:]
            kw = {param_clase: objeto}
            nombreFichero = os.path.split(ruta)[-1]
            if Adjunto.copiar_a_diradjuntos(ruta):
                try:
                    nuevoDoc = Adjunto(nombre = nombre, 
                                       nombreFichero = nombreFichero, 
                                       **kw)
                except TypeError, msg:
                    txterror = "pclases::Adjunto::adjuntar -> "\
                               "%s no es un tipo válido.\n\tTypeError: %s" % (
                                    type(objeto), msg)
                    raise TypeError, txterror 
                res = nuevoDoc
        return res

    adjuntar = staticmethod(adjuntar)


class Alerta(SQLObject, PRPCTOO):
    class sqlmeta:
        fromDatabase = True

    def _init(self, *args, **kw):
        starter(self, *args, **kw)


class Foto(SQLObject, PRPCTOO):
    class sqlmeta:
        fromDatabase = True

    def _init(self, *args, **kw):
        starter(self, *args, **kw)

    def get_pixbuf(self, maximo):
        """
        Devuelve una GtkImage de la foto del empleado o de la foto por 
        defecto si no tiene.
        Si maximo != None reescala la imagen para que ninguna de sus dos 
        dimensiones supere esa cantidad
        """
        if self.data:
            impil = foto.to_pil()
        else:
            from PIL import Image
            impil = Image.open(os.path.join("..", "imagenes", "users.png"))
        ancho, alto = impil.size
        escala = (float(maximo) / max(ancho, alto))
        impil = impil.resize((int(ancho * escala), 
                              int(alto * escala)), 
                              resample = 1)
        pixbuf = utils.image2pixbuf(impil)
        return pixbuf

        def _set_data(self, value):
            self._SO_set_data(value.encode('base64'))

        def _get_data(self):
            return self._SO_get_data().decode('base64')

        def save_to_temp(self):
            """
            Guarda la imagen en un temporal y devuelve la ruta a la misma.
            """
            # OJO: 1.- No chequea que no haya imagen almacenada.
            #      2.- No chequea que no exista una imagen con el mismo 
            #          nombre o que no pueda escribir a disco por falta de 
            #          espacio, etc.
            from tempfile import gettempdir
            from random import randint 
            dir = gettempdir()
            nombre = "%d" % randint(10**9, 10**10 - 1) 
            ruta = os.path.join(dir, nombre)
            f = open(ruta, "wb")
            f.write(self.data)
            f.close()
            return ruta

        def to_pil(self):
            """
            Devuelve una imagen PIL a partir del BLOB guardado.
            """
            from PIL import Image
            path_tmp_im = self.save_to_temp()
            im = Image.open(path_tmp_im)
            return im

        def store_from_file(self, ruta):
            """
            Guarda la imagen especificada por la ruta en la base de datos.
            """
            self.data = ""
            f = open(ruta, "rb")
            binchunk = f.read()
            while binchunk:
                self.data += binchunk
                binchunk = f.read()
            f.close()

        def store_from_pil(self, imagen):
            """
            Guarda la imagen del objeto PIL en la base de datos.
            """
            import Image
            # PLAN
            raise NotImplementedError


class Ciudad(SQLObject, PRPCTOO):
    codigosPostales = MultipleJoin("CodigoPostal")
    class sqlmeta:
        fromDatabase = True

    def _init(self, *args, **kw):
        starter(self, *args, **kw)


class CodigoPostal(SQLObject, PRPCTOO):
    direcciones = MultipleJoin("Direccion")
    class sqlmeta:
        fromDatabase = True

    def _init(self, *args, **kw):
        starter(self, *args, **kw)


class Direccion(SQLObject, PRPCTOO):
    pedidosVenta = MultipleJoin("PedidoVenta")
    clientes = MultipleJoin("Cliente")
    obras = MultipleJoin("Obra")
    empleados = MultipleJoin("Empleado")
    class sqlmeta:
        fromDatabase = True

    def _init(self, *args, **kw):
        starter(self, *args, **kw)


class Pais(SQLObject, PRPCTOO):
    direcciones = MultipleJoin("Direccion")
    class sqlmeta:
        fromDatabase = True

    def _init(self, *args, **kw):
        starter(self, *args, **kw)


class PedidoVenta(SQLObject, PRPCTOO):
    class sqlmeta:
        fromDatabase = True

    def _init(self, *args, **kw):
        starter(self, *args, **kw)


class Provincia(SQLObject, PRPCTOO):
    ciudades = MultipleJoin("Ciudad")
    class sqlmeta:
        fromDatabase = True

    def _init(self, *args, **kw):
        starter(self, *args, **kw)

class TipoFactura(SQLObject, PRPCTOO):
    facturasVenta = MultipleJoin("FacturaVenta")
    class sqlmeta:
        fromDatabase = True

    def _init(self, *args, **kw):
        starter(self, *args, **kw)


class SerieNumerica(PRPCTOO, SQLObject):
    """
     # PyUML: Do not remove this line! # XMI_ID:_XWkPMe5DEd-QvZvwvxUy6Q
    """
    facturasVenta = MultipleJoin("FacturaVenta")
    tiposFactura = MultipleJoin("TipoFactura")
    class sqlmeta:
        fromDatabase = True

    def _init(self, *args, **kw):
        starter(self, *args, **kw)

    def get_next_numfactura(self, commit = False, inc = 1):
        """
        Por defecto devuelve el que sería el siguiente número 
        de factura. Si commit = True entonces sí lo hace 
        efectivo y corre el contador de la serie.
        "inc" es el número en que avanza el contador. Por defecto 1.
        No tiene en cuenta las fechas de aplicación de la serie.
        """
        self.sync()
        # CWT: El número entre prefijo y sufijo pasa a tener 4 dígitos como 
        # mínimo
        numfactura = "%s%04d%s" % (self.prefijo, 
                                   self.contador - 1 + inc, 
                                   self.sufijo)
        if commit:
            self.contador += inc
            self.syncUpdate()
        return numfactura

    def get_last_factura_creada(self):
        """
        Devuelve la última factura creada según el orden del campo numfactura.
        None si no hay facturas de la serie (ninguna factura coincide en 
        prefijo ni sufijo).
        """
        self.sync()
        fras = self.FacturasVenta
        fras.sort(key = lambda f: f.numfactura, reverse = True)
        try:
            return fras[0]
        except IndexError:
            return None

    def get_last_numfactura_creada(self):
        """
        Devuelve la última factura creada de la serie según el orden del 
        campo numfactura, no el de ID ni el de la tabla de la BD.
        Si no hay facturas en la serie, devuelve la cadena vacía.
        """
        ultima_fra = self.get_last_factura_creada()
        if ultima_fra:
            return ultima_fra.numfactura
        return ""
 
class FacturaVenta(PRPCTOO, SQLObject):
    """
     # PyUML: Do not remove this line! # XMI_ID:_XWmEYe5DEd-QvZvwvxUy6Q
    """
    class sqlmeta:
        fromDatabase = True

    def _init(self, *args, **kw):
        starter(self, *args, **kw)

