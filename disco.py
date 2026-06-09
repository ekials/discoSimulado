class Sector:
    def __init__(self, plato, superficie, pista, numero, tam_bytes):
        self.plato      = plato
        self.superficie = superficie
        self.pista      = pista
        self.numero     = numero
        self.datos      = bytearray(tam_bytes)
        self.ocupado    = False


class Disco:
    def __init__(self, n_platos, n_pistas, n_sectores, bytes_por_sector):
        self.n_platos         = n_platos
        self.n_pistas         = n_pistas
        self.n_sectores       = n_sectores
        self.bytes_por_sector = bytes_por_sector
        self.sectores         = {}
        self.libres           = {}
        self._construir()

    def _construir(self):
        for p in range(self.n_platos):
            self.libres[p] = []
            for s in range(2):
                for t in range(self.n_pistas):
                    for sec in range(self.n_sectores):
                        addr = (p, s, t, sec)
                        self.sectores[addr] = Sector(p, s, t, sec, self.bytes_por_sector)
                        self.libres[p].append(addr)

    def capacidad_total_bytes(self):
        return self.n_platos * 2 * self.n_pistas * self.n_sectores * self.bytes_por_sector

    def total_sectores(self):
        return self.n_platos * 2 * self.n_pistas * self.n_sectores

    def sectores_libres(self):
        return sum(len(v) for v in self.libres.values())

    def sectores_usados(self):
        return self.total_sectores() - self.sectores_libres()

    def esta_lleno(self):
        return self.sectores_libres() == 0

    def _plato_con_espacio(self):
        for p, lista in self.libres.items():
            if lista:
                return p
        return None

    def escribir_registro(self, datos: bytes) -> list:
        if len(datos) > self.sectores_libres() * self.bytes_por_sector:
            raise Exception(
                f"Disco lleno: se necesitan {len(datos)} bytes"
                f"pero solo hay {self.sectores_libres() * self.bytes_por_sector} disponibles"
            )

        fragmentos   = []
        offset       = 0
        plato_actual = self._plato_con_espacio()

        while offset < len(datos):
            if not self.libres[plato_actual]:
                plato_actual = self._plato_con_espacio()
                if plato_actual is None:
                    raise Exception("disco lleno (al fragmentar entre platos) aa")

            addr   = self.libres[plato_actual].pop(0)
            sector = self.sectores[addr]

            bytes_a_escribir = min(len(datos) - offset, self.bytes_por_sector)
            sector.datos[0:bytes_a_escribir] = datos[offset:offset + bytes_a_escribir]
            sector.ocupado = True

            fragmentos.append((sector.plato, sector.superficie, sector.pista, sector.numero, 0, bytes_a_escribir - 1))
            offset += bytes_a_escribir

        return fragmentos

    def leer_registro(self, fragmentos: list) -> bytes:
        datos = b""
        for (plato, sup, pista, sec, b_ini, b_fin) in fragmentos:
            sector = self.sectores[(plato, sup, pista, sec)]
            datos += bytes(sector.datos[b_ini:b_fin + 1])
        return datos

    def direccion_legible(self, fragmentos: list) -> str:
        lineas = []
        for i, (plato, sup, pista, sec, b_ini, b_fin) in enumerate(fragmentos):
            lineas.append(
                f"  Fragmento {i+1}: "
                f"Plato {plato} | Sup {sup} | "
                f"Pista {pista} | Sector {sec} | "
                f"Bytes {b_ini}-{b_fin}"
            )
        return "\n".join(lineas)

    def info(self) -> str:
        return (
            f"  DISCO SIMULADO\n"
            f"  Platos           : {self.n_platos}\n"
            f"  Superficies      : 2 por plato\n"
            f"  Pistas/superficie: {self.n_pistas}\n"
            f"  Sectores/pista   : {self.n_sectores}\n"
            f"  Bytes/sector     : {self.bytes_por_sector}\n"
            f"  Capacidad total  : {self.capacidad_total_bytes()} bytes\n"
            f"  Sectores totales : {self.total_sectores()}\n"
            f"  Sectores usados  : {self.sectores_usados()}\n"
            f"  Sectores libres  : {self.sectores_libres()}\n"
        )

    def info_por_plato(self) -> str:
        lineas = ["Uso por plato:"]
        for p in range(self.n_platos):
            total_plato  = 2 * self.n_pistas * self.n_sectores
            usados_plato = total_plato - len(self.libres[p])
            pct = usados_plato / total_plato * 100 if total_plato > 0 else 0
            lineas.append(f"  Plato {p}: {usados_plato}/{total_plato} sectores usados ({pct:.1f}%)")
        return "\n".join(lineas)