import struct

TAM_CABECERA = 7
SIN_SIGUIENTE = 0xFFFF
SIN_SIGUIENTE_1 = 0xFF  


class Sector:
    def __init__(self, plato, superficie, pista, numero, tam_bytes):
        self.plato      = plato
        self.superficie = superficie
        self.pista      = pista
        self.numero     = numero
        self.datos      = bytearray(tam_bytes)  # incluye cabecera + datos reales
        self.ocupado    = False                 # True = sector completo, no recibe mas datos

    def espacio_datos(self):
        # espacio real para datos (descontando cabecera)
        return len(self.datos) - TAM_CABECERA

    def escribir_cabecera(self, plato_sig, sup_sig, pista_sig, sector_sig):
        struct.pack_into('>H', self.datos, 0, plato_sig)   # 2 bytes
        self.datos[2] = sup_sig                             # 1 byte
        struct.pack_into('>H', self.datos, 3, pista_sig)   # 2 bytes
        struct.pack_into('>H', self.datos, 5, sector_sig)  # 2 bytes

    def leer_cabecera(self):
        plato_sig  = struct.unpack_from('>H', self.datos, 0)[0]
        sup_sig    = self.datos[2]
        pista_sig  = struct.unpack_from('>H', self.datos, 3)[0]
        sector_sig = struct.unpack_from('>H', self.datos, 5)[0]
        return plato_sig, sup_sig, pista_sig, sector_sig

    def escribir_datos(self, chunk: bytes):
        # escribe chunk despues de la cabecera
        self.datos[TAM_CABECERA: TAM_CABECERA + len(chunk)] = chunk
        self.ocupado = True

    def leer_datos(self, n_bytes: int) -> bytes:
        return bytes(self.datos[TAM_CABECERA: TAM_CABECERA + n_bytes])


class Disco:
    def __init__(self, n_platos, n_pistas, n_sectores, bytes_por_sector):
        self.n_platos         = n_platos
        self.n_pistas         = n_pistas
        self.n_sectores       = n_sectores
        self.bytes_por_sector = bytes_por_sector
        self.sectores         = {}
        self._construir()

    def _construir(self):
        for p in range(self.n_platos):
            for s in range(2):
                for t in range(self.n_pistas):
                    for sec in range(self.n_sectores):
                        addr = (p, s, t, sec)
                        self.sectores[addr] = Sector(
                            p, s, t, sec,
                            self.bytes_por_sector
                        )

    def _siguiente_libre(self):
        for addr, sector in self.sectores.items():
            if not sector.ocupado:
                return addr
        return None

    def escribir_registro(self, datos: bytes) -> tuple:
        espacio_por_sector = self.bytes_por_sector - TAM_CABECERA

        n_sectores_necesarios = math.ceil(len(datos) / espacio_por_sector)

        libres = [addr for addr, s in self.sectores.items() if not s.ocupado]
        if len(libres) < n_sectores_necesarios:
            raise Exception(
                f"Disco lleno: se necesitan {n_sectores_necesarios} sectores "
                f"pero solo hay {len(libres)} libres"
            )

        sectores_usados = libres[:n_sectores_necesarios]

        offset = 0
        for i, addr in enumerate(sectores_usados):
            sector = self.sectores[addr]

            chunk = datos[offset: offset + espacio_por_sector]
            offset += len(chunk)

            if i < len(sectores_usados) - 1:
                sig = sectores_usados[i + 1]
                sector.escribir_cabecera(sig[0], sig[1], sig[2], sig[3])
            else:
                sector.escribir_cabecera(
                    SIN_SIGUIENTE,  
                    SIN_SIGUIENTE_1, 
                    SIN_SIGUIENTE,   
                    SIN_SIGUIENTE 
                )

            sector.escribir_datos(chunk)

        inicio = sectores_usados[0]
        return inicio  

    def leer_registro(self, inicio: tuple, tam_registro: int) -> bytes:
        datos        = b''
        bytes_leidos = 0
        addr         = inicio

        while True:
            sector = self.sectores[addr]
            espacio = self.bytes_por_sector - TAM_CABECERA

            por_leer = min(espacio, tam_registro - bytes_leidos)
            datos   += sector.leer_datos(por_leer)
            bytes_leidos += por_leer

            if bytes_leidos >= tam_registro:
                break

            p_sig, s_sig, t_sig, sec_sig = sector.leer_cabecera()

            if p_sig == SIN_SIGUIENTE:
                break 

            addr = (p_sig, s_sig, t_sig, sec_sig)

        return datos

    def capacidad_total_bytes(self):
        return (
            self.n_platos * 2 *
            self.n_pistas *
            self.n_sectores *
            self.bytes_por_sector
        )

    def total_sectores(self):
        return self.n_platos * 2 * self.n_pistas * self.n_sectores

    def sectores_libres(self):
        return sum(1 for s in self.sectores.values() if not s.ocupado)

    def sectores_usados(self):
        return sum(1 for s in self.sectores.values() if s.ocupado)

    def esta_lleno(self):
        return self.sectores_libres() == 0

    def info(self):
        return (
            f"DISCO SIMULADO\n"
            f"Platos            : {self.n_platos}\n"
            f"Superficies       : 2 por plato\n"
            f"Pistas/superficie : {self.n_pistas}\n"
            f"Sectores/pista    : {self.n_sectores}\n"
            f"Bytes/sector      : {self.bytes_por_sector}\n"
            f"Cabecera/sector   : {TAM_CABECERA} bytes\n"
            f"Datos/sector      : {self.bytes_por_sector - TAM_CABECERA} bytes\n"
            f"Capacidad total   : {self.capacidad_total_bytes()} bytes\n"
            f"Sectores totales  : {self.total_sectores()}\n"
            f"Sectores usados   : {self.sectores_usados()}\n"
            f"Sectores libres   : {self.sectores_libres()}\n"
        )

    def info_por_plato(self):
        lineas = ["Uso por plato:"]
        cap_plato = (
            2 * self.n_pistas *
            self.n_sectores
        )
        for p in range(self.n_platos):
            usados = sum(
                1 for s in self.sectores.values()
                if s.plato == p and s.ocupado
            )
            lineas.append(
                f"  Plato {p}: "
                f"{usados}/{cap_plato} sectores usados "
                f"({usados/cap_plato*100:.1f}%)"
            )
        return "\n".join(lineas)

    def direccion_legible(self, inicio: tuple, tam_registro: int) -> str:
        lineas = []
        addr   = inicio
        i      = 0
        bytes_leidos = 0
        espacio = self.bytes_por_sector - TAM_CABECERA

        while True:
            sector = self.sectores[addr]
            por_leer = min(espacio, tam_registro - bytes_leidos)
            bytes_leidos += por_leer

            lineas.append(
                f"  Fragmento {i+1}: "
                f"Plato {addr[0]} | Sup {addr[1]} | "
                f"Pista {addr[2]} | Sector {addr[3]} | "
                f"Bytes {TAM_CABECERA}-{TAM_CABECERA + por_leer - 1}"
            )
            i += 1

            if bytes_leidos >= tam_registro:
                break

            p_sig, s_sig, t_sig, sec_sig = sector.leer_cabecera()
            if p_sig == SIN_SIGUIENTE:
                break

            addr = (p_sig, s_sig, t_sig, sec_sig)

        return "\n".join(lineas)


import math