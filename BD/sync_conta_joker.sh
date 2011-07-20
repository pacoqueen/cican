#!/bin/sh

HOST=joker  
SSH=`which ssh`

echo "Copiando base de datos"
$SSH cican@$HOST "./backup_full.sh"
FBAK=$($SSH cican@$HOST "ls *.pgdump -tr | tail -n 1")
scp cican@$HOST:$FBAK /tmp
echo "Restaurando base de datos en local"
pg_restore -c -d cican /tmp/$FBAK
echo "Copiando log"
scp cican@$HOST:/home/compartido/src/ginn.log .
# TODO: Y faltan los adjuntos

