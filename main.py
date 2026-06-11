import os
from disco import Disco
from avl import construir_indice, buscar, buscar_rango, offset_desde_nreg, offset_campo
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

# estructura_db = leer_estructura_sql(os.path.join(CARPETA, "estructura.txt"))
estructura_db = leer_estructura_sql("C:\\Users\\lolitascim\\bd\\disco\\estructura.txt")
tam_registro  = sum(c['tam'] for c in estructura_db)

print(f"\ntam_registro : {tam_registro} bytes")

registros = leer_csv("C:\\Users\\lolitascim\\bd\\disco\\prueba.csv")
print(f"registros    : {len(registros)}")


print("\n")
print("INSERTANDO REGISTROS")
tabla         = []
tabla_offsets = []   # para avl
errores       = []

bytes_por_plato = 2 * n_pistas * n_sectores * bytes_por_sector

for i, registro in enumerate(registros):
    try:
        datos_bytes = serializar(registro, estructura_db)
        offset      = disco.escribir_registro(datos_bytes)

        n_registro  = offset // tam_registro
        plato       = offset // bytes_por_plato

        tabla.append({
            'original': registro,
            'offset':   offset
        })

        rec = deserializar(datos_bytes, estructura_db)
        tabla_offsets.append((offset, rec))

        print(f"\nRegistro {i+1}")
        print(f"  valores     : {registro}")
        print(f"  bytes       : {len(datos_bytes)}")
        print(f"  offset      : {offset}  |  n_reg: {n_registro}  |  plato: {plato}")
        print(disco.direccion_legible(offset, tam_registro))

    except Exception as e:
        errores.append(f"Registro {i+1}: {e}")
        print(f"\n  error: {e}")
        break

print("\n")
print("VERIFICANDO LECTURA")
print("")
todos_ok = True
"""
for i, entrada in enumerate(tabla):
    datos_leidos = disco.leer_registro(entrada['offset'], tam_registro)
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
"""
print("\n")
print("ESTADO DEL DISCO")
print(disco.info())
print(disco.info_por_plato())

if errores:
    print("\nerrores:")
    for e in errores:
        print(f"  {e}")


# avl
nombres_campos = [c['nombre'] for c in estructura_db]

while True:
    print("\n\nBUSQUEDA AVL")
    print("Campos disponibles:")
    for i, nombre in enumerate(nombres_campos):
        print(f"  {i:>2}. {nombre}")
    print("\n   q. salir")

    opcion = input("\nElige campo (numero o 'q'): ").strip()
    if opcion.lower() == 'q':
        break

    try:
        idx_campo = int(opcion)
        if idx_campo < 0 or idx_campo >= len(nombres_campos):
            print("  numero fuera de rango")
            continue
    except ValueError:
        print("  ingresa un numero valido")
        continue

    campo = nombres_campos[idx_campo]
    tipo  = estructura_db[idx_campo]['tipo']

    print(f"\nCampo: {campo}  (tipo: {tipo})")
    print("  1. busqueda exacta")
    print("  2. busqueda por rango")
    modo = input("Modo: ").strip()

    if modo not in ('1', '2'):
        print("  opcion invalida")
        continue

    print(f"\n  construyendo indice AVL para {campo}")
    raiz = construir_indice(tabla_offsets, estructura_db, campo, tam_registro)
    print("  listo\n")

    def convertir(val_str):
        if tipo == 'int':
            return int(val_str)
        if tipo == 'float':
            return float(val_str)
        return val_str

    if modo == '1':
        try:
            clave = convertir(input("  valor a buscar: ").strip())
        except ValueError:
            print("  valor invalido")
            raiz = None
            continue

        resultado = buscar(raiz, clave)

        if resultado is None:
            print(f"\n  no encontrado '{clave}' en '{campo}'")
        else:
            for idx, (n_reg, plato) in enumerate(resultado, 1):
                offset = offset_desde_nreg(n_reg, tam_registro)
                datos  = disco.leer_registro(offset, tam_registro)
                rec    = deserializar(datos, estructura_db)
                off_campo_en_registro = offset_campo(estructura_db, idx_campo)
                offset_dato           = offset + off_campo_en_registro
                p, sup, pi, sec, byte           = disco._offset_a_dir(offset)
                p_d, sup_d, pi_d, sec_d, byte_d = disco._offset_a_dir(offset_dato)
                print(f"  [{idx}] n_reg={n_reg} | offset={offset}")
                print(f"  registro → Plato:{p} | Sup:{sup} | Pista:{pi} | Sector:{sec} | Byte:{byte}")
                print(f"  dato '{campo}' → Plato:{p_d} | Sup:{sup_d} | Pista:{pi_d} | Sector:{sec_d} | Byte:{byte_d}")
                for c, v in zip(estructura_db, rec):
                    print(f"    {c['nombre']:<30}: {v}")
                print()

    else:
        try:
            clave_min = convertir(input("  valor minimo: ").strip())
            clave_max = convertir(input("  valor maximo: ").strip())
        except ValueError:
            print("  valor invalido")
            raiz = None
            continue

        resultados = buscar_rango(raiz, clave_min, clave_max)

        if not resultados:
            print(f"\n  no hay registros en [{clave_min}, {clave_max}]")
        else:
            print(f"\n  {len(resultados)} registro(s) en [{clave_min}, {clave_max}]:\n")
            for idx, (n_reg, plato) in enumerate(resultados, 1):
                offset = offset_desde_nreg(n_reg, tam_registro)
                datos  = disco.leer_registro(offset, tam_registro)
                rec    = deserializar(datos, estructura_db)

                off_campo_en_registro = offset_campo(estructura_db, idx_campo)
                offset_dato           = offset + off_campo_en_registro

                # dirección del REGISTRO
                p, sup, pi, sec, byte         = disco._offset_a_dir(offset)
                # dirección del DATO  ← línea que faltaba
                p_d, sup_d, pi_d, sec_d, byte_d = disco._offset_a_dir(offset_dato)

                print(f"  [{idx}] n_reg={n_reg} | offset={offset}")
                print(f"  registro → Plato:{p} | Sup:{sup} | Pista:{pi} | Sector:{sec} | Byte:{byte}")
                print(f"  dato '{campo}' → Plato:{p_d} | Sup:{sup_d} | Pista:{pi_d} | Sector:{sec_d} | Byte:{byte_d}")
                print(f"  debug: off_campo={off_campo_en_registro} offset_dato={offset_dato}")
                for c, v in zip(estructura_db, rec):
                    print(f"    {c['nombre']:<30}: {v}")
                print()
    # avl se elimina de RAM
    raiz = None
    print("  indice AVL liberado")