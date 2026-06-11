import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os

RUTA_SQL = "C:\\Users\\lolitascim\\bd\\disco\\estructura.txt"
RUTA_CSV = "C:\\Users\\lolitascim\\bd\\disco\\prueba.csv"

BG          = "#0f0f1a"
BG2         = "#1a1a2e"
BG3         = "#16213e"
ACCENT      = "#00d4ff"
ACCENT2     = "#7b2ff7"
TEXT        = "#e0e0e0"
TEXT_DIM    = "#888888"
VERDE       = "#00ff88"
AMARILLO    = "#ffd700"
ROJO        = "#ff4444"
SECTOR_LIBRE   = "#1e3a5f"
SECTOR_OCUPADO = "#00d4ff"
SECTOR_REGISTRO = "#ffd700"
SECTOR_DATO     = "#ff4444"

FONT_TITLE  = ("Consolas", 18, "bold")
FONT_LABEL  = ("Consolas", 11)
FONT_SMALL  = ("Consolas", 9)
FONT_MONO   = ("Consolas", 10)

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Simulador de Disco")
        self.configure(bg=BG)
        self.geometry("1100x750")
        self.resizable(True, True)

        # estado compartido entre pantallas
        self.disco         = None
        self.estructura_db = None
        self.tam_registro  = 0
        self.registros     = None
        self.tabla_offsets = []

        # contenedor principal
        self.container = tk.Frame(self, bg=BG)
        self.container.pack(fill="both", expand=True)

        self.frames = {}
        for F in (PantallaConfig, PantallaDiscoVacio, PantallaCarga, PantallaBusqueda):
            frame = F(self.container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.mostrar(PantallaConfig)

    def mostrar(self, pantalla):
        frame = self.frames[pantalla]
        frame.tkraise()
        if hasattr(frame, 'al_mostrar'):
            frame.al_mostrar()

class DiscoVisual(tk.Canvas):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=BG, highlightthickness=0, **kwargs)
        self.disco            = None
        self.tam_registro     = 0
        self.sector_registro  = None   # (p, s, pi, sec) resaltado amarillo
        self.sector_dato      = None   # (p, s, pi, sec) resaltado rojo

    def actualizar(self, disco, tam_registro, n_registros=0, sector_registro=None, sector_dato=None):
        self.disco           = disco
        self.tam_registro    = tam_registro
        self.n_registros     = n_registros
        self.sector_registro = sector_registro
        self.sector_dato     = sector_dato
        self.dibujar()

    def dibujar(self):
        self.delete("all")
        if self.disco is None:
            return

        disco = self.disco
        ancho = self.winfo_width()
        if ancho < 10:
            ancho = 900

        bytes_usados   = self.n_registros * self.tam_registro if self.tam_registro else 0
        bytes_por_plato = 2 * disco.n_pistas * disco.n_sectores * disco.bytes_por_sector

        PAD     = 20
        GAP_P   = 18   # gap entre platos
        GAP_S   = 2    # gap entre superficies
        H_LABEL = 20

        # calcular tamaño de sector
        total_secs  = disco.n_pistas * disco.n_sectores
        ancho_disp  = ancho - 2 * PAD - 60   # 60 para labels izquierda
        sec_w       = max(6, (ancho_disp // total_secs) - 1)
        sec_h       = 18

        y = PAD

        for p in range(disco.n_platos):
            # título plato
            self.create_text(
                PAD, y + H_LABEL // 2,
                text=f"Plato {p}",
                fill=ACCENT, font=FONT_SMALL,
                anchor="w"
            )
            y += H_LABEL

            for s in range(2):
                # label superficie
                self.create_text(
                    PAD + 4, y + sec_h // 2,
                    text=f"S{s}",
                    fill=TEXT_DIM, font=FONT_SMALL,
                    anchor="w"
                )

                x = PAD + 52

                for t in range(disco.n_pistas):
                    for sec in range(disco.n_sectores):
                        addr        = (p, s, t, sec)
                        offset_byte = (
                            p * bytes_por_plato +
                            s * disco.n_pistas * disco.n_sectores * disco.bytes_por_sector +
                            t * disco.n_sectores * disco.bytes_por_sector +
                            sec * disco.bytes_por_sector
                        )

                        # color según estado
                        if addr == self.sector_dato:
                            color = SECTOR_DATO
                        elif addr == self.sector_registro:
                            color = SECTOR_REGISTRO
                        elif offset_byte < bytes_usados:
                            color = SECTOR_OCUPADO
                        else:
                            color = SECTOR_LIBRE

                        self.create_rectangle(
                            x, y,
                            x + sec_w, y + sec_h,
                            fill=color,
                            outline=BG,
                            width=1
                        )
                        x += sec_w + 1

                y += sec_h + GAP_S

            y += GAP_P

        # leyenda
        items = [
            (SECTOR_LIBRE,    "libre"),
            (SECTOR_OCUPADO,  "ocupado"),
            (SECTOR_REGISTRO, "registro encontrado"),
            (SECTOR_DATO,     "dato buscado"),
        ]
        lx = PAD
        ly = y + 8
        for color, label in items:
            self.create_rectangle(lx, ly, lx+12, ly+12, fill=color, outline="")
            self.create_text(lx+16, ly+6, text=label, fill=TEXT_DIM, font=FONT_SMALL, anchor="w")
            lx += 130

class PantallaConfig(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app

        tk.Label(self, text="SIMULADOR DE DISCO", font=FONT_TITLE,
                 bg=BG, fg=ACCENT).pack(pady=(60, 4))
        tk.Label(self, text="configuración del disco físico",
                 font=FONT_LABEL, bg=BG, fg=TEXT_DIM).pack(pady=(0, 40))

        form = tk.Frame(self, bg=BG)
        form.pack()

        campos = [
            ("Platos",                "n_platos",         "2"),
            ("Pistas por superficie", "n_pistas",         "4"),
            ("Sectores por pista",    "n_sectores",       "8"),
            ("Bytes por sector",      "bytes_por_sector", "64"),
            ("Máx. registros (dir.)", "max_registros",    "1024"),
        ]

        self.vars = {}
        for i, (label, key, default) in enumerate(campos):
            tk.Label(form, text=label, font=FONT_LABEL,
                     bg=BG, fg=TEXT, anchor="e", width=26).grid(
                row=i, column=0, padx=(0, 12), pady=6, sticky="e")

            var = tk.StringVar(value=default)
            self.vars[key] = var

            e = tk.Entry(form, textvariable=var, font=FONT_MONO,
                         bg=BG2, fg=ACCENT, insertbackground=ACCENT,
                         relief="flat", width=10,
                         highlightthickness=1, highlightbackground=ACCENT2,
                         highlightcolor=ACCENT)
            e.grid(row=i, column=1, pady=6, sticky="w")

        btn = tk.Button(self, text="crear disco →",
                        font=FONT_LABEL, bg=ACCENT2, fg="white",
                        relief="flat", padx=24, pady=10,
                        cursor="hand2", command=self.crear)
        btn.pack(pady=40)

        self.error_lbl = tk.Label(self, text="", font=FONT_SMALL,
                                  bg=BG, fg=ROJO)
        self.error_lbl.pack()

    def crear(self):
        from disco import Disco
        try:
            n_platos         = int(self.vars["n_platos"].get())
            n_pistas         = int(self.vars["n_pistas"].get())
            n_sectores       = int(self.vars["n_sectores"].get())
            bytes_por_sector = int(self.vars["bytes_por_sector"].get())
            max_registros    = int(self.vars["max_registros"].get())

            assert n_platos >= 1
            assert n_pistas >= 1
            assert n_sectores >= 1
            assert bytes_por_sector >= 8
            assert max_registros >= 1

        except:
            self.error_lbl.config(text="valores inválidos — todos deben ser enteros positivos")
            return

        self.app.disco = Disco(n_platos, n_pistas, n_sectores,
                               bytes_por_sector, max_registros)
        self.error_lbl.config(text="")
        self.app.mostrar(PantallaDiscoVacio)

class PantallaDiscoVacio(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app

        # header
        hdr = tk.Frame(self, bg=BG2)
        hdr.pack(fill="x", padx=0, pady=0)
        tk.Label(hdr, text="disco físico", font=FONT_TITLE,
                 bg=BG2, fg=ACCENT).pack(side="left", padx=20, pady=12)
        tk.Button(hdr, text="cargar datos →",
                  font=FONT_LABEL, bg=ACCENT2, fg="white",
                  relief="flat", padx=16, pady=6,
                  cursor="hand2",
                  command=lambda: app.mostrar(PantallaCarga)
                  ).pack(side="right", padx=20, pady=12)

        # info
        self.info_lbl = tk.Label(self, text="", font=FONT_SMALL,
                                 bg=BG, fg=TEXT_DIM, justify="left")
        self.info_lbl.pack(anchor="w", padx=24, pady=(8, 0))

        # disco visual
        self.canvas = DiscoVisual(self, width=900, height=500)
        self.canvas.pack(fill="both", expand=True, padx=16, pady=10)
        self.canvas.bind("<Configure>", lambda e: self.dibujar())

    def al_mostrar(self):
        self.dibujar()

    def dibujar(self):
        d = self.app.disco
        if d is None:
            return
        cap  = d.capacidad_total_bytes()
        used = d.n_registros * self.app.tam_registro if self.app.tam_registro else 0
        self.info_lbl.config(
            text=f"capacidad: {cap} bytes   |   "
                 f"usados: {used} bytes   |   "
                 f"libres: {cap - used} bytes   |   "
                 f"registros: {d.n_registros}"
        )
        self.canvas.actualizar(d, self.app.tam_registro)

class PantallaCarga(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app        = app
        self.ruta_sql   = tk.StringVar(value="")
        self.ruta_csv   = tk.StringVar(value="")

        hdr = tk.Frame(self, bg=BG2)
        hdr.pack(fill="x")
        tk.Label(hdr, text="cargar datos", font=FONT_TITLE,
                 bg=BG2, fg=ACCENT).pack(side="left", padx=20, pady=12)

        # selección archivos
        sel = tk.Frame(self, bg=BG, pady=16)
        sel.pack(fill="x", padx=24)

        self._fila_archivo(sel, 0, "estructura SQL (.txt)", self.ruta_sql, self.browse_sql)
        self._fila_archivo(sel, 1, "datos CSV (.csv)",      self.ruta_csv, self.browse_csv)


        self.estado_lbl = tk.Label(self, text="", font=FONT_SMALL,
                                   bg=BG, fg=TEXT_DIM)
        self.estado_lbl.pack()

        # disco visual
        self.canvas = DiscoVisual(self, width=900, height=380)
        self.canvas.pack(fill="both", expand=True, padx=16, pady=8)
        self.canvas.bind("<Configure>", lambda e: self.canvas.dibujar())

        # botón siguiente
        tk.Button(self, text="buscar →",
                  font=FONT_LABEL, bg=ACCENT2, fg="white",
                  relief="flat", padx=20, pady=8,
                  cursor="hand2",
                  command=lambda: app.mostrar(PantallaBusqueda)
                  ).pack(pady=8)

    def _fila_archivo(self, parent, row, label, var, cmd):
        tk.Label(parent, text=label, font=FONT_LABEL,
                 bg=BG, fg=TEXT, width=24, anchor="e").grid(
            row=row, column=0, padx=(0, 10), pady=6, sticky="e")
        tk.Entry(parent, textvariable=var, font=FONT_SMALL,
                 bg=BG2, fg=ACCENT, relief="flat", width=50,
                 highlightthickness=1, highlightbackground=ACCENT2,
                 highlightcolor=ACCENT).grid(row=row, column=1, pady=6)
        tk.Button(parent, text="...", font=FONT_SMALL,
                  bg=BG3, fg=TEXT, relief="flat", padx=6,
                  cursor="hand2", command=cmd).grid(
            row=row, column=2, padx=6, pady=6)

    def browse_sql(self):
        f = filedialog.askopenfilename(filetypes=[("Text", "*.txt"), ("All", "*.*")])
        if f:
            self.ruta_sql.set(f)

    def browse_csv(self):
        f = filedialog.askopenfilename(filetypes=[("CSV", "*.csv"), ("All", "*.*")])
        if f:
            self.ruta_csv.set(f)

    def insertar(self):
        from lector2 import leer_estructura_sql, leer_csv, serializar

        if not self.ruta_sql.get() or not self.ruta_csv.get():
            self.estado_lbl.config(text="selecciona ambos archivos", fg=ROJO)
            return

        try:
            self.app.estructura_db = leer_estructura_sql(self.ruta_sql.get())
            self.app.tam_registro  = sum(c['tam'] for c in self.app.estructura_db)
            registros              = leer_csv(self.ruta_csv.get())
            self.app.registros     = registros
            self.app.tabla_offsets = []

            for registro in registros:
                datos_bytes = serializar(registro, self.app.estructura_db)
                offset      = self.app.disco.escribir_registro(datos_bytes)
                from lector2 import deserializar
                rec = deserializar(datos_bytes, self.app.estructura_db)
                self.app.tabla_offsets.append((offset, rec))

            n = len(self.app.tabla_offsets)
            cap = self.app.disco.capacidad_total_bytes()
            used = n * self.app.tam_registro

            self.estado_lbl.config(
                text=f"{n} registros insertados  |  "
                     f"{used}/{cap} bytes usados  |  "
                     f"tam_registro: {self.app.tam_registro} bytes",
                fg=VERDE
            )
            self.canvas.actualizar(self.app.disco, self.app.tam_registro, n)

        except Exception as e:
            self.estado_lbl.config(text=f"error: {e}", fg=ROJO)

    def al_mostrar(self):
        self.ruta_sql.set(RUTA_SQL)
        self.ruta_csv.set(RUTA_CSV)
        self.insertar()

class PantallaBusqueda(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app

        hdr = tk.Frame(self, bg=BG2)
        hdr.pack(fill="x")
        tk.Label(hdr, text="búsqueda AVL", font=FONT_TITLE,
                 bg=BG2, fg=ACCENT).pack(side="left", padx=20, pady=12)
        tk.Button(hdr, text="← volver",
                  font=FONT_LABEL, bg=BG3, fg=TEXT,
                  relief="flat", padx=12, pady=6,
                  cursor="hand2",
                  command=lambda: app.mostrar(PantallaCarga)
                  ).pack(side="right", padx=20, pady=12)

        # controles
        ctrl = tk.Frame(self, bg=BG2)
        ctrl.pack(fill="x", padx=0, pady=0)

        tk.Label(ctrl, text="campo:", font=FONT_LABEL,
                 bg=BG2, fg=TEXT).pack(side="left", padx=(20, 6), pady=10)

        self.campo_var = tk.StringVar()
        self.campo_cb  = ttk.Combobox(ctrl, textvariable=self.campo_var,
                                       font=FONT_MONO, width=24, state="readonly")
        self.campo_cb.pack(side="left", padx=6, pady=10)

        tk.Label(ctrl, text="modo:", font=FONT_LABEL,
                 bg=BG2, fg=TEXT).pack(side="left", padx=(20, 6))

        self.modo_var = tk.StringVar(value="exacta")
        ttk.Combobox(ctrl, textvariable=self.modo_var,
                     values=["exacta", "rango"],
                     font=FONT_MONO, width=10, state="readonly"
                     ).pack(side="left", padx=6)
        self.modo_var.trace("w", self.toggle_rango)

        tk.Label(ctrl, text="valor:", font=FONT_LABEL,
                 bg=BG2, fg=TEXT).pack(side="left", padx=(20, 6))
        self.val1 = tk.Entry(ctrl, font=FONT_MONO, bg=BG, fg=ACCENT,
                              insertbackground=ACCENT, relief="flat", width=12,
                              highlightthickness=1, highlightbackground=ACCENT2)
        self.val1.pack(side="left", padx=4)

        self.lbl_hasta = tk.Label(ctrl, text="hasta:", font=FONT_LABEL,
                                   bg=BG2, fg=TEXT)
        self.val2 = tk.Entry(ctrl, font=FONT_MONO, bg=BG, fg=ACCENT,
                              insertbackground=ACCENT, relief="flat", width=12,
                              highlightthickness=1, highlightbackground=ACCENT2)

        tk.Button(ctrl, text="buscar",
                  font=FONT_LABEL, bg=ACCENT, fg=BG,
                  relief="flat", padx=16, pady=4,
                  cursor="hand2", command=self.buscar
                  ).pack(side="left", padx=20)

        # panel inferior: disco + resultados
        inf = tk.Frame(self, bg=BG)
        inf.pack(fill="both", expand=True, padx=0, pady=0)
        inf.grid_columnconfigure(0, weight=2)
        inf.grid_columnconfigure(1, weight=3)
        inf.grid_rowconfigure(0, weight=1)

        # disco visual izquierda
        self.canvas = DiscoVisual(inf, width=400, height=400)
        self.canvas.grid(row=0, column=0, sticky="nsew", padx=12, pady=10)
        self.canvas.bind("<Configure>", lambda e: self.canvas.dibujar())

        # resultados derecha
        res_frame = tk.Frame(inf, bg=BG)
        res_frame.grid(row=0, column=1, sticky="nsew", padx=(0, 12), pady=10)
        res_frame.grid_rowconfigure(1, weight=1)
        res_frame.grid_columnconfigure(0, weight=1)

        self.res_lbl = tk.Label(res_frame, text="", font=FONT_SMALL,
                                 bg=BG, fg=TEXT_DIM)
        self.res_lbl.grid(row=0, column=0, sticky="w", pady=(0, 4))

        self.txt = tk.Text(res_frame, font=FONT_SMALL, bg=BG2, fg=TEXT,
                           relief="flat", wrap="none",
                           insertbackground=ACCENT)
        self.txt.grid(row=1, column=0, sticky="nsew")

        sb = tk.Scrollbar(res_frame, command=self.txt.yview)
        sb.grid(row=1, column=1, sticky="ns")
        self.txt.config(yscrollcommand=sb.set)

        # tags de color en el text
        self.txt.tag_config("clave",    foreground=AMARILLO)
        self.txt.tag_config("dir_reg",  foreground=SECTOR_REGISTRO)
        self.txt.tag_config("dir_dato", foreground=SECTOR_DATO)
        self.txt.tag_config("campo",    foreground=TEXT_DIM)
        self.txt.tag_config("valor",    foreground=ACCENT)

    def al_mostrar(self):
        if self.app.estructura_db:
            nombres = [c['nombre'] for c in self.app.estructura_db]
            self.campo_cb['values'] = nombres
            self.campo_cb.current(0)
        self.canvas.actualizar(self.app.disco, self.app.tam_registro)
    def toggle_rango(self, *args):
        if self.modo_var.get() == "rango":
            self.lbl_hasta.pack(side="left", padx=(12, 6))
            self.val2.pack(side="left", padx=4)
        else:
            self.lbl_hasta.pack_forget()
            self.val2.pack_forget()

    def buscar(self):
        from avl import construir_indice, buscar, buscar_rango, offset_desde_nreg

        campo = self.campo_var.get()
        if not campo:
            return

        idx_campo = next(
            (i for i, c in enumerate(self.app.estructura_db) if c['nombre'] == campo),
            None
        )
        tipo = self.app.estructura_db[idx_campo]['tipo']

        def convertir(v):
            if tipo == 'int':   return int(v)
            if tipo == 'float': return float(v)
            return v

        try:
            v1 = convertir(self.val1.get().strip())
            v2 = convertir(self.val2.get().strip()) if self.modo_var.get() == "rango" else None
        except:
            self.res_lbl.config(text="valor inválido", fg=ROJO)
            return

        raiz = construir_indice(
            self.app.tabla_offsets,
            self.app.estructura_db,
            campo,
            self.app.tam_registro
        )

        if self.modo_var.get() == "exacta":
            resultado = buscar(raiz, v1)
        else:
            resultado = buscar_rango(raiz, v1, v2)

        raiz = None

        self.txt.delete("1.0", "end")

        if not resultado:
            self.res_lbl.config(text="sin resultados", fg=ROJO)
            self.canvas.actualizar(self.app.disco, self.app.tam_registro)
            return

        self.res_lbl.config(
            text=f"{len(resultado)} resultado(s) para '{campo}' = {v1}",
            fg=VERDE
        )

        primer_nreg = resultado[0][0]
        primer_offset = offset_desde_nreg(primer_nreg, self.app.tam_registro)
        off_campo = sum(
            self.app.estructura_db[i]['tam']
            for i in range(idx_campo)
        )
        offset_dato = primer_offset + off_campo

        p_r,  s_r,  pi_r,  sec_r,  _ = self.app.disco._offset_a_dir(primer_offset)
        p_d,  s_d,  pi_d,  sec_d,  _ = self.app.disco._offset_a_dir(offset_dato)

        self.canvas.actualizar(
            self.app.disco,
            self.app.tam_registro,
            sector_registro=(p_r, s_r, pi_r, sec_r),
            sector_dato=(p_d, s_d, pi_d, sec_d)
        )

        from lector2 import deserializar

        for i, (n_reg, plato) in enumerate(resultado, 1):
            offset  = offset_desde_nreg(n_reg, self.app.tam_registro)
            datos   = self.app.disco.leer_registro(offset, self.app.tam_registro)
            rec     = deserializar(datos, self.app.estructura_db)

            off_c   = sum(self.app.estructura_db[j]['tam'] for j in range(idx_campo))
            off_d   = offset + off_c
            p_r2, s_r2, pi_r2, sec_r2, byte_r = self.app.disco._offset_a_dir(offset)
            p_d2, s_d2, pi_d2, sec_d2, byte_d = self.app.disco._offset_a_dir(off_d)

            self.txt.insert("end", f"\n[{i}] n_reg={n_reg}  offset={offset}\n", "clave")
            self.txt.insert("end",
                f"  registro → Plato:{p_r2} Sup:{s_r2} Pista:{pi_r2} Sector:{sec_r2} Byte:{byte_r}\n",
                "dir_reg"
            )
            self.txt.insert("end",
                f"  dato '{campo}' → Plato:{p_d2} Sup:{s_d2} Pista:{pi_d2} Sector:{sec_d2} Byte:{byte_d}\n",
                "dir_dato"
            )

            for c, v in zip(self.app.estructura_db, rec):
                self.txt.insert("end", f"    {c['nombre']:<30}", "campo")
                self.txt.insert("end", f": {v}\n", "valor")

            self.txt.insert("end", "\n")

if __name__ == "__main__":
    app = App()
    app.mainloop()