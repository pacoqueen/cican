#!/bin/bash

# Elimina y vuelve a crear la base de datos de CICAN con algunos ejemplos.

function usage(){
    echo Uso: $0 [-h] [-d]
    echo "    -h = Esta ayuda."
    echo "    -d = Modo depuración."
    exit 1
}

DEBUG=0
while getopts 'hd' OPTION; do
    case $OPTION in 
        h)  usage
                    ;;
        d)  DEBUG=1
                    ;;
        ?)  printf "Usage: %s: [-h] [-d]\n" $(basename $0) >&2
            exit 2
                    ;;
    esac
done
shift $(($OPTIND - 1))

if [ $DEBUG -eq 1 ]; then
    echo Eliminando base de datos...
fi 
dropdb cican -h joker -U cican
if [ $DEBUG -eq 1 ]; then
    echo Creando nueva base de datos...
fi 
createdb cican -O cican -E utf8 -h joker -U cican && psql cican -U cican -h joker < tablas.sql 2>&1 | grep -v NOTICE
if [ $DEBUG -eq 1 ]; then
    echo Creando usuarios... 
fi 
psql cican -h joker -U cican < usuarios.sql
if [ $DEBUG -eq 1 ]; then
    echo Insertando datos de ejemplo...
fi 
./inserta_ejemplos.py
if [ $DEBUG -eq 1 ]; then
    echo Creando estructura de ventanas...
fi 
./inserta_ventanas.py
if [ $DEBUG -eq 1 ]; then
    echo Insertando países... 
fi 
psql cican -h joker -U cican < paises.sql
if [ $DEBUG -eq 1 ]; then
    echo Insertando provincias...
fi 
psql cican -h joker -U cican < provincias.sql
if [ $DEBUG -eq 1 ]; then
    echo Insertando municipios...
fi 
psql cican -h joker -U cican < municipios.sql
if [ $DEBUG -eq 1 ]; then
    echo Insertando tipos de vía...
fi 
psql cican -h joker -U cican < tipos_de_via.sql
if [ $DEBUG -eq 1 ]; then
    echo Insertando categorías laborales...
fi 
psql cican -h joker -U cican < categorias_laborales.sql
if [ $DEBUG -eq 1 ]; then
    echo Insertando formas de pago...
fi 
psql cican -h joker -U cican < formas_de_pago.sql
if [ $DEBUG -eq 1 ]; then
    echo Insertando tabla de medidas...
fi 
psql cican -h joker -U cican < unidades.sql
if [ $DEBUG -eq 1 ]; then
    echo Insertando códigos postales...
fi 
./codigos_postales.py

