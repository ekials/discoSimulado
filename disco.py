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

    def _calcular_tam_con_padding(self, offset_inicial: int, estructura: list) -> int:
        offset = offset_inicial
        for campo in estructura:
            tam_campo      = campo['tam']
            byte_en_sector = offset % self.bytes_por_sector
            espacio        = self.bytes_por_sector - byte_en_sector
            if espacio < tam_campo and byte_en_sector != 0:
                offset += espacio          
            offset += tam_campo
        return offset - offset_inicial

    def escribir_registro(self, datos_bytes: bytes, estructura: list) -> int:
 
        tam_real = self._calcular_tam_con_padding(self.offset_actual, estructura)
        libres   = self.capacidad_total_bytes() - self.offset_actual

        if tam_real > libres:
            raise Exception(
                f"Disco lleno: el registro necesita {tam_real} bytes reales "
                f"(datos + padding) pero solo quedan {libres} bytes libres.\n"
                f"  Registros insertados hasta ahora: {self.n_registros}\n"
                f"  Capacidad total: {self.capacidad_total_bytes()} bytes"
            )

        offset_backup = self.offset_actual
        offset        = self.offset_actual
        offset_inicial = offset
        pos_bytes      = 0

        try:
            for campo in estructura:
                tam_campo      = campo['tam']
                byte_en_sector = offset % self.bytes_por_sector
                espacio        = self.bytes_por_sector - byte_en_sector

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

        except Exception as e:
            self.offset_actual = offset_backup
            raise Exception(f"Error durante escritura, cambios revertidos: {e}")


    def leer_registro(self, offset_inicial: int, estructura: list) -> bytes:
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
        offset = offset_inicial
        for i, campo in enumerate(estructura):
            tam_campo      = campo['tam']
            byte_en_sector = offset % self.bytes_por_sector
            espacio        = self.bytes_por_sector - byte_en_sector
            if espacio < tam_campo and byte_en_sector != 0:
                offset += espacio
            if i == idx_campo:
                return offset
            offset += tam_campo
        return offset

    def sectores_campo(self, offset_inicial: int, estructura: list, idx_campo: int) -> list:
        """
        Devuelve el (único) sector donde vive el campo. Como escribir_registro
        nunca parte un campo entre sectores (si no cabe, lo manda completo
        al siguiente sector con padding), el campo siempre vive en un solo
        sector — nunca en dos o más.
        """
        offset_campo = self.offset_campo(offset_inicial, estructura, idx_campo)
        plato, sup, pista, sec, _ = self._offset_a_dir(offset_campo)
        return [(plato, sup, pista, sec)]

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
        (offset, valores), devuelve (offset_registro, nombre_campo, valor)
        para cada campo que vive en ese sector exacto. Como un campo nunca
        se parte entre sectores, basta comparar el sector de inicio.
        """
        resultado = []

        for offset_reg, registro in tabla_offsets:
            offset = offset_reg
            for idx_campo, campo in enumerate(estructura):
                tam_campo      = campo['tam']
                byte_en_sector = offset % self.bytes_por_sector
                espacio        = self.bytes_por_sector - byte_en_sector

                if espacio < tam_campo and byte_en_sector != 0:
                    offset += espacio

                plato, sup, pista, sec, _ = self._offset_a_dir(offset)

                if (plato, sup, pista, sec) == direccion:
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