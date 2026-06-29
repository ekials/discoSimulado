import math

class Sector:
    def __init__(self, plato, superficie, pista, numero, tam_bytes):
        self.plato      = plato
        self.superficie = superficie
        self.pista      = pista
        self.numero     = numero
        self.datos      = bytearray(tam_bytes)

class Disco:
    def __init__(self, n_platos, n_pistas, n_sectores, bytes_por_sector, max_registros=1024):
        self.n_platos         = n_platos
        self.n_pistas         = n_pistas
        self.n_sectores       = n_sectores
        self.bytes_por_sector = bytes_por_sector
        self.offset_actual    = 0
        self.n_registros      = 0
        self.sectores         = {}
        self._construir()

    def _construir(self):
        for p in range(self.n_platos):
            for s in range(2):
                for t in range(self.n_pistas):
                    for sec in range(self.n_sectores):
                        self.sectores[(p, s, t, sec)] = Sector(
                            p, s, t, sec,
                            self.bytes_por_sector
                        )

    def _offset_a_dir(self, offset_byte: int) -> tuple:
        sectores_por_plato = 2 * self.n_pistas * self.n_sectores
        bytes_por_plato    = sectores_por_plato * self.bytes_por_sector

        plato           = offset_byte // bytes_por_plato
        resto           = offset_byte  % bytes_por_plato
        sector_en_plato = resto // self.bytes_por_sector
        byte_en_sector  = resto  % self.bytes_por_sector

        sup    = sector_en_plato // (self.n_pistas * self.n_sectores)
        resto2 = sector_en_plato  % (self.n_pistas * self.n_sectores)
        pista  = resto2 // self.n_sectores
        sec    = resto2  % self.n_sectores

        return plato, sup, pista, sec, byte_en_sector

    def _escribir_bytes(self, offset_byte: int, datos: bytes):
        escritos = 0
        while escritos < len(datos):
            plato, sup, pista, sec, byte_en_sector = self._offset_a_dir(
                offset_byte + escritos
            )
            sector  = self.sectores[(plato, sup, pista, sec)]
            espacio = self.bytes_por_sector - byte_en_sector
            chunk   = datos[escritos : escritos + espacio]
            sector.datos[byte_en_sector : byte_en_sector + len(chunk)] = chunk
            escritos += len(chunk)

    def _leer_bytes(self, offset_byte: int, n_bytes: int) -> bytes:
        datos  = b''
        leidos = 0
        while leidos < n_bytes:
            plato, sup, pista, sec, byte_en_sector = self._offset_a_dir(
                offset_byte + leidos
            )
            sector   = self.sectores[(plato, sup, pista, sec)]
            espacio  = self.bytes_por_sector - byte_en_sector
            por_leer = min(espacio, n_bytes - leidos)
            datos   += bytes(sector.datos[byte_en_sector : byte_en_sector + por_leer])
            leidos  += por_leer
        return datos

    def escribir_registro(self, datos_bytes: bytes, estructura: list) -> int:
        """
        Recibe el registro YA serializado (bytes crudos, sin padding) y la
        estructura (para saber dónde corta cada campo). Escribe campo por
        campo metiendo padding de ceros cuando un campo no cabe entero en
        el sector actual. Retorna el offset_inicial del registro.
        """
        offset         = self.offset_actual
        offset_inicial = offset
        pos_bytes      = 0   # posición dentro de datos_bytes (sin padding)

        for campo in estructura:
            tam_campo      = campo['tam']
            byte_en_sector = offset % self.bytes_por_sector
            espacio        = self.bytes_por_sector - byte_en_sector

            # no cabe → padding
            if espacio < tam_campo and byte_en_sector != 0:
                self._escribir_bytes(offset, b'\x00' * espacio)
                offset += espacio

            chunk = datos_bytes[pos_bytes : pos_bytes + tam_campo]
            self._escribir_bytes(offset, chunk)
            offset    += tam_campo
            pos_bytes += tam_campo

        self.offset_actual = offset
        self.n_registros  += 1
        return offset_inicial

    def leer_registro(self, offset_inicial: int, estructura: list) -> bytes:
        """
        Hace el mismo cálculo geométrico que escribir_registro — por cada
        campo verifica si hubo padding y lo salta. Retorna bytes limpios
        (sin padding), listos para pasar a deserializar().
        """
        offset    = offset_inicial
        resultado = b''

        for campo in estructura:
            tam_campo = campo['tam']

            byte_en_sector = offset % self.bytes_por_sector
            espacio        = self.bytes_por_sector - byte_en_sector

            if espacio < tam_campo and byte_en_sector != 0:
                offset += espacio

            chunk      = self._leer_bytes(offset, tam_campo)
            resultado += chunk
            offset    += tam_campo

        return resultado

    def offset_campo(self, offset_inicial: int, estructura: list, idx_campo: int) -> int:
        """
        Calcula el offset real (con padding incluido) donde empieza el
        campo idx_campo dentro del registro que arranca en offset_inicial.
        """
        offset = offset_inicial
        for i, campo in enumerate(estructura):
            if i == idx_campo:
                return offset
            tam_campo      = campo['tam']
            byte_en_sector = offset % self.bytes_por_sector
            espacio        = self.bytes_por_sector - byte_en_sector
            if espacio < tam_campo and byte_en_sector != 0:
                offset += espacio
            offset += tam_campo
        return offset

    def sectores_campo(self, offset_inicial: int, estructura: list, idx_campo: int) -> list:
        """
        Calcula todos los sectores (plato, sup, pista, sec) que ocupa
        un campo específico dentro del registro, incluyendo el caso en
        que el campo cruce el límite de un sector y siga en el siguiente.
        """
        offset_campo = self.offset_campo(offset_inicial, estructura, idx_campo)
        tam_campo    = estructura[idx_campo]['tam']

        sectores  = []
        recorrido = 0
        while recorrido < tam_campo:
            plato, sup, pista, sec, byte_en_sector = self._offset_a_dir(
                offset_campo + recorrido
            )
            sectores.append((plato, sup, pista, sec))
            espacio    = self.bytes_por_sector - byte_en_sector
            recorrido += espacio

        return list(dict.fromkeys(sectores))

    def direccion_legible(self, offset_inicial: int, estructura: list) -> str:
        offset = offset_inicial
        lineas = []

        for i, campo in enumerate(estructura):
            tam_campo = campo['tam']

            byte_en_sector = offset % self.bytes_por_sector
            espacio        = self.bytes_por_sector - byte_en_sector

            if espacio < tam_campo and byte_en_sector != 0:
                offset += espacio

            plato, sup, pista, sec, byte = self._offset_a_dir(offset)
            lineas.append(
                f"  Campo {i+1} ({campo['nombre']}): "
                f"Plato {plato} | Sup {sup} | "
                f"Pista {pista} | Sector {sec} | "
                f"Byte {byte}-{byte + tam_campo - 1}"
            )
            offset += tam_campo

        return "\n".join(lineas)

    def sectores_ocupados(self, offset_inicial, estructura):
        offset   = offset_inicial
        sectores = []

        for campo in estructura:
            tam_campo      = campo['tam']
            byte_en_sector = offset % self.bytes_por_sector
            espacio        = self.bytes_por_sector - byte_en_sector

            if espacio < tam_campo and byte_en_sector != 0:
                offset += espacio

            plato, sup, pista, sec, _ = self._offset_a_dir(offset)
            sectores.append((plato, sup, pista, sec))
            offset += tam_campo

        return list(dict.fromkeys(sectores))

    def campos_en_sector(self, direccion: tuple, tabla_offsets: list, estructura: list) -> list:
        """
        Dado un sector (plato, sup, pista, sec) y la tabla de registros
        (offset, valores), devuelve una lista de tuplas
        (offset_registro, nombre_campo, valor) para cada campo cuyo dato
        tiene al menos un byte dentro de ese sector exacto. No incluye
        padding porque solo se reportan campos reales con datos.
        """
        p_obj, s_obj, t_obj, sec_obj = direccion
        resultado = []

        for offset_reg, registro in tabla_offsets:
            offset = offset_reg
            for idx_campo, campo in enumerate(estructura):
                tam_campo      = campo['tam']
                byte_en_sector = offset % self.bytes_por_sector
                espacio        = self.bytes_por_sector - byte_en_sector

                if espacio < tam_campo and byte_en_sector != 0:
                    offset += espacio

                # sectores que toca este campo en particular
                inicio_campo = offset
                fin_campo    = offset + tam_campo - 1  # último byte (inclusive)

                p1, s1, t1, sec1, _ = self._offset_a_dir(inicio_campo)
                p2, s2, t2, sec2, _ = self._offset_a_dir(fin_campo)

                toca_sector = (p1, s1, t1, sec1) == direccion or (p2, s2, t2, sec2) == direccion

                if not toca_sector and inicio_campo != fin_campo:
                    # el campo puede cruzar varios sectores intermedios;
                    # solo revisamos si el sector buscado cae en ese rango
                    recorrido = inicio_campo
                    while recorrido <= fin_campo:
                        pp, ss, tt, secsec, ben = self._offset_a_dir(recorrido)
                        if (pp, ss, tt, secsec) == direccion:
                            toca_sector = True
                            break
                        recorrido += self.bytes_por_sector - ben

                if toca_sector:
                    resultado.append((offset_reg, campo['nombre'], registro[idx_campo]))

                offset += tam_campo

        return resultado

    def capacidad_total_bytes(self):
        return (
            self.n_platos * 2 *
            self.n_pistas *
            self.n_sectores *
            self.bytes_por_sector
        )

    def total_sectores(self):
        return self.n_platos * 2 * self.n_pistas * self.n_sectores

    def info(self):
        return (
            f"DISCO SIMULADO\n"
            f"Platos            : {self.n_platos}\n"
            f"Superficies       : 2 por plato\n"
            f"Pistas/superficie : {self.n_pistas}\n"
            f"Sectores/pista    : {self.n_sectores}\n"
            f"Bytes/sector      : {self.bytes_por_sector}\n"
            f"Capacidad total   : {self.capacidad_total_bytes()} bytes\n"
            f"Bytes usados      : {self.offset_actual}\n"
        )

    def info_por_plato(self):
        lineas    = ["Uso por plato:"]
        cap_plato = 2 * self.n_pistas * self.n_sectores

        for p in range(self.n_platos):
            bytes_por_plato    = 2 * self.n_pistas * self.n_sectores * self.bytes_por_sector
            offset_inicio      = p * bytes_por_plato
            offset_fin         = offset_inicio + bytes_por_plato
            bytes_usados_plato = max(0, min(self.offset_actual, offset_fin) - offset_inicio)
            sectores_usados    = math.ceil(bytes_usados_plato / self.bytes_por_sector)
            porcentaje         = sectores_usados / cap_plato * 100

            lineas.append(
                f"  Plato {p}: "
                f"{sectores_usados}/{cap_plato} sectores usados "
                f"({porcentaje:.1f}%)"
            )

        return "\n".join(lineas)