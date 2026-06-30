import csv
import struct
import math
import re

def tipo_sql_a_interno(tipo_sql):
    tipo_sql = tipo_sql.strip().upper()

    if tipo_sql in ('INTEGER', 'INT'):
        return 'int', 4

    if tipo_sql in ('FLOAT', 'REAL'):
        return 'float', 4

    if tipo_sql == 'DOUBLE':
        return 'double', 8

    if tipo_sql in ('BOOLEAN', 'BOOL'):
        return 'bool', 1

    match = re.match(r'VARCHAR\s*\((\d+)\)', tipo_sql)
    if match:
        return 'char', int(match.group(1))

    match = re.match(r'CHAR\s*\((\d+)\)', tipo_sql)
    if match:
        return 'char', int(match.group(1))

    match = re.match(r'DECIMAL\s*\(\d+\s*,\s*\d+\)', tipo_sql)
    if match:
        return 'double', 8
    
    raise ValueError(f"tipo SQL no reconocido: {tipo_sql}")


def serializar(registro, estructura):
    resultado = b''

    for valor, campo in zip(registro, estructura):
        if campo['tipo'] == 'int':
            resultado += int(valor).to_bytes(4, 'big')

        elif campo['tipo'] == 'float':
            resultado += struct.pack('>f', float(valor))

        elif campo['tipo'] == 'double':
            resultado += struct.pack('>d', float(valor))

        elif campo['tipo'] == 'bool':
            resultado += bytes([
                1 if str(valor).upper() in ('TRUE', '1', 'T') else 0
            ])

        else:  # char
            encoded = valor.encode('utf-8')
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

        elif campo['tipo'] == 'double':
            resultado.append(round(struct.unpack('>d', chunk)[0], 12))

        elif campo['tipo'] == 'bool':
            resultado.append(bool(chunk[0]))

        else:  # char
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
        #tipo_raw = partes[1]
        tipo_raw = partes[1]
        if '(' in tipo_raw and ')' not in tipo_raw:
            for extra in partes[2:]:
                tipo_raw += extra
                if ')' in extra:
                    break

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