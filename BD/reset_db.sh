#!/bin/sh

# Reinicia la base de datos creando una copia de seguridad, reordenándola y 
# recreando la BD de nuevo en base a la copia.
# Útil para los cambios en tablas.sql

DB=cican
USER=cican
PASS=cican
BAK=/tmp/reset.sql

pg_dump $DB -a -f $BAK && \
dropdb $DB && \
createdb $DB -O $USER -E utf8 && psql $DB -U $USER < tablas.sql 2>&1 | grep -v NOTICE && \
pg_restore -d $DB -a $BAK

