#!/bin/sh

DBNAME=cican

pg_dump -Fc -f ~/`date +%Y%m%d`_$DBNAME.Fc.pgdump $DBNAME
# Y ahora debería copiar los adjuntos. Mirar el script de FP.

