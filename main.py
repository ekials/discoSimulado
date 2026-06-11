import os
from disco import Disco
from avl import buscar
from lector2 import leer_estructura_sql, leer_csv, serializar, deserializar

def pedir_entero(mensaje, minimo=1):
    while True:
        try:
            valor = int(input(mensaje))
            if valor < minimo:
                print(f"  debe ser al menos {minimo}")
            else:
                return valor
        except ValueError:
            print("  ingresa un numero valido")


print("\n=")
print("SIMULADOR DE DISCO")

print("\nConfiguracion del disco")
n_platos         = pedir_entero("  platos                : ", 1)
n_pistas         = pedir_entero("  pistas por superficie : ", 1)
n_sectores       = pedir_entero("  sectores por pista    : ", 1)
bytes_por_sector = pedir_entero("  bytes por sector      : ", 8)

disco = Disco(n_platos, n_pistas, n_sectores, bytes_por_sector)

print()
print(disco.info())
print(disco.info_por_plato())

CARPETA = os.path.dirname(os.path.abspath(__file__))

estructura_db = leer_estructura_sql(os.path.join(CARPETA, "estructura.txt"))
tam_registro  = sum(c['tam'] for c in estructura_db)

print(f"\ntam_registro : {tam_registro} bytes")

registros = leer_csv(os.path.join(CARPETA, "prueba.csv"))
print(f"registros    : {len(registros)}")


print("\n")
print("INSERTANDO REGISTROS")
tabla   = []
errores = []

for i, registro in enumerate(registros):
    try:
        datos_bytes     = serializar(registro, estructura_db)
        offset = disco.escribir_registro(datos_bytes)

        tabla.append({
            'original': registro,
            'offset': offset
        })

        print(f"\nRegistro {i+1}")
        print(f"  valores     : {registro}")
        print(f"  bytes       : {len(datos_bytes)}")
        print(f"  offset      : {offset}")
        print(disco.direccion_legible(offset, tam_registro))

    except Exception as e:
        errores.append(f"Registro {i+1}: {e}")
        print(f"\n  error: {e}")
        break

print("\n")
print("VERIFICANDO LECTURA")
print("")
todos_ok = True

for i, entrada in enumerate(tabla):
    datos_leidos = disco.leer_registro(entrada['offset'],tam_registro)
    recuperado   = deserializar(datos_leidos, estructura_db)
    original     = entrada['original']

    ok = True
    for orig, rec, campo in zip(original, recuperado, estructura_db):
        if rec is None:
            ok = False
            break
        if campo['tipo'] == 'char':
            if str(orig)[:campo['tam']] != str(rec):
                ok = False
                break
        else:
            if str(orig) != str(rec):
                ok = False
                break

    if not ok:
        todos_ok = False

    print(f"\nRegistro {i+1}:  {'ok' if ok else 'ERROR'}")
    print(f"  original    : {original}")
    print(f"  desde disco : {recuperado}")


print("\n")
print("ESTADO DEL DISCO")
print(disco.info())
print(disco.info_por_plato())

if errores:
    print("\nerrores:")
    for e in errores:
        print(f"  {e}")
