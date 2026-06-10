import csv
import struct
import math
import re

def tipo_sql_a_interno(tipo_sql):
    tipo_sql = tipo_sql.strip().upper()

    if tipo_sql == 'INTEGER' or tipo_sql == 'INT':
        return 'int', 4

    if tipo_sql == 'FLOAT' or tipo_sql == 'REAL' or tipo_sql == 'DOUBLE':
        return 'float', 4

    match = re.match(r'VARCHAR\s*\((\d+)\)', tipo_sql)
    if match:
        return 'char', int(match.group(1))

    match = re.match(r'CHAR\s*\((\d+)\)', tipo_sql)
    if match:
        return 'char', int(match.group(1))

    raise ValueError(f"tipo SQL no reconocido: {tipo_sql}")

def serializar(registro, estructura):
    resultado = b''
    for valor, campo in zip(registro, estructura):
        if campo['tipo'] == 'int':
            resultado += int(valor).to_bytes(4, 'big')
        elif campo['tipo'] == 'float':
            resultado += struct.pack('>f', float(valor))
        else:
            encoded    = valor.encode('utf-8')
            if len(encoded) > campo['tam']: #si el tam de varchar es mas grande
                raise ValueError(
                    f"ERROR DBMS: El valor '{valor}' es demasiado largo "
                    f"para el tipo VARCHAR({campo['tam']}) en el campo '{campo['nombre']}'"
                )
            resultado += encoded[:campo['tam']].ljust(campo['tam'], b'\x00')
    return resultado


def deserializar(datos_bytes, estructura):
    offset    = 0
    resultado = []
    for campo in estructura:
        chunk   = datos_bytes[offset : offset + campo['tam']]
        offset += campo['tam']
        if campo['tipo'] == 'int':
            resultado.append(int.from_bytes(chunk, 'big'))
        elif campo['tipo'] == 'float':
            resultado.append(round(struct.unpack('>f', chunk)[0], 6))
        else:
            resultado.append(chunk.rstrip(b'\x00').decode('utf-8'))
    return resultado


def leer_estructura_sql(ruta_sql):
    estructura = []
    with open(ruta_sql, encoding='utf-8') as f:
        contenido = f.read()
    match = re.search(r'CREATE\s+TABLE\s+\w+\s*\((.+)\)', contenido, re.DOTALL | re.IGNORECASE)
    if not match:
        raise ValueError("no se encontró CREATE TABLE en el archivo")
    cuerpo = match.group(1)
    for linea in cuerpo.splitlines():
        linea = linea.strip().rstrip(',').strip()
        if not linea:
            continue
        if linea.upper().startswith(('PRIMARY', 'FOREIGN', 'UNIQUE', 'CHECK', 'INDEX', 'KEY', 'CONSTRAINT')):
            continue
        partes = linea.split()
        if len(partes) < 2:
            continue
        nombre   = partes[0]
        tipo_raw = partes[1]
        try:
            tipo, tam = tipo_sql_a_interno(tipo_raw)
        except ValueError:
            continue
        estructura.append({'nombre': nombre, 'tipo': tipo, 'tam': tam})

    tam_registro = sum(c['tam'] for c in estructura)

    print("\nEstructura desde SQL")
    for c in estructura:
        print(f"  {c['nombre']:<35} tipo: {c['tipo']:<6}  tam: {c['tam']} bytes")
    print(f"  tam_registro: {tam_registro} bytes")

    return estructura


def leer_csv(ruta_csv):
    registros = []
    with open(ruta_csv, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        for fila in reader:
            if any(v.strip() for v in fila):
                registros.append([v.strip() for v in fila])
    return registros


def probar(ruta_sql, ruta_csv):
    print("\nLEYENDO ESTRUCTURA SQL")
    estructura_db = leer_estructura_sql(ruta_sql)
    tam_registro  = sum(c['tam'] for c in estructura_db)

    print("\nLEYENDO CSV")
    registros = leer_csv(ruta_csv)
    print(f"registros leidos: {len(registros)}")

    print("\nPRUEBA SERIALIZACION")
    for i, registro in enumerate(registros):
        binario    = serializar(registro, estructura_db)
        recuperado = deserializar(binario, estructura_db)

        print(f"\nRegistro {i+1}")
        print("Original:  ", registro)
        print("Bytes:     ", binario.hex(' '))
        print("Recuperado:", recuperado)


#probar("C:\\Users\\lolitascim\\bd\\disco\\estructura.txt", "C:\\Users\\lolitascim\\bd\\disco\\prueba.csv")