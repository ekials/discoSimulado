class NodoAVL:
    def __init__(self, clave, inicio, tam_registro):
        self.clave        = clave
        self.registros    = [(inicio, tam_registro)]
        self.izq          = None
        self.der          = None
        self.altura       = 1


class AVL:
    def __init__(self, nombre_campo):
        self.nombre_campo = nombre_campo
        self.raiz         = None

    def _altura(self, nodo):
        if nodo is None:
            return 0
        return nodo.altura

    def _balance(self, nodo):
        if nodo is None:
            return 0
        return self._altura(nodo.izq) - self._altura(nodo.der)

    def _actualizar_altura(self, nodo):
        nodo.altura = 1 + max(
            self._altura(nodo.izq),
            self._altura(nodo.der)
        )

    def _rotar_der(self, y):
        x     = y.izq
        T2    = x.der
        x.der = y
        y.izq = T2
        self._actualizar_altura(y)
        self._actualizar_altura(x)
        return x

    def _rotar_izq(self, x):
        y     = x.der
        T2    = y.izq
        y.izq = x
        x.der = T2
        self._actualizar_altura(x)
        self._actualizar_altura(y)
        return y

    def _insertar(self, nodo, clave, inicio, tam_registro):
        if nodo is None:
            return NodoAVL(clave, inicio, tam_registro)

        if clave < nodo.clave:
            nodo.izq = self._insertar(nodo.izq, clave, inicio, tam_registro)
        elif clave > nodo.clave:
            nodo.der = self._insertar(nodo.der, clave, inicio, tam_registro)
        else:
            nodo.registros.append((inicio, tam_registro))
            return nodo

        self._actualizar_altura(nodo)
        bal = self._balance(nodo)

        if bal > 1 and clave < nodo.izq.clave:
            return self._rotar_der(nodo)
        if bal < -1 and clave > nodo.der.clave:
            return self._rotar_izq(nodo)
        if bal > 1 and clave > nodo.izq.clave:
            nodo.izq = self._rotar_izq(nodo.izq)
            return self._rotar_der(nodo)
        if bal < -1 and clave < nodo.der.clave:
            nodo.der = self._rotar_der(nodo.der)
            return self._rotar_izq(nodo)

        return nodo

    def insertar(self, clave, inicio, tam_registro):
        self.raiz = self._insertar(self.raiz, clave, inicio, tam_registro)

    def _buscar(self, nodo, clave):
        if nodo is None:
            return None
        if clave == nodo.clave:
            return nodo.registros
        elif clave < nodo.clave:
            return self._buscar(nodo.izq, clave)
        else:
            return self._buscar(nodo.der, clave)

    def buscar(self, clave):
        resultado = self._buscar(self.raiz, clave)
        return resultado if resultado is not None else []

    def _buscar_rango(self, nodo, clave_ini, clave_fin, resultado):
        if nodo is None:
            return
        if clave_ini < nodo.clave:
            self._buscar_rango(nodo.izq, clave_ini, clave_fin, resultado)
        if clave_ini <= nodo.clave <= clave_fin:
            for r in nodo.registros:
                resultado.append((nodo.clave, r))
        if clave_fin > nodo.clave:
            self._buscar_rango(nodo.der, clave_ini, clave_fin, resultado)

    def buscar_rango(self, clave_ini, clave_fin):
        resultado = []
        self._buscar_rango(self.raiz, clave_ini, clave_fin, resultado)
        return resultado

    def _inorden(self, nodo, resultado):
        if nodo is None:
            return
        self._inorden(nodo.izq, resultado)
        resultado.append((nodo.clave, nodo.registros))
        self._inorden(nodo.der, resultado)

    def inorden(self):
        resultado = []
        self._inorden(self.raiz, resultado)
        return resultado

    def info(self):
        nodos  = self.inorden()
        lineas = [f"AVL [{self.nombre_campo}] - {len(nodos)} claves:"]
        for clave, registros in nodos:
            lineas.append(f"  {clave} -> {len(registros)} registro")
        return "\n".join(lineas)


class IndiceAVL:
    def __init__(self, estructura):
        self.estructura = estructura
        self.arboles    = {}
        for campo in estructura:
            self.arboles[campo['nombre']] = AVL(campo['nombre'])

    def insertar(self, registro, inicio, tam_registro):
        NULOS = ('', 'NULL', 'null', '\\N', None)
        for i, campo in enumerate(self.estructura):
            valor = registro[i]
            if valor in NULOS:
                continue
            if campo['tipo'] == 'int':
                clave = int(valor)
            elif campo['tipo'] == 'float':
                clave = float(valor)
            else:
                clave = str(valor)
            self.arboles[campo['nombre']].insertar(clave, inicio, tam_registro)

    def buscar(self, nombre_campo, valor):
        if nombre_campo not in self.arboles:
            print(f"  campo '{nombre_campo}' no existe")
            return []
        return self.arboles[nombre_campo].buscar(valor)

    def buscar_rango(self, nombre_campo, valor_ini, valor_fin):
        if nombre_campo not in self.arboles:
            print(f"  campo '{nombre_campo}' no existe")
            return []
        return self.arboles[nombre_campo].buscar_rango(valor_ini, valor_fin)

    def info(self):
        lineas = ["INDICES AVL:"]
        for arbol in self.arboles.values():
            lineas.append(arbol.info())
        return "\n".join(lineas)
