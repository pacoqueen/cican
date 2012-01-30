--#############################################################################
-- Copyright (C) 2009, 2010 Francisco José Rodríguez Bogado                   #
--                          <frbogado@novawwe.es>                             #
-- TODO: Aquí va la licencia.                                                 #
--#############################################################################

----------------------------------
-- Script de creación de tablas --
----------------------------------
CREATE TABLE unidad_de_medida(
    id SERIAL PRIMARY KEY, 
    propiedad_fisica TEXT DEFAULT '', 
    unidad TEXT DEFAULT '', 
    abreviatura TEXT DEFAULT ''
);

CREATE TABLE producto(
    id SERIAL PRIMARY KEY, 
    unidad_de_medida_id INT REFERENCES unidad_de_medida DEFAULT NULL,
    codigo TEXT DEFAULT '', 
    descripcion TEXT DEFAULT '', 
    precio_defecto FLOAT DEFAULT 0.0, 
    inventariable BOOLEAN DEFAULT TRUE, 
    existencias FLOAT DEFAULT 0.0,  -- No hago distinción de almacenes.
    observaciones TEXT DEFAULT ''
);

-- Lo de separar los servicios es un follón para el usuario. De momento 
-- mantendré solo una tabla de productos hasta que no me quede más remedio. 
-- Ni siquiera voy a hacer la distinción de productos de venta/compra.
--CREATE TABLE servicio(
--    id SERIAL PRIMARY KEY, 
--    descripcion TEXT DEFAULT '', 
--    precio_defecto FLOAT DEFAULT 0.0
--);

CREATE TABLE pais(
    id SERIAL PRIMARY KEY, 
    pais TEXT NOT NULL DEFAULT '', 
    codigo TEXT DEFAULT ''
);

CREATE TABLE provincia(
    id SERIAL PRIMARY KEY, 
    pais_id INT REFERENCES pais DEFAULT NULL, 
    provincia TEXT NOT NULL DEFAULT '', 
    prefijo CHAR(3) DEFAULT '', 
    codigo CHAR(2) DEFAULT ''
);

CREATE TABLE ciudad(
    id SERIAL PRIMARY KEY, 
    provincia_id INT REFERENCES provincia DEFAULT NULL, 
    ciudad TEXT NOT NULL DEFAULT '', 
    codigo_municipio TEXT DEFAULT '' 
);

CREATE TABLE codigo_postal(
    id SERIAL PRIMARY KEY, 
    ciudad_id INT REFERENCES ciudad DEFAULT NULL, 
    cp TEXT NOT NULL DEFAULT ''
);
------------------------------------------
-- Direcciones de envío, de clientes... --
------------------------------------------
CREATE TABLE tipo_de_via(
    id SERIAL PRIMARY KEY, 
    tipo_de_via TEXT DEFAULT ''
);

CREATE TABLE direccion(
    id SERIAL PRIMARY KEY, 
    codigo_postal_id INT REFERENCES codigo_postal DEFAULT NULL,
    ciudad_id INT REFERENCES ciudad,
    pais_id INT REFERENCES pais,
    tipo_de_via_id INT REFERENCES tipo_de_via DEFAULT NULL, 
    direccion TEXT DEFAULT '', 
    numero TEXT DEFAULT '', 
    portal TEXT DEFAULT '', 
    piso TEXT DEFAULT '', 
    puerta TEXT DEFAULT '', 
    observaciones TEXT DEFAULT '',
    lat FLOAT DEFAULT NULL, 
    lon FLOAT DEFAULT NULL 
);

--------------------------
-- Categorías laborales -- 
--------------------------
CREATE TABLE categoria_laboral(
    id SERIAL PRIMARY KEY, 
    nombre TEXT DEFAULT 'Nueva categoría laboral', 
    laborante BOOLEAN DEFAULT FALSE -- Laborantes trabajan en laboratorio, 
                                    -- pueden ir a recoger material y hacer 
                                    -- análisis.
);

CREATE TABLE centro_trabajo(
    id SERIAL PRIMARY KEY, 
    direccion_id INT REFERENCES direccion DEFAULT NULL, 
    nombre TEXT DEFAULT 'Nuevo centro de trabajo'
);

CREATE TABLE empleado(
    id SERIAL PRIMARY KEY, 
    direccion_id INT REFERENCES direccion DEFAULT NULL, 
    categoria_laboral_id INT REFERENCES categoria_laboral DEFAULT NULL, 
    centro_trabajo_id INT REFERENCES centro_trabajo DEFAULT NULL, 
    dni TEXT DEFAULT '00000000T', 
    nombre TEXT DEFAULT 'Nuevo empleado', 
    apellidos TEXT DEFAULT '' 
);

----------------------------------
-- Series numéricas de facturas --
----------------------------------
CREATE TABLE serie_numerica(
    id SERIAL PRIMARY KEY, 
    prefijo TEXT DEFAULT '', 
    contador INT DEFAULT 1, 
    sufijo TEXT DEFAULT '', 
    fecha_inicio DATE DEFAULT NULL,     -- Si procede, fechas de inicio y fin 
    fecha_fin DATE DEFAULT NULL,        -- de aplicación de la serie numérica.
    cifras INT DEFAULT 4    -- 0: Sin especificar. 1: S0P, 2: S00P, 3: S000P...
);

CREATE TABLE cliente(
    id SERIAL PRIMARY KEY, 
    direccion_id INT REFERENCES direccion DEFAULT NULL, 
    serie_numerica_id INT REFERENCES serie_numerica DEFAULT NULL, 
    cif TEXT DEFAULT '', 
    nombre TEXT DEFAULT 'Nuevo cliente', 
    -- TODO: Después pensaremos en el muchos a muchos para la dirección 
    -- social, fiscal, correspondencia, etc.
    iva FLOAT DEFAULT 0.18, 
    dia_de_pago INT DEFAULT NULL,   -- 0 si no tiene uno específico. Si no, 
                                    -- el día del mes en el que paga.
    -- codigo INT UNIQUE DEFAULT NULL
    codigo TEXT DEFAULT NULL
);

CREATE TABLE contacto(
    id SERIAL PRIMARY KEY, 
    nombre TEXT DEFAULT '', 
    apellidos TEXT DEFAULT '', 
    email TEXT DEFAULT '',      -- FIXME: Sé que esto no pasa la normalización.
    telefono TEXT DEFAULT '',   -- FIXME: Esto tampoco. ¿Qué pasa si tiene 
                                --        móvil y fijo? 
    observaciones TEXT DEFAULT ''
);

CREATE TABLE clientes__contactos(
    cliente_id INT REFERENCES cliente NOT NULL, 
    contacto_id INT REFERENCES contacto NOT NULL
);

CREATE TABLE proveedor(
    id SERIAL PRIMARY KEY, 
    direccion_id INT REFERENCES direccion DEFAULT NULL, 
    -- TODO: Después pensaremos en el muchos a muchos para la dirección 
    -- social, fiscal, correspondencia, etc.
    cif TEXT DEFAULT '', 
    nombre TEXT DEFAULT 'Nuevo proveedor', 
    iva FLOAT DEFAULT 0.18, 
    dia_de_pago INT DEFAULT NULL    -- 0 si no tiene uno específico. Si no, 
                                    -- el día del mes en el que paga.
);

CREATE TABLE proveedores__contactos(
    proveedor_id INT REFERENCES proveedor NOT NULL, 
    contacto_id INT REFERENCES contacto NOT NULL
);

CREATE TABLE modo_pago(
    id SERIAL PRIMARY KEY, 
    nombre TEXT DEFAULT '', -- Transferencia, cheque, recibo, pagaré... 
    cobro_automatico BOOLEAN DEFAULT FALSE
        -- Si TRUE la cobranza se marcará como realizada (pendiente = FALSE) 
        -- automáticamente en la fecha de vencimiento.
);

CREATE TABLE periodo_pago(
    id SERIAL PRIMARY KEY, 
    nombre TEXT DEFAULT '', 
    numero_vencimientos INT DEFAULT 1, 
    dia_inicio INT DEFAULT 0,   -- Días entre la fecha de la factura y el 
                                -- primer vencimiento.
    dias_entre_vencimientos INT DEFAULT 30  -- Días que transcurrirán entre el 
                                    -- el primer vencimiento y subsiguientes.
);

CREATE TABLE forma_de_pago(
    id SERIAL PRIMARY KEY, 
    modo_pago_id INT REFERENCES modo_pago DEFAULT NULL, 
    periodo_pago_id INT REFERENCES periodo_pago DEFAULT NULL, 
    descripcion TEXT DEFAULT '', 
    retencion FLOAT DEFAULT 0.0     -- Porcentaje de retención en facturas.
);

CREATE TABLE obra(
    id SERIAL PRIMARY KEY, 
    cliente_id INT REFERENCES cliente DEFAULT NULL, 
    direccion_id INT REFERENCES direccion DEFAULT NULL, 
    forma_de_pago_id INT REFERENCES forma_de_pago DEFAULT NULL, 
    nombre TEXT DEFAULT ''
);

--CREATE TABLE solicitante(
--    id SERIAL PRIMARY KEY, 
--    nombre TEXT DEFAULT '', 
--    apellidos TEXT DEFAULT ''
--);

CREATE TABLE albaran_entrada(
    id SERIAL PRIMARY KEY, 
    contacto_id INT REFERENCES contacto DEFAULT NULL, 
    numalbaran TEXT DEFAULT '', 
    fecha DATE DEFAULT CURRENT_DATE
);

CREATE TABLE libro_registro(
    id SERIAL PRIMARY KEY, 
    numero INT DEFAULT 0, 
    ejercicio INT DEFAULT DATE_PART('year', CURRENT_DATE)
);

CREATE TABLE material(
    id SERIAL PRIMARY KEY, 
    nombre TEXT DEFAULT 'Nuevo material'
);

-----------------------------------------
-- Solicitudes de recogida de material -- 
-----------------------------------------
CREATE TABLE peticion(
    id SERIAL PRIMARY KEY, 
    -- cliente_id INT REFERENCES cliente DEFAULT NULL, 
    obra_id INT REFERENCES obra DEFAULT NULL, 
    direccion_id INT REFERENCES direccion DEFAULT NULL, 
    empleado_id INT REFERENCES empleado DEFAULT NULL, 
    material_id INT REFERENCES material DEFAULT NULL, 
    fecha_solicitud DATE DEFAULT CURRENT_DATE, 
    fecha_recogida DATE DEFAULT NULL, 
    observaciones TEXT DEFAULT '', 
    hora_recogida TIME DEFAULT CURRENT_TIME, 
    usuario_id INT REFERENCES usuario DEFAULT NULL,
    contacto_id INT REFERENCES contacto DEFAULT NULL, 
    solicitante TEXT DEFAULT '' -- Not sure about deba ser un contacto 
        -- también o incluso una FK de la tabla de solicitantes que no llegué 
        -- a crear.
);

CREATE TABLE muestra(
    id SERIAL PRIMARY KEY,
    empleado_id INT REFERENCES empleado DEFAULT NULL, 
    obra_id INT REFERENCES obra DEFAULT NULL, 
    albaran_entrada_id INT REFERENCES albaran_entrada DEFAULT NULL, 
    libro_registro_id INT REFERENCES libro_registro DEFAULT NULL, 
    centro_trabajo_id INT REFERENCES centro_trabajo DEFAULT NULL, 
    material_id INT REFERENCES material DEFAULT NULL, 
    peticion_id INT REFERENCES peticion DEFAULT NULL,  
    codigo TEXT DEFAULT '' 
);

CREATE TABLE capitulo(
    id SERIAL PRIMARY KEY, 
    nombre TEXT DEFAULT '', 
    codigo TEXT DEFAULT '', -- En la forma "2.1.3" por ejemplo. Debe tener el 
                    -- mismo número de dígitos separados por puntos que el 
                    -- entero que representa el nivel.
    nivel INT DEFAULT 0 -- 1 para subcapítulos, 2 para subsubcapítulos, and 
                        -- so on...
);

ALTER TABLE capitulo ADD COLUMN capitulo_id INT REFERENCES capitulo DEFAULT NULL;

CREATE TABLE ensayo(
    id SERIAL PRIMARY KEY,
    material_id INT REFERENCES material DEFAULT NULL,
    capitulo_id INT REFERENCES capitulo DEFAULT NULL, 
    codigo INT DEFAULT 0, 
    nombre TEXT DEFAULT 'Nuevo ensayo', 
    norma TEXT DEFAULT '', 
    numero INT DEFAULT 1,     -- Número de veces el lote, me parece.
    tamanno_lote TEXT DEFAULT '',   -- Acepta tanto números como textos en  
                                    -- plan "Tipo / Mes", "Tipo / Suelo", 
                                    -- "Origen", etc.
    unidad TEXT DEFAULT '', 
    medicion INT DEFAULT 0, 
    numero_ensayos INT DEFAULT 0,       -- Número de veces a repetir el 
                                        -- ensayo, creo.
    precio FLOAT DEFAULT 0.0            -- Precio unitario del ensayo.
    -- importe FLOAT DEFAULT NULL    -- Es campo calculado EN VERDAD. 
);

----------------------
-- Tipos de factura --
----------------------
CREATE TABLE tipo_factura(
    id SERIAL PRIMARY KEY, 
    serie_numerica_id INT REFERENCES serie_numerica DEFAULT NULL, 
    nombre TEXT NOT NULL DEFAULT '', 
    descripcion TEXT DEFAULT ''
);

-----------------------
-- Facturas de venta --
-----------------------
CREATE TABLE factura_venta(
    id SERIAL PRIMARY KEY, 
    tipo_factura_id INT REFERENCES tipo_factura DEFAULT NULL, 
    obra_id INT REFERENCES obra DEFAULT NULL, 
    serie_numerica_id INT REFERENCES serie_numerica DEFAULT NULL, 
    forma_de_pago_id INT REFERENCES forma_de_pago DEFAULT NULL, 
    numfactura TEXT UNIQUE NOT NULL DEFAULT '', 
    fecha DATE NOT NULL DEFAULT CURRENT_DATE, 
    retencion FLOAT DEFAULT 0.0, 
    observaciones TEXT DEFAULT ''
);

CREATE TABLE linea_de_venta(
    id SERIAL PRIMARY KEY, 
    producto_id INT REFERENCES producto DEFAULT NULL, 
    factura_venta_id INT REFERENCES factura_venta, 
    cantidad FLOAT DEFAULT 1.0, 
    precio FLOAT DEFAULT 0.0, 
    descuento FLOAT DEFAULT 0.0, 
    iva FLOAT DEFAULT 0.18, 
    descripcion TEXT DEFAULT ''
);

----------------------
-- Pedidos de venta --
----------------------
-- Solicitud de recogida de material, compras, servicios...
-- XXX: Creo que no me va a hacer falta nunca más teniendo la tabla «oferta».
-- CREATE TABLE pedido_venta(
--    id SERIAL PRIMARY KEY,
--    cliente_id INT REFERENCES cliente DEFAULT NULL,
--    direccion_id INT REFERENCES direccion DEFAULT NULL, -- Dirección de 
--        -- envío. Por si no tiene obra.
--    obra_id INT REFERENCES obra DEFAULT NULL, 
--    fecha DATE DEFAULT CURRENT_DATE,
--    numpedido TEXT DEFAULT ''
--);

CREATE TABLE pedido_compra(
    id SERIAL PRIMARY KEY, 
    proveedor_id INT REFERENCES proveedor DEFAULT NULL, 
    fecha DATE DEFAULT CURRENT_DATE
);

CREATE TABLE factura_compra(
    id SERIAL PRIMARY KEY, 
    forma_de_pago_id INT REFERENCES forma_de_pago DEFAULT NULL, 
    numfactura TEXT DEFAULT '', 
    fecha DATE NOT NULL DEFAULT CURRENT_DATE, 
    observaciones TEXT DEFAULT ''
);

CREATE TABLE linea_de_compra(
    id SERIAL PRIMARY KEY, 
    factura_compra_id INT REFERENCES factura_compra, 
    concepto TEXT DEFAULT '', 
    cantidad FLOAT DEFAULT 1.0, 
    precio FLOAT DEFAULT 0.0, 
    descuento FLOAT DEFAULT 0.0, 
    iva FLOAT DEFAULT 0.18 
);

CREATE TABLE pago(
    id SERIAL PRIMARY KEY, 
    factura_compra_id INT REFERENCES factura_compra, 
    modo_pago_id INT REFERENCES modo_pago DEFAULT NULL, 
    documento_de_pago_id INT REFERENCES documento_de_pago DEFAULT NULL, 
    fecha DATE DEFAULT CURRENT_DATE, 
    importe FLOAT DEFAULT 0.0
);

CREATE TABLE vencimiento_pago(
    id SERIAL PRIMARY KEY, 
    factura_compra_id INT REFERENCES factura_compra, 
    modo_pago_id INT REFERENCES modo_pago, 
    fecha DATE DEFAULT CURRENT_DATE, 
    importe FLOAT DEFAULT 0.0, 
    observaciones TEXT DEFAULT ''
);


-----------------------
-- TABLAS AUXILIARES --
-----------------------
CREATE TABLE usuario(
    id SERIAL PRIMARY KEY,
    empleado_id INT REFERENCES empleado DEFAULT NULL, 
    usuario VARCHAR(16) UNIQUE NOT NULL CHECK (usuario <> ''), -- Usuario de
                                                               -- la aplicación
    passwd CHAR(32) NOT NULL, -- MD5 de la contraseña
    nombre TEXT DEFAULT '',   -- Nombre completo del usuario
    cuenta TEXT DEFAULT '',   -- Cuenta de correo de soporte
    cpass TEXT DEFAULT '',    -- Contraseña del correo de soporte. TEXTO PLANO.
    nivel INT DEFAULT 5,      -- 0 es el mayor. 5 es el menor.
        -- Además de los permisos sobre ventanas, para un par de casos
        -- especiales se mirará el nivel de privilegios para permitir volver a
        -- desbloquear partes, editar albaranes antiguos y cosas así...
    email TEXT DEFAULT '',          -- NEW! 25/10/2006. Dirección de correo
        -- electrónico del usuario (propia, no soporte).
    smtpserver TEXT DEFAULT '',     -- NEW! 25/10/2006. Servidor SMTP
        -- correspondiente a la dirección anterior por donde
        -- enviar, por ejemplo, albaranes.
    smtpuser TEXT DEFAULT '',       -- NEW! 25/10/2006. Usuario para
        -- autenticación en el servidor SMTP (si fuera necesario)
    smtppassword TEXT DEFAULT '',   -- NEW! 25/10/2006. Contraseña para
        -- autenticación en el servidor SMTP (si fuera necesario).
    firma_total BOOLEAN DEFAULT FALSE,      -- NEW! 26/02/2007. Puede firmar
        -- por cualquiera de los 4 roles en facturas de compra.
    firma_comercial BOOLEAN DEFAULT FALSE,  -- NEW! 26/02/2007. Puede firmar
        -- como director comercial.
    firma_director BOOLEAN DEFAULT FALSE,   -- NEW! 26/02/2007. Puede firmar
        -- como director general.
    firma_tecnico BOOLEAN DEFAULT FALSE,    -- NEW! 26/02/2007. Puede firmar
        -- como director técnico.
    firma_usuario BOOLEAN DEFAULT FALSE,    -- NEW! 26/02/2007. Puede firmar
        -- como usuario (confirmar total de factura).
    observaciones TEXT DEFAULT ''           -- NEW! 26/02/2007. Observaciones.
);

CREATE TABLE modulo(
    id SERIAL PRIMARY KEY,
    nombre TEXT,
    icono TEXT,
    descripcion TEXT
);

CREATE TABLE ventana(
    id SERIAL PRIMARY KEY,
    modulo_id INT REFERENCES modulo,
    descripcion TEXT,
    fichero TEXT,         -- Nombre del fichero .py
    clase TEXT,           -- Nombre de la clase principal de la ventana.
    icono TEXT DEFAULT '' -- Fichero del icono o '' para el icono por defecto
);

CREATE TABLE permiso(
    -- Relación muchos a muchos con atributo entre usuarios y ventanas.
    id SERIAL PRIMARY KEY,
    usuario_id INT REFERENCES usuario,
    ventana_id INT REFERENCES ventana,
    permiso BOOLEAN DEFAULT FALSE,   -- Indica si tiene permiso o no para
                                     -- abrir la ventana.
    --    PRIMARY KEY(usuario_id, ventana_id)   SQLObject requiere que cada
    -- tabla tenga un único ID.
    lectura BOOLEAN DEFAULT FALSE,
    escritura BOOLEAN DEFAULT FALSE,
    nuevo BOOLEAN DEFAULT FALSE     -- Nuevos permisos. Entrarán en la
                                    -- siguiente versión.
);

CREATE TABLE estadistica(
    id SERIAL PRIMARY KEY,
    usuario_id INT REFERENCES usuario,
    ventana_id INT REFERENCES ventana,
    veces INT DEFAULT 0,
    ultima_vez TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE datos_de_la_empresa(
    -- Datos de la empresa. Aparecen en los informes, facturas, albaranes,
    -- etc... Además, también sirven para determinar si un cliente es
    -- extranjero, generar albaranes internos...
    id SERIAL PRIMARY KEY,      -- Lo requiere SQLObject, pero no debería
                                -- haber más de un registro aquí.
    nombre TEXT DEFAULT 'Empresa',
    cif TEXT DEFAULT 'T-00.000.000',
    dirfacturacion TEXT DEFAULT 'C/ Dirección de facturación',
    cpfacturacion TEXT DEFAULT '00000',
    ciudadfacturacion TEXT DEFAULT 'Ciudad',
    provinciafacturacion TEXT DEFAULT 'Provincia',
    direccion TEXT DEFAULT 'C/ Dirección postal',
    cp TEXT DEFAULT '00000',
    ciudad TEXT DEFAULT 'Ciudad',
    provincia TEXT DEFAULT 'Provincia',
    telefono TEXT DEFAULT '034 000 00 00 00',
    fax TEXT DEFAULT '034 000 00 00 00',
    email TEXT DEFAULT 'correo@electronico.com',
    paisfacturacion TEXT DEFAULT 'España',
    pais TEXT DEFAULT 'España',
    telefonofacturacion TEXT DEFAULT '000 000 000 000',
    faxfacturacion TEXT DEFAULT '000 000 000 000',
    nombre_responsable_compras TEXT DEFAULT 'Responsable De Compras',
    telefono_responsable_compras TEXT DEFAULT '000 00 00 00',
    nombre_contacto TEXT DEFAULT 'Nombre Contacto',
    registro_mercantil TEXT DEFAULT 'Inscrita en el Registro Mercantil ...',
    email_responsable_compras TEXT DEFAULT 'resposable@compras.com',
    logo TEXT DEFAULT 'logo-inn.png',  -- Nombre de fichero (solo nombre,
        -- no ruta completa) de la imagen del logo de la empresa.
    logo2 TEXT DEFAULT '',  -- Nombre del logo alternativo
    bvqi BOOLEAN DEFAULT TRUE,          -- TRUE si hay que imprimir el logo
                                        -- de calidad certificada BVQI
    -- Dirección para albaran alternativo (albaran composan)
    nomalbaran2 TEXT DEFAULT 'NOMBRE ALTERNATIVO ALBARÁN',
    diralbaran2 TEXT DEFAULT 'Dirección albarán',
    cpalbaran2 TEXT DEFAULT '00000',
    ciualbaran2 TEXT DEFAULT 'Ciudad',
    proalbaran2 TEXT DEFAULT 'Provincia',
    telalbaran2 TEXT DEFAULT '00 000 00 00',
    faxalbaran2 TEXT DEFAULT '00 000 00 00',
    regalbaran2 TEXT DEFAULT 'CIF T-00000000 Reg.Mec. de ...',
    irpf FLOAT DEFAULT 0.0, -- NEW! 10/04/07. Si -0.15 aparecerá el campo
        -- IRPF en las facturas de venta para descontarse de la base imponible
    es_sociedad BOOLEAN DEFAULT TRUE,   -- NEW! 02/05/07. Si es TRUE la
        -- empresa es una sociedad. Si FALSE, la empresa es
        -- persona física o persona jurídica. En los impresos se usará
        -- "nombre" como nombre comercial y nombre_contacto como nombre
        -- fiscal de facturación.
        -- También servirá para discernir si mostrar servicios y transportes
        -- en albaranes y si valorar o no albaranes en el PDF generado al
        -- imprimir.
        -- OJO: También se usa para escribir "FÁBRICA" o "TIENDA" en los
        -- pedidos de compra, etc.
    logoiso1 TEXT DEFAULT 'bvqi.gif',  -- NEW! 27/06/07. Si bvqi es TRUE en
                                       -- algunos impresos aparecerá este logo.
    logoiso2 TEXT DEFAULT 'bvqi2.png', -- NEW! 27/06/07. Si bvqi es TRUE en
                                       -- algunos impresos aparecerá este logo.
    recargo_equivalencia BOOLEAN DEFAULT FALSE, -- 4% adicional de IVA y eso.
    iva FLOAT DEFAULT 0.18, -- IVA soportado por defecto, sin contar R.E.
    ped_compra_texto_fijo TEXT DEFAULT 'ROGAMOS NOS REMITAN COPIA DE ESTE PEDIDO SELLADO Y FIRMADO POR UDS.',   -- Sólo lo puede editar el usuario de nivel 0 (admin).
    ped_compra_texto_editable TEXT DEFAULT 'ESTA MERCANCIA SE DEBE ENTREGAR...', -- Se puede editar por cualquiera con permiso de escritura en pedidos de compra.
    ped_compra_texto_editable_con_nivel1 TEXT DEFAULT 'PAGO A 120 DÍAS F.F. PAGO LOS 25.', -- Solo lo puede editar en perdidos de compra los usuarios con nivel 0 ó 1.
    direccion_laboratorio TEXT DEFAULT 'Dirección de laboratorio', 
    cp_laboratorio TEXT DEFAULT '00000', 
    ciudad_laboratorio TEXT DEFAULT 'Ciudad laboratorio', 
    provincia_laboratorio TEXT DEFAULT 'Provincia laboratorio', 
    telefono_laboratorio TEXT DEFAULT '000000000'
);

CREATE TABLE alerta(
    id SERIAL PRIMARY KEY,
    usuario_id INT REFERENCES usuario,
    mensaje TEXT DEFAULT '',
    fechahora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    entregado BOOLEAN DEFAULT FALSE
);

CREATE TABLE foto(
    id SERIAL PRIMARY KEY, 
    empleado_id INT REFERENCES empleado DEFAULT NULL, 
    data TEXT DEFAULT '', 
    fechahora TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

------------------------------------------------
-- Muchos a muchos entre peticiones y ensayos --
------------------------------------------------
CREATE TABLE peticiones__ensayos(
    peticion_id INT REFERENCES peticion NOT NULL, 
    ensayo_id INT REFERENCES ensayo NOT NULL
);

-----------------------------------------------------------------
-- Muchos a muchos entre laborantes y ensayos que pueden hacer --
-----------------------------------------------------------------
CREATE TABLE empleados__ensayos(
    empleado_id INT REFERENCES empleado NOT NULL, 
    ensayo_id INT REFERENCES ensayo NOT NULL
);

CREATE TABLE vencimiento_cobro(
    id SERIAL PRIMARY KEY, 
    factura_venta_id INT REFERENCES factura_venta, 
    modo_pago_id INT REFERENCES modo_pago, 
    fecha DATE DEFAULT CURRENT_DATE, 
    importe FLOAT DEFAULT 0.0, 
    observaciones TEXT DEFAULT ''
);

CREATE TABLE documento_de_pago(
    id SERIAL PRIMARY KEY, 
    numero TEXT DEFAULT '', 
    fecha_recepcion DATE DEFAULT CURRENT_DATE, 
    fecha_vencimiento DATE DEFAULT CURRENT_DATE, 
    pendiente BOOLEAN DEFAULT TRUE, 
    observaciones TEXT DEFAULT ''
);

CREATE TABLE cobro(
    id SERIAL PRIMARY KEY, 
    factura_venta_id INT REFERENCES factura_venta, 
    modo_pago_id INT REFERENCES modo_pago DEFAULT NULL, 
    documento_de_pago_id INT REFERENCES documento_de_pago DEFAULT NULL, 
    fecha DATE DEFAULT CURRENT_DATE, 
    importe FLOAT DEFAULT 0.0
);

CREATE TABLE oferta(
    id SERIAL PRIMARY KEY, 
    obra_id INT REFERENCES obra DEFAULT NULL, 
    numoferta TEXT DEFAULT '', 
    fecha DATE DEFAULT CURRENT_DATE
);

CREATE TABLE linea_de_oferta(
    id SERIAL PRIMARY KEY, 
    oferta_id INT REFERENCES oferta DEFAULT NULL, 
    ensayo_id INT REFERENCES ensayo DEFAULT NULL, 
    precio FLOAT DEFAULT 0.0, 
    observaciones TEXT DEFAULT ''
);

CREATE TABLE informe(
    id SERIAL PRIMARY KEY, 
    oferta_id INT REFERENCES oferta DEFAULT NULL, 
    linea_de_venta_id INT REFERENCES linea_de_venta DEFAULT NULL, 
    numinforme TEXT DEFAULT '', 
    -- El código de muestra es campo calculado
    fecha DATE DEFAULT CURRENT_DATE, 
    observaciones TEXT DEFAULT ''
);

CREATE TABLE resultado(
    id SERIAL PRIMARY KEY, 
    muestra_id INT REFERENCES muestra DEFAULT NULL, 
    ensayo_id INT REFERENCES ensayo DEFAULT NULL, 
    informe_id INT REFERENCES informe DEFAULT NULL, 
    -- linea_de_venta_id INT REFERENCES linea_de_venta DEFAULT NULL, 
    valor FLOAT DEFAULT 0.0, 
    fecha DATE DEFAULT CURRENT_DATE
);

----------------
-- Adjuntos --
----------------
-- Documentos adjuntos a resultados.
CREATE TABLE adjunto(
    id SERIAL PRIMARY KEY, 
    resultado_id INT REFERENCES resultado DEFAULT NULL, 
    empleado_id INT REFERENCES empleado DEFAULT NULL, 
    informe_id INT REFERENCES informe DEFAULT NULL, 
    nombre TEXT DEFAULT '',     -- Nombre descriptivo
    nombre_fichero TEXT NOT NULL DEFAULT '', -- Nombre del fichero. SIN RUTAS.
    observaciones TEXT DEFAULT ''
);


-- XXX
--CREATE TABLE <++>(
--    id SERIAL PRIMARY KEY
--);



