#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os
if os.path.realpath(os.path.curdir).split(os.path.sep)[-1] == "BD":
    sys.path.append("..")
from framework import pclases

def main():
    try:
        f = open("/home/bogado/CICAN/Pruebas/Códigos postales/cps.txt")
    except:
        f = open("cps.txt")
    for l in f.readlines():
        nombre_ciudad, cp = l.split(";")
        cp = cp.replace("\n", "")   # Viene con el retorno de carro.
        if not cp.startswith("41"):
            continue    # Ignoro los CP que no son de Sevilla para no saturar la tabla. Son demasiados registros.
        try:
            ciudad = pclases.Ciudad.selectBy(ciudad = nombre_ciudad)[0]
        except IndexError:
            print "Ciudad no encontrada:", nombre_ciudad
        except Exception:
            print "Error en codificación de caracteres casi seguro. Ignorando", nombre_ciudad
        else:
            pclases.CodigoPostal(ciudad = ciudad, cp = cp)
            print "Código postal", cp, "insertado."
    f.close()

if __name__ == "__main__":
    main()

