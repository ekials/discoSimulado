import tkinter as tk
import math
from tkinter import ttk, messagebox
import os

#RUTA_SQL = "C:\\Users\\lolitascim\\bd\\trabajo_50%\\estructura.txt"
#RUTA_CSV = "C:\\Users\\lolitascim\\bd\\trabajo_50%\\prueba.csv"

#RUTA_SQL = "D:\\CCOMP\\CCOMP - UCSP\Quinto Semestre\\BD2\proyecto\\code\\7ProyectoFinal\\estructura.txt"
#RUTA_CSV = "D:\\CCOMP\\CCOMP - UCSP\Quinto Semestre\\BD2\proyecto\\code\\7ProyectoFinal\\prueba.csv"


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RUTA_SQL = os.path.join(BASE_DIR, "shipments.txt")
RUTA_CSV = os.path.join(BASE_DIR, "shipments.csv")

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

        self.disco         = None
        self.estructura_db = None
        self.tam_registro  = 0
        self.registros     = None
        self.tabla_offsets = []

        self.container = tk.Frame(self, bg=BG)
        self.container.pack(fill="both", expand=True)

        self.frames = {}
        for F in (PantallaConfig, PantallaCarga, PantallaBusqueda):
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
    def __init__(self, parent, on_click_sector=None, **kwargs):
        super().__init__(parent, bg=BG, highlightthickness=0, **kwargs)
        self.disco              = None
        self.tam_registro       = 0
        self.sectores_registro  = []   
        self.sectores_dato      = []   
        self.n_registros        = 0
        self.on_click_sector    = on_click_sector   
        self.bind("<Button-1>", self._click)

    def actualizar(self, disco, tam_registro, n_registros=0, sectores_registro=None, sectores_dato=None):
        self.disco             = disco
        self.tam_registro      = tam_registro
        self.n_registros       = n_registros
        self.sectores_registro = sectores_registro or []
        self.sectores_dato     = sectores_dato or []
        self.dibujar()

    def _click(self, event):
        if not self.on_click_sector:
            return
        item = self.find_closest(event.x, event.y)
        if not item:
            return
        tags = self.gettags(item[0])
        for tag in tags:
            if tag.startswith("sec_"):
                p, s, t, sec = map(int, tag[4:].split("_"))
                self.on_click_sector((p, s, t, sec))
                return

    def dibujar(self):
        self.delete("all")
        if self.disco is None:
            return

        disco = self.disco
        ancho = self.winfo_width()
        if ancho < 10:
            ancho = 900

        #bytes_usados   = self.n_registros * self.tam_registro if self.tam_registro else 0
        bytes_usados = disco.offset_actual    
        bytes_por_plato = 2 * disco.n_pistas * disco.n_sectores * disco.bytes_por_sector

        PAD     = 24
        GAP_P   = 30   # gap entre platos
        GAP_S   = 5    # gap entre superficies
        H_LABEL = 26

        total_secs  = disco.n_pistas * disco.n_sectores
        ancho_disp  = ancho - 2 * PAD - 70   
        #sec_w       = max(14, (ancho_disp // total_secs) - 3)
        sec_w       = min(18, max(8, (ancho_disp // total_secs) - 2))
        sec_h       = 34

        y = PAD

        for p in range(disco.n_platos):
            
            self.create_text(
                PAD, y + H_LABEL // 2,
                text=f"Plato {p}",
                fill=ACCENT, font=FONT_LABEL,
                anchor="w"
            )
            y += H_LABEL

            for s in range(2):
                self.create_text(
                    PAD + 4, y + sec_h // 2,
                    text=f"S{s}",
                    fill=TEXT_DIM, font=FONT_SMALL,
                    anchor="w"
                )

                x = PAD + 62

                for t in range(disco.n_pistas):
                    for sec in range(disco.n_sectores):
                        addr        = (p, s, t, sec)
                        offset_byte = (
                            p * bytes_por_plato +
                            s * disco.n_pistas * disco.n_sectores * disco.bytes_por_sector +
                            t * disco.n_sectores * disco.bytes_por_sector +
                            sec * disco.bytes_por_sector
                        )

                        if addr in self.sectores_dato:
                            color = SECTOR_DATO
                        elif addr in self.sectores_registro:
                            color = SECTOR_REGISTRO
                        #elif offset_byte < bytes_usados:
                        elif offset_byte < bytes_usados + disco.bytes_por_sector: 
                            color = SECTOR_OCUPADO
                        else:
                            color = SECTOR_LIBRE

                        tag = f"sec_{p}_{s}_{t}_{sec}"
                        self.create_rectangle(
                            x, y,
                            x + sec_w, y + sec_h,
                            fill=color,
                            outline=BG,
                            width=2,
                            tags=(tag,)
                        )
                        x += sec_w + 3

                y += sec_h + GAP_S

            y += GAP_P

        total_secs = disco.n_pistas * disco.n_sectores
        ancho_real = PAD + 62 + total_secs * (sec_w + 3) + PAD
        alto_real  = y + 60
        self.config(scrollregion=(0, 0, ancho_real, alto_real))

        items = [
            (SECTOR_LIBRE,    "libre"),
            (SECTOR_OCUPADO,  "ocupado"),
            (SECTOR_REGISTRO, "registro encontrado"),
            (SECTOR_DATO,     "dato buscado"),
        ]
        lx = PAD
        ly = y + 12
        for color, label in items:
            self.create_rectangle(lx, ly, lx + 14, ly + 14, fill=color, outline="")
            self.create_text(lx + 20, ly + 7, text=label, fill=TEXT_DIM, font=FONT_SMALL, anchor="w")
            lx += len(label) * 7 + 30

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
        self.app.mostrar(PantallaCarga)

class PantallaCarga(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app

        hdr = tk.Frame(self, bg=BG2)
        hdr.pack(fill="x")
        tk.Label(hdr, text="cargar datos", font=FONT_TITLE,
                 bg=BG2, fg=ACCENT).pack(side="left", padx=20, pady=12)

        self.estado_lbl = tk.Label(self, text="", font=FONT_SMALL,
                                   bg=BG, fg=TEXT_DIM)
        self.estado_lbl.pack(pady=(12, 0))

        inf = tk.Frame(self, bg=BG)
        inf.pack(fill="both", expand=True, padx=0, pady=0)
        inf.grid_columnconfigure(0, weight=3)
        inf.grid_columnconfigure(1, weight=2)
        inf.grid_rowconfigure(0, weight=1)

        #self.canvas = DiscoVisual(inf, on_click_sector=self.click_sector, width=700, height=420)
        #self.canvas.grid(row=0, column=0, sticky="nsew", padx=12, pady=10)
        #self.canvas.bind("<Configure>", lambda e: self.canvas.dibujar())

        canvas_frame = tk.Frame(inf, bg=BG)
        canvas_frame.grid(row=0, column=0, sticky="nsew", padx=12, pady=10)
        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)

        self.canvas = DiscoVisual(canvas_frame, on_click_sector=self.click_sector,
                                width=700, height=420)
        self.canvas.grid(row=0, column=0, sticky="nsew")

        h_scroll = tk.Scrollbar(canvas_frame, orient="horizontal",
                                command=self.canvas.xview, bg=BG2)
        h_scroll.grid(row=1, column=0, sticky="ew")
        self.canvas.config(xscrollcommand=h_scroll.set, scrollregion=(0, 0, 2000, 600))
        self.canvas.bind("<Configure>", lambda e: self.canvas.dibujar())

        self.canvas.bind("<Shift-MouseWheel>", lambda e: self.canvas.xview_scroll(
            -1 if e.delta > 0 else 1, "units"))
        
        det_frame = tk.Frame(inf, bg=BG)
        det_frame.grid(row=0, column=1, sticky="nsew", padx=(0, 12), pady=10)
        det_frame.grid_rowconfigure(1, weight=1)
        det_frame.grid_columnconfigure(0, weight=1)

        self.det_lbl = tk.Label(det_frame, text="haz click en un sector para ver su contenido",
                                 font=FONT_SMALL, bg=BG, fg=TEXT_DIM)
        self.det_lbl.grid(row=0, column=0, sticky="w", pady=(0, 4))

        self.det_txt = tk.Text(det_frame, font=FONT_SMALL, bg=BG2, fg=TEXT,
                                relief="flat", wrap="word",
                                insertbackground=ACCENT)
        self.det_txt.grid(row=1, column=0, sticky="nsew")

        sb = tk.Scrollbar(det_frame, command=self.det_txt.yview)
        sb.grid(row=1, column=1, sticky="ns")
        self.det_txt.config(yscrollcommand=sb.set)

        self.det_txt.tag_config("clave", foreground=AMARILLO)
        self.det_txt.tag_config("campo", foreground=TEXT_DIM)
        self.det_txt.tag_config("valor", foreground=ACCENT)

        tk.Button(self, text="buscar →",
                  font=FONT_LABEL, bg=ACCENT2, fg="white",
                  relief="flat", padx=20, pady=8,
                  cursor="hand2",
                  command=lambda: app.mostrar(PantallaBusqueda)
                  ).pack(pady=8)

    def click_sector(self, direccion):
        self.det_txt.delete("1.0", "end")

        if self.app.disco is None or not self.app.tabla_offsets:
            self.det_lbl.config(text="no hay datos cargados")
            return

        campos = self.app.disco.campos_en_sector(
            direccion, self.app.tabla_offsets, self.app.estructura_db
        )

        p, s, t, sec = direccion
        self.det_lbl.config(
            text=f"sector → Plato:{p} Sup:{s} Pista:{t} Sector:{sec}"
        )

        if not campos:
            self.det_txt.insert("end", "  (sector libre, sin datos)\n", "campo")
            return

        registros_vistos = {}
        for offset_reg, nombre_campo, valor in campos:
            registros_vistos.setdefault(offset_reg, []).append((nombre_campo, valor))

        for offset_reg, lista_campos in registros_vistos.items():
            self.det_txt.insert("end", f"\nregistro offset={offset_reg}\n", "clave")
            for nombre_campo, valor in lista_campos:
                self.det_txt.insert("end", f"  {nombre_campo:<28}", "campo")
                self.det_txt.insert("end", f": {valor}\n", "valor")

    def insertar(self):
        from lector2 import leer_estructura_sql, leer_csv, serializar, deserializar

        try:
            self.app.estructura_db = leer_estructura_sql(RUTA_SQL)
            self.app.tam_registro  = sum(c['tam'] for c in self.app.estructura_db)
            registros              = leer_csv(RUTA_CSV)
            self.app.registros     = registros
            self.app.tabla_offsets = []

            insertados_ok = 0
            disco_lleno   = False

            for i, registro in enumerate(registros):
                try:
                    datos_bytes = serializar(registro, self.app.estructura_db)
                    offset      = self.app.disco.escribir_registro(datos_bytes, self.app.estructura_db)
                    rec         = deserializar(datos_bytes, self.app.estructura_db)
                    self.app.tabla_offsets.append((offset, rec))
                    insertados_ok += 1
                except Exception:
                    disco_lleno = True
                    break

            n   = len(self.app.tabla_offsets)
            cap = self.app.disco.capacidad_total_bytes()

            if disco_lleno:
                self.estado_lbl.config(
                    text=f"disco lleno: se insertaron {insertados_ok} de {len(registros)} registros  |  "
                        f"tam_registro: {self.app.tam_registro} bytes",
                    fg=AMARILLO
                )
            else:
                self.estado_lbl.config(
                    text=f"{n} registros insertados  |  "
                        f"{self.app.disco.offset_actual}/{cap} bytes usados  |  "
                        f"tam_registro: {self.app.tam_registro} bytes",
                    fg=VERDE
                )

            self.canvas.actualizar(self.app.disco, self.app.tam_registro, n)

        except Exception as e:
            self.estado_lbl.config(text=f"error: {e}", fg=ROJO)

    def al_mostrar(self):
        if not self.app.tabla_offsets:
            self.insertar()
        else:
            n = len(self.app.tabla_offsets)
            self.canvas.actualizar(self.app.disco, self.app.tam_registro, n)

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

        inf = tk.Frame(self, bg=BG)
        inf.pack(fill="both", expand=True, padx=0, pady=0)
        inf.grid_columnconfigure(0, weight=2)
        inf.grid_columnconfigure(1, weight=3)
        inf.grid_rowconfigure(0, weight=1)

        #self.canvas = DiscoVisual(inf, width=400, height=400)
        #self.canvas.grid(row=0, column=0, sticky="nsew", padx=12, pady=10)
        #self.canvas.bind("<Configure>", lambda e: self.canvas.dibujar())
        canvas_frame2 = tk.Frame(inf, bg=BG)
        canvas_frame2.grid(row=0, column=0, sticky="nsew", padx=12, pady=10)
        canvas_frame2.grid_rowconfigure(0, weight=1)
        canvas_frame2.grid_columnconfigure(0, weight=1)

        self.canvas = DiscoVisual(canvas_frame2, width=400, height=400)
        self.canvas.grid(row=0, column=0, sticky="nsew")

        h_scroll2 = tk.Scrollbar(canvas_frame2, orient="horizontal",
                                command=self.canvas.xview, bg=BG2)
        h_scroll2.grid(row=1, column=0, sticky="ew")
        self.canvas.config(xscrollcommand=h_scroll2.set, scrollregion=(0, 0, 2000, 600))
        self.canvas.bind("<Configure>", lambda e: self.canvas.dibujar())

        self.canvas.bind("<Shift-MouseWheel>", lambda e: self.canvas.xview_scroll(
            -1 if e.delta > 0 else 1, "units"))
        
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
        from avl import construir_indice, buscar, buscar_rango
        from lector2 import deserializar

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
            if tipo == 'double': return float(v)
            #return v
            return v.lower()

        try:
            v1 = convertir(self.val1.get().strip())
            v2 = convertir(self.val2.get().strip()) if self.modo_var.get() == "rango" else None
        except:
            self.res_lbl.config(text="valor inválido", fg=ROJO)
            return

        raiz = construir_indice(
            self.app.tabla_offsets,
            self.app.estructura_db,
            campo
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

        sectores_registro_total = []
        sectores_dato_total     = []

        for i, (offset, plato) in enumerate(resultado, 1):
            datos = self.app.disco.leer_registro(offset, self.app.estructura_db)
            rec   = deserializar(datos, self.app.estructura_db)

            sectores_registro_total.extend(
                self.app.disco.sectores_ocupados(offset, self.app.estructura_db)
            )
            sectores_dato_total.extend(
                self.app.disco.sectores_campo(offset, self.app.estructura_db, idx_campo)
            )

            off_d = self.app.disco.offset_campo(offset, self.app.estructura_db, idx_campo)
            p_r2, s_r2, pi_r2, sec_r2, byte_r = self.app.disco._offset_a_dir(offset)
            p_d2, s_d2, pi_d2, sec_d2, byte_d = self.app.disco._offset_a_dir(off_d)

            self.txt.insert("end", f"\n[{i}] offset={offset} \n", "clave")
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

        sectores_registro_total = [
            s for s in dict.fromkeys(sectores_registro_total)
            if s not in sectores_dato_total
        ]
        sectores_dato_total = list(dict.fromkeys(sectores_dato_total))

        self.canvas.actualizar(
            self.app.disco,
            self.app.tam_registro,
            sectores_registro=sectores_registro_total,
            sectores_dato=sectores_dato_total
        )

if __name__ == "__main__":
    app = App()
    app.mainloop()