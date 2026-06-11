class NodoAVL:
    def __init__(self, clave, n_registro, plato):
        self.clave     = clave
        self.registros = [(n_registro, plato)]
        self.izq       = None
        self.der       = None
        self.altura    = 1


def _altura(nodo):
    return nodo.altura if nodo else 0

def _actualizar_altura(nodo):
    nodo.altura = 1 + max(_altura(nodo.izq), _altura(nodo.der))

def _balance(nodo):
    return _altura(nodo.izq) - _altura(nodo.der) if nodo else 0

def _rotar_der(y):
    x     = y.izq
    T     = x.der
    x.der = y
    y.izq = T
    _actualizar_altura(y)
    _actualizar_altura(x)
    return x

def _rotar_izq(x):
    y     = x.der
    T     = y.izq
    y.izq = x
    x.der = T
    _actualizar_altura(x)
    _actualizar_altura(y)
    return y

def insertar(nodo, clave, n_registro, plato):
    if nodo is None:
        return NodoAVL(clave, n_registro, plato)

    if clave < nodo.clave:
        nodo.izq = insertar(nodo.izq, clave, n_registro, plato)
    elif clave > nodo.clave:
        nodo.der = insertar(nodo.der, clave, n_registro, plato)
    else:
        nodo.registros.append((n_registro, plato))
        return nodo

    _actualizar_altura(nodo)
    b = _balance(nodo)

    if b > 1 and clave < nodo.izq.clave:
        return _rotar_der(nodo)
    if b < -1 and clave > nodo.der.clave:
        return _rotar_izq(nodo)
    if b > 1 and clave > nodo.izq.clave:
        nodo.izq = _rotar_izq(nodo.izq)
        return _rotar_der(nodo)
    if b < -1 and clave < nodo.der.clave:
        nodo.der = _rotar_der(nodo.der)
        return _rotar_izq(nodo)

    return nodo


def buscar(nodo, clave):
    if nodo is None:
        return None
    if clave == nodo.clave:
        return nodo.registros
    if clave < nodo.clave:
        return buscar(nodo.izq, clave)
    return buscar(nodo.der, clave)


def buscar_rango(nodo, clave_min, clave_max, resultados=None):
    if resultados is None:
        resultados = []
    if nodo is None:
        return resultados

    if clave_min < nodo.clave:
        buscar_rango(nodo.izq, clave_min, clave_max, resultados)

    if clave_min <= nodo.clave <= clave_max:
        resultados.extend(nodo.registros)

    if clave_max > nodo.clave:
        buscar_rango(nodo.der, clave_min, clave_max, resultados)

    return resultados


def offset_desde_nreg(n_registro, tam_registro):
    return n_registro * tam_registro


def construir_indice(registros_raw, estructura, campo, tam_registro):
    idx_campo = next(
        (i for i, c in enumerate(estructura) if c['nombre'] == campo),
        None
    )
    if idx_campo is None:
        raise ValueError(f"campo '{campo}' no existe en la estructura")

    tipo = estructura[idx_campo]['tipo']
    raiz = None

    for offset, registro in registros_raw:
        valor_raw = registro[idx_campo]
        if tipo == 'int':
            clave = int(valor_raw)
        elif tipo == 'float':
            clave = float(valor_raw)
        else:
            clave = str(valor_raw)

        n_registro = offset // tam_registro
        raiz = insertar(raiz, clave, n_registro, 0)

    return raiz