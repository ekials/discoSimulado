import csv
import struct
import math
#valores null en caso se presenten
NULOS = ('', 'NULL', 'null', '\\N', None)


def leer_archivo(ruta):
    registros = []
    #['Ana','','1.60']
    #['Luis','25','1.80']
    if ruta.endswith('.csv'):
        with open(ruta, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            for fila in reader:
                if any(v.strip() for v in fila):#ignorar filas vacias
                    registros.append(fila)
    else:
        with open(ruta, encoding='utf-8') as f:
            for linea in f:
                linea = linea.strip()
                if linea:
                    registros.append(linea.split(' '))
    #$igualar cantidad de columnas en caso de vaciooo
    # ['Juan','20','1.75'],
    #['Ana',None,None],
    max_cols = max(len(fila) for fila in registros)
    for fila in registros:
        while len(fila) < max_cols:
            fila.append(None)

    return registros

def estructura(registros):
    estructura = []
#recorrer por columna como columnar???? by chance
    for col in zip(*registros):
        valores = [v for v in col if v not in NULOS]#no nulos discr

        if not valores:
            estructura.append({'tipo': 'char', 'tam': 1})
            #igual le pones 1 byte que indique que no hay nada
            continue

        try:
            [int(v) for v in valores]
            estructura.append({'tipo': 'int', 'tam': 4})
            continue
        except (ValueError, TypeError):
            pass

        try:
            [float(v) for v in valores]
            estructura.append({'tipo': 'float', 'tam': 4})
            continue
        except (ValueError, TypeError):
            pass
#buscar el mas grande
        max_tam = max(len(v.encode('utf-8')) for v in valores)
        estructura.append({'tipo': 'char', 'tam': max_tam})
    
    num_campos    = len(estructura)
    tam_bitmap    = math.ceil(num_campos / 8)   # bytes del bitmap
    tam_datos     = sum(c['tam'] for c in estructura)
    tam_registro  = tam_bitmap + tam_datos

    return estructura, tam_registro, tam_bitmap
# ['Juan', None, '1.75']
# campo 0 -> 1
# campo 1 -> 0
# campo 2 -> 1
# tonces el bitmap eso 101 wa

#para binario pues
def serializar(registro, estructura, tam_bitmap):
    # construir bitmap
    bitmap = 0
    for i, valor in enumerate(registro):
        if valor not in NULOS:
            bitmap |= (1 << i)      # bit i = 1 → tiene valor

    resultado = bitmap.to_bytes(tam_bitmap, 'big')

    # ahora peor campos
    for valor, campo in zip(registro, estructura):
        es_nulo = valor in NULOS

        if es_nulo:
            resultado += b'\x00' * campo['tam']   # rellenar de ceros

        else:
            if campo['tipo'] == 'int':
                resultado += int(valor).to_bytes(4, 'big')

            elif campo['tipo'] == 'float':
                resultado += struct.pack('>f', float(valor))

            else:  # char
                encoded = valor.encode('utf-8')
                resultado += encoded.ljust(campo['tam'], b'\x00')

    return resultado

def deserializar(datos_bytes, estructura, tam_bitmap):
    # bitmap
    bitmap = int.from_bytes(datos_bytes[:tam_bitmap], 'big')
    offset = tam_bitmap

    resultado = []

    for i, campo in enumerate(estructura):
        chunk    = datos_bytes[offset : offset + campo['tam']]
        offset  += campo['tam']

        tiene_valor = (bitmap >> i) & 1   # 1 = tiene valor, 0 = nulo

        if not tiene_valor:
            resultado.append(None)
            continue

        if campo['tipo'] == 'int':
            resultado.append(int.from_bytes(chunk, 'big'))

        elif campo['tipo'] == 'float':
            resultado.append(round(struct.unpack('>f', chunk)[0], 6))

        else:  # char
            resultado.append(chunk.rstrip(b'\x00').decode('utf-8'))

    return resultado

#eliminar porque solo es para probar que todo funciona
def probar(ruta):
    registros = leer_archivo(ruta)

    print("leido")
    for r in registros:
        print(r)

    estructura_db, tam_registro, tam_bitmap = estructura(registros)

    print("\nEstrcutura")
    for campo in estructura_db:
        print(campo)

    print("\nTam registr:", tam_registro)
    print("Tam bitmap:", tam_bitmap)


    for i, registro in enumerate(registros):
        binario = serializar(registro, estructura_db, tam_bitmap)

        recuperado = deserializar(
            binario,
            estructura_db,
            tam_bitmap
        )

        print(f"\nRegistro {i+1}")
        print("Original :", registro)
        print("Recuperado :", recuperado)

        if recuperado == [
            None if v in NULOS else
            int(v) if estructura_db[j]['tipo'] == 'int' else
            round(float(v), 6) if estructura_db[j]['tipo'] == 'float' else
            v
            for j, v in enumerate(registro)
        ]: 
            print("esta bien")




probar("C:/Users/lolitascim/disco/prueba.csv")
probar("C:/Users/lolitascim/disco/prueba2.txt")
