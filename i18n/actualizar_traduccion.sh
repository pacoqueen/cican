#!/bin/sh
FUENTES=$(grep "from gettext import gettext as _" -R .. | cut -d ":" -f 1 | grep -v ".swp"  | grep -v ".pyw" | grep -v ".sh" | sort -u)
PRJNAME=cican
DOMAIN=$PRJNAME
POT=messages_$PRJNAME.pot
# 0.- Preparar plantilla:
xgettext --package-name $PRJNAME --default-domain=$DOMAIN --output=$POT \
         --from-code=utf-8 \
         --copyright-holder="Francisco José Rodríguez Bogado" \
         --msgid-bugs-address="frbogado@novaweb.es" -s $FUENTES
# 1.- Ficheros de traducción
IDIOMAS="en
es"
for IDIOMA in $IDIOMAS; do
    PO=$IDIOMA\_$PRJNAME.po
    ls $PO 2>/dev/null
    if [ $? -eq 0 ]; then    # Existe, actualizo solamente.
        msgmerge -s -U $PO $POT
    else                            # No existe, lo creo.
        msginit -l $IDIOMA -o $PO -i $POT
    fi 
    # 2.- Traducción
    gtranslator $PWD/$PO
    # 3.- Compilación
    MO=../l10n/$IDIOMA/LC_MESSAGES/$PRJNAME.mo
    msgfmt -c -v --output-file=$MO $PO
done 

