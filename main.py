import os
from disco import Disco
from lector2 import leer_estructura_sql, leer_csv, serializar, deserializar
from avl import IndiceAVL

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

print("\nConfiguracion del disco")
n_platos         = pedir_entero("  platos                : ", 1)
n_pistas         = pedir_entero("  pistas por superficie : ", 1)
n_sectores       = pedir_entero("  sectores por pista    : ", 1)
bytes_por_sector = pedir_entero("  bytes por sector      : ", 8)

disco = Disco(n_platos, n_pistas, n_sectores, bytes_por_sector)
print()
print(disco.info())
print(disco.info_por_plato())

#estructura_db = leer_estructura_sql("C:\\Users\\lolitascim\\bd\\disco\\estructura.txt")
estructura_db = leer_estructura_sql("D:\\CCOMP\\CCOMP - UCSP\\Quinto Semestre\\BD2\\proyecto\\code\\4ProyectoFinal\\struct_tableNew.txt")
tam_registro  = sum(c['tam'] for c in estructura_db)
print(f"tam_registro: {tam_registro} bytes")

#registros = leer_csv("C:\\Users\\lolitascim\\bd\\disco\\prueba.csv")
registros = leer_csv("D:\\CCOMP\\CCOMP - UCSP\\Quinto Semestre\\BD2\\proyecto\\code\\4ProyectoFinal\\Inventory_v4.csv")
print(f"registros leidos: {len(registros)}")

indice = IndiceAVL(estructura_db)

print("\n--- INSERTANDO REGISTROS ---")

tabla   = []
errores = []

for i, registro in enumerate(registros):
    try:
        datos_bytes = serializar(registro, estructura_db)
        inicio      = disco.escribir_registro(datos_bytes)

        tabla.append({
            'original': registro,
            'inicio'  : inicio
        })
        indice.insertar(registro, inicio, tam_registro)

        print(f"\nRegistro {i+1}: {registro}")
        print(f"  serializado : {len(datos_bytes)} bytes")
        print(f"  inicio      : plato={inicio[0]} sup={inicio[1]} pista={inicio[2]} sector={inicio[3]}")
        print(disco.direccion_legible(inicio, tam_registro))

    except Exception as e:
        errores.append(f"Registro {i+1}: {e}")
        print(f"\nerror registro {i+1}: {e}")
        break

print("\n--- VERIFICANDO LECTURA ---")

todos_ok = True

for i, entrada in enumerate(tabla):
    datos_leidos = disco.leer_registro(entrada['inicio'], tam_registro)
    recuperado   = deserializar(datos_leidos, estructura_db)
    original     = entrada['original']

    ok = True
    for orig, rec, campo in zip(original, recuperado, estructura_db):
        if rec is None:
            ok = False
            break
        if campo['tipo'] == 'char':
            orig_cortado = str(orig)[:campo['tam']]
            if orig_cortado != str(rec):
                ok = False
                break
        else:
            if str(orig) != str(rec):
                ok = False
                break

    if not ok:
        todos_ok = False

    print(f"\nRegistro {i+1}:")
    print(f"  original   : {original}")
    print(f"  desde disco: {recuperado}")
    print(f"  estado     : {'ok' if ok else 'error'}")

print()
print(disco.info())
print(disco.info_por_plato())

if errores:
    print("\nerrores:")
    for e in errores:
        print(f"  {e}")

print("\nresultado final:", "todo ok" if todos_ok else "hay errores")

#print()
#print(indice.info())

print("\n--- BUSQUEDA EN AVL ---")
print("  campos:", [c['nombre'] for c in estructura_db])

while True:
    campo = input("\n  campo (o 'salir'): ").strip()
    if campo == 'salir':
        break

    campo_info = next((c for c in estructura_db if c['nombre'] == campo), None)
    if campo_info is None:
        print("  campo no encontrado")
        continue

    valor = input("  valor: ").strip()

    if campo_info['tipo'] == 'int':
        try:
            valor_cast = int(valor)
        except ValueError:
            print("  valor invalido para int")
            continue
    elif campo_info['tipo'] == 'float':
        try:
            valor_cast = float(valor)
        except ValueError:
            print("  valor invalido para float")
            continue
    else:
        valor_cast = valor

    resultados = indice.buscar(campo, valor_cast)

    if not resultados:
        print("  no se encontro")
    else:
        print(f"  {len(resultados)} resultado(s):")
        for j, (inicio, tam) in enumerate(resultados):
            datos_leidos = disco.leer_registro(inicio, tam)
            recuperado   = deserializar(datos_leidos, estructura_db)
            print(f"    [{j+1}] {recuperado}")