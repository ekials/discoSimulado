import csv
import struct
import math

NULOS = ('', 'NULL', 'null', '\\N', None)

def leer_archivo(ruta):
    registros = []
    cabecera  = None

    if ruta.endswith('.csv'):
        with open(ruta, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            for i, fila in enumerate(reader):
                if i == 0:
                    cabecera = [c.strip() for c in fila]
                else:
                    if any(v.strip() for v in fila):
                        registros.append([v.strip() for v in fila])
    else:
        with open(ruta, encoding='utf-8') as f:
            for i, linea in enumerate(f):
                linea = linea.strip()
                if not linea:
                    continue
                if i == 0:
                    cabecera = linea.split(' ')   # primera línea = cabecera
                else:
                    registros.append(linea.split(' '))

    max_cols = max(len(fila) for fila in registros)
    for fila in registros:
        while len(fila) < max_cols:
            fila.append(None)

    return cabecera, registros


def detectar_estructura(cabecera, registros):
    estructura = []

    for i, nombre_campo in enumerate(cabecera):
        col     = [fila[i] for fila in registros if i < len(fila)]
        valores = [v for v in col if v not in NULOS]

        if not valores:
            estructura.append({'nombre': nombre_campo, 'tipo': 'char', 'tam': 1})
            continue

        try:
            [int(v) for v in valores]
            estructura.append({'nombre': nombre_campo, 'tipo': 'int', 'tam': 4})
            continue
        except (ValueError, TypeError):
            pass

        try:
            [float(v) for v in valores]
            estructura.append({'nombre': nombre_campo, 'tipo': 'float', 'tam': 4})
            continue
        except (ValueError, TypeError):
            pass

        max_tam = max(len(v.encode('utf-8')) for v in valores)
        estructura.append({'nombre': nombre_campo, 'tipo': 'char', 'tam': max_tam})

    tam_bitmap   = math.ceil(len(estructura) / 8)
    tam_datos    = sum(c['tam'] for c in estructura)
    tam_registro = tam_bitmap + tam_datos

    print("\nEstructura detectada")
    for c in estructura:
        print(f"  {c['nombre']:<15} tipo: {c['tipo']:<6}  tam: {c['tam']} bytes")
    print(f"\n  bitmap      : {tam_bitmap} byte(s)")
    print(f"  tam_registro: {tam_registro} bytes")

    return estructura, tam_registro, tam_bitmap


def serializar(registro, estructura, tam_bitmap):
    bitmap = 0
    for i, valor in enumerate(registro):
        if valor not in NULOS:
            bitmap |= (1 << i)

    resultado = bitmap.to_bytes(tam_bitmap, 'big')

    for valor, campo in zip(registro, estructura):
        if valor in NULOS:
            resultado += b'\x00' * campo['tam']
        else:
            if campo['tipo'] == 'int':
                resultado += int(valor).to_bytes(4, 'big')
            elif campo['tipo'] == 'float':
                resultado += struct.pack('>f', float(valor))
            else:
                encoded    = valor.encode('utf-8')
                resultado += encoded.ljust(campo['tam'], b'\x00')

    return resultado


def deserializar(datos_bytes, estructura, tam_bitmap):
    bitmap  = int.from_bytes(datos_bytes[:tam_bitmap], 'big')
    offset  = tam_bitmap
    resultado = []

    for i, campo in enumerate(estructura):
        chunk   = datos_bytes[offset : offset + campo['tam']]
        offset += campo['tam']

        tiene_valor = (bitmap >> i) & 1

        if not tiene_valor:
            resultado.append(None)
            continue

        if campo['tipo'] == 'int':
            resultado.append(int.from_bytes(chunk, 'big'))
        elif campo['tipo'] == 'float':
            resultado.append(round(struct.unpack('>f', chunk)[0], 6))
        else:
            resultado.append(chunk.rstrip(b'\x00').decode('utf-8'))

    return resultado


#probar("C:\\Users\\lolitascim\\bd\\disco\\prueba.csv")