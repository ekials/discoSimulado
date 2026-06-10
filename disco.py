class Sector:
    def __init__(self, plato, superficie, pista, numero, tam_bytes):
        self.plato = plato
        self.superficie = superficie
        self.pista = pista
        self.numero = numero

        self.datos = bytearray(tam_bytes)
        self.bytes_usados = 0


class Disco:
    def __init__(self, n_platos, n_pistas, n_sectores, bytes_por_sector):
        self.n_platos = n_platos
        self.n_pistas = n_pistas
        self.n_sectores = n_sectores
        self.bytes_por_sector = bytes_por_sector

        self.sectores = {}

        self._construir()

    def _construir(self):
        for p in range(self.n_platos):
            for s in range(2):
                for t in range(self.n_pistas):
                    for sec in range(self.n_sectores):

                        addr = (p, s, t, sec)

                        self.sectores[addr] = Sector(
                            p,
                            s,
                            t,
                            sec,
                            self.bytes_por_sector
                        )

    def capacidad_total_bytes(self):
        return (
            self.n_platos *
            2 *
            self.n_pistas *
            self.n_sectores *
            self.bytes_por_sector
        )

    def bytes_usados(self):
        return sum(
            sector.bytes_usados
            for sector in self.sectores.values()
        )

    def bytes_libres(self):
        return self.capacidad_total_bytes() - self.bytes_usados()

    def total_sectores(self):
        return (
            self.n_platos *
            2 *
            self.n_pistas *
            self.n_sectores
        )

    def sectores_usados(self):
        return sum(
            1
            for sector in self.sectores.values()
            if sector.bytes_usados > 0
        )

    def sectores_libres(self):
        return sum(
            1
            for sector in self.sectores.values()
            if sector.bytes_usados == 0
        )

    def esta_lleno(self):
        return self.bytes_libres() == 0

    def _sector_con_espacio(self):

        for addr, sector in self.sectores.items():

            if sector.bytes_usados < self.bytes_por_sector:
                return addr

        return None

    def escribir_registro(self, datos: bytes) -> list:

        if len(datos) > self.bytes_libres():
            raise Exception(
                f"Disco lleno: se necesitan {len(datos)} bytes "
                f"pero solo hay {self.bytes_libres()} disponibles"
            )

        fragmentos = []

        offset = 0

        while offset < len(datos):

            addr = self._sector_con_espacio()

            if addr is None:
                raise Exception("Disco lleno")

            sector = self.sectores[addr]

            byte_inicio = sector.bytes_usados

            espacio_libre = (
                self.bytes_por_sector -
                sector.bytes_usados
            )

            bytes_a_escribir = min(
                len(datos) - offset,
                espacio_libre
            )

            byte_fin = byte_inicio + bytes_a_escribir

            sector.datos[
                byte_inicio:byte_fin
            ] = datos[
                offset:offset + bytes_a_escribir
            ]

            sector.bytes_usados += bytes_a_escribir

            fragmentos.append(
                (
                    sector.plato,
                    sector.superficie,
                    sector.pista,
                    sector.numero,
                    byte_inicio,
                    byte_fin - 1
                )
            )

            offset += bytes_a_escribir

        return fragmentos

    def leer_registro(self, fragmentos: list) -> bytes:

        datos = b""

        for (
            plato,
            sup,
            pista,
            sec,
            b_ini,
            b_fin
        ) in fragmentos:

            sector = self.sectores[
                (plato, sup, pista, sec)
            ]

            datos += bytes(
                sector.datos[b_ini:b_fin + 1]
            )

        return datos

    def direccion_legible(self, fragmentos: list) -> str:

        lineas = []

        for i, (
            plato,
            sup,
            pista,
            sec,
            b_ini,
            b_fin
        ) in enumerate(fragmentos):

            lineas.append(
                f"Fragmento {i+1}: "
                f"Plato {plato} | "
                f"Sup {sup} | "
                f"Pista {pista} | "
                f"Sector {sec} | "
                f"Bytes {b_ini}-{b_fin}"
            )

        return "\n".join(lineas)

    def info(self):

        return (
            f"DISCO SIMULADO\n"
            f"Platos            : {self.n_platos}\n"
            f"Superficies       : 2 por plato\n"
            f"Pistas/superficie : {self.n_pistas}\n"
            f"Sectores/pista    : {self.n_sectores}\n"
            f"Bytes/sector      : {self.bytes_por_sector}\n"
            f"Capacidad total   : {self.capacidad_total_bytes()} bytes\n"
            f"Bytes usados      : {self.bytes_usados()}\n"
            f"Bytes libres      : {self.bytes_libres()}\n"
            f"Sectores usados   : {self.sectores_usados()}\n"
            f"Sectores libres   : {self.sectores_libres()}\n"
        )

    def info_por_plato(self):

        lineas = ["Uso por plato:"]

        for p in range(self.n_platos):

            bytes_plato = 0

            for sector in self.sectores.values():

                if sector.plato == p:
                    bytes_plato += sector.bytes_usados

            capacidad_plato = (
                2 *
                self.n_pistas *
                self.n_sectores *
                self.bytes_por_sector
            )

            porcentaje = (
                bytes_plato /
                capacidad_plato *
                100
            )

            lineas.append(
                f"Plato {p}: "
                f"{bytes_plato}/{capacidad_plato} bytes "
                f"({porcentaje:.2f}%)"
            )

        return "\n".join(lineas)