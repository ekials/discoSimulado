import os
import struct
import math
import csv

from disco import Disco
from lector import leer_archivo, detectar_estructura, serializar, deserializar

#confi disco

print("\n Configuracion del disco")

def pedir_entero(mensaje, minimo=1):
    while True:
        try:
            valor = int(input(mensaje))
            if valor < minimo:
                print(f"  debe ser al menos {minimo}")
            else:
                return valor
        except ValueError:
            print("  Ingresa un nro valido.")

n_platos         = pedir_entero("  nro de platos         : ", 1)
n_pistas         = pedir_entero("  Pistas por superficie    : ", 1)
n_sectores       = pedir_entero("  Sectores por pista       : ", 1)
bytes_por_sector = pedir_entero("  Bytes por sector         : ", 8)


disco = Disco(n_platos, n_pistas, n_sectores, bytes_por_sector)

print()
print(disco.info())
print(disco.info_por_plato())

print("\nArchivos de pruebita:")
print("  1 prueba.csv ")
print("  2 prueba2.txt ")
opcion = input("\n  opc ").strip()

CARPETA = os.path.dirname(os.path.abspath(__file__))

if opcion == "1":
    ruta = "C:\\Users\\lolitascim\\bd\\disco\\prueba.csv"
elif opcion == "2":
    ruta = "C:\\Users\\lolitascim\\bd\\disco\\prueba2.txt"

cabecera, registros = leer_archivo("C:\\Users\\lolitascim\\bd\\disco\\prueba.csv")
print(f"  registros leidos: {len(registros)}")

estructura_db, tam_registro, tam_bitmap = detectar_estructura(cabecera, registros)

print(f"\n  Estructura detectada ({tam_registro} bytes por registro):")
for i, campo in enumerate(estructura_db):
    print(f"    Campo {i}: tipo={campo['tipo']}, tam={campo['tam']} bytes")

tabla  = []
errores = []

for i, registro in enumerate(registros):
    try:
        datos_bytes = serializar(registro, estructura_db, tam_bitmap)
        fragmentos  = disco.escribir_registro(datos_bytes)
        tabla.append({
            'original'  : registro,
            'fragmentos': fragmentos
        })
        n_frag = len(fragmentos)
        print(f"\n  Registro {i+1}: {registro}")
        print(f" Serializado: {len(datos_bytes)} bytes - Fragmentos: {n_frag}")
        print(disco.direccion_legible(fragmentos))

    except Exception as e:
        errores.append(f"Registro {i+1}: {e}")
        print(f"\n  error Registro {i+1}: {e}")
        break

print()
todos_ok = True
for i, entrada in enumerate(tabla):
    datos_leidos = disco.leer_registro(entrada['fragmentos'])
    recuperado   = deserializar(datos_leidos, estructura_db, tam_bitmap)
    original     = entrada['original']
    print(f"  Registro {i+1}:")
    print(f"    Original  : {original}")
    print(f"    Desde disco: {recuperado}")

    #verificar valores
    NULOS_CHECK = ('', 'NULL', 'null', '\\N', None)
    ok = True
    for j, (orig, rec) in enumerate(zip(original, recuperado)):
        es_nulo = orig in NULOS_CHECK
        if es_nulo and rec is not None:
            ok = False
        elif not es_nulo and rec is None:
            ok = False
    estado = "estabien" if ok else "error"
    if not ok:
        todos_ok = False
    print(f"    Estado    : {estado}")



print()
print(disco.info())
print()
print(disco.info_por_plato())

if errores:
    for e in errores:
        print(f"  {e}")

if todos_ok:
    print("esta bien")
else:
    print("esta mal")

