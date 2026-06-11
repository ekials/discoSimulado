import math


class Sector:
    def __init__(self, plato, superficie, pista, numero, tam_bytes):
        self.plato      = plato
        self.superficie = superficie
        self.pista      = pista
        self.numero     = numero
        self.datos      = bytearray(tam_bytes)


class Disco:
    # cada entrada del directorio ocupa 4 bytes (int offset en bytes)
    TAM_ENTRADA_DIR = 4

    def __init__(self, n_platos, n_pistas, n_sectores, bytes_por_sector):
        self.n_platos         = n_platos
        self.n_pistas         = n_pistas
        self.n_sectores       = n_sectores
        self.bytes_por_sector = bytes_por_sector
        self.offset_actual = 0
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


    def escribir_registro(self, datos: bytes):
        tam = len(datos)

        offset_inicial = self.offset_actual

        if offset_inicial + tam > self.capacidad_total_bytes():
            raise Exception("Disco lleno")

        self._escribir_bytes(offset_inicial, datos)

        self.offset_actual += tam

        return offset_inicial

    def leer_registro(self, offset_inicial, tam_registro):
        return self._leer_bytes(offset_inicial, tam_registro)

    def direccion_legible(self, offset_inicial, tam_registro):
        offset_byte = offset_inicial
        leidos       = 0
        lineas       = []
        i            = 0

        while leidos < tam_registro:
            plato, sup, pista, sec, byte_en_sector = self._offset_a_dir(
                offset_byte + leidos
            )
            espacio  = self.bytes_por_sector - byte_en_sector
            por_leer = min(espacio, tam_registro - leidos)

            lineas.append(
                f"  Fragmento {i+1}: "
                f"Plato {plato} | Sup {sup} | "
                f"Pista {pista} | Sector {sec} | "
                f"Bytes {byte_en_sector}-{byte_en_sector + por_leer - 1}"
            )
            leidos += por_leer
            i      += 1

        return "\n".join(lineas)

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

        bytes_usados_total = self.offset_actual

        for p in range(self.n_platos):

            bytes_por_plato = (
                2 * self.n_pistas *
                self.n_sectores *
                self.bytes_por_sector
            )

            offset_inicio = p * bytes_por_plato
            offset_fin    = offset_inicio + bytes_por_plato

            bytes_usados_plato = max(
                0,
                min(bytes_usados_total, offset_fin) - offset_inicio
            )

            sectores_usados = math.ceil(
                bytes_usados_plato / self.bytes_por_sector
            )

            porcentaje = sectores_usados / cap_plato * 100

            lineas.append(
                f"  Plato {p}: "
                f"{sectores_usados}/{cap_plato} sectores usados "
                f"({porcentaje:.1f}%)"
            )

        return "\n".join(lineas)