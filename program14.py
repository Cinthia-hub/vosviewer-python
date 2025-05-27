import tkinter as tk
from tkinter import filedialog, ttk, messagebox, colorchooser
import pandas as pd
import networkx as nx
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import warnings
import community as community_louvain  # Librería Louvain

# Ignorar warning de openpyxl
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

# Funciones
def cargar_archivo():
    filepath = filedialog.askopenfilename(
        filetypes=[("Archivos CSV", "*.csv"), ("Archivos Excel", "*.xlsx *.xls")]
    )
    if not filepath:
        return

    try:
        app.filepath = filepath
        if filepath.endswith((".xlsx", ".xls")):
            app.excel_file = pd.ExcelFile(filepath)
            app.hojas = app.excel_file.sheet_names
            combo_hojas["values"] = app.hojas
            combo_hojas.set(app.hojas[0])
            label_estado.config(text=f"✅ Excel cargado: {filepath.split('/')[-1]}")
            cargar_columnas_excel()
        else:
            df = pd.read_csv(filepath, header=None)
            app.df_raw = df
            app.hojas = []
            combo_hojas["values"] = []
            combo_hojas.set("")
            label_estado.config(text=f"✅ CSV cargado: {filepath.split('/')[-1]}")
            cargar_columnas_desde_df_csv()
    except Exception as e:
        label_estado.config(text=f"⚠️ Error al cargar: {str(e)}")

def manejar_cambio_hoja(event=None):
    if app.filepath.endswith((".xlsx", ".xls")):  # archivo_excel es un path o workbook abierto
        cargar_columnas_excel()
    else:
        cargar_columnas_desde_df_csv()

def crear_red_general(df, source_col, target_col):
    G = nx.Graph()
    for _, row in df.iterrows():
        source = str(row[source_col])
        target = str(row[target_col])
        if G.has_edge(source, target):
            G[source][target]["weight"] += 1
        else:
            G.add_edge(source, target, weight=1)
    return G

def crear_red_palabras_clave(df, keywords_col):
    G = nx.Graph()
    keywords_unicas = set()
    for _, row in df.iterrows():
        try:
            raw_text = str(row[keywords_col])
            if ";" in raw_text:
                keywords = raw_text.split(";")
            elif "," in raw_text:
                keywords = raw_text.split(",")
            elif "." in raw_text:
                keywords = raw_text.split(".")
            else:
                keywords = [raw_text]

            keywords = [k.strip() for k in keywords if k.strip()]
            keywords_unicas.update(keywords)

            for i in range(len(keywords)):
                for j in range(i + 1, len(keywords)):
                    k1, k2 = keywords[i], keywords[j]
                    if G.has_edge(k1, k2):
                        G[k1][k2]["weight"] += 1
                    else:
                        G.add_edge(k1, k2, weight=1)
        except:
            continue

    app.lista_keywords = sorted(keywords_unicas)
    return G

def dibujar_red(G):
    if app.canvas_network:
        app.canvas_network.get_tk_widget().destroy()
        app.scrollable_canvas.destroy()

    zoom = app.zoom_level

    fig, ax = plt.subplots(figsize=(8 * zoom, 6 * zoom))
    pos = nx.spring_layout(G, seed=42, scale=zoom)

    # Obtener límites de posición para dar padding
    x_vals = [x for x, y in pos.values()]
    y_vals = [y for x, y in pos.values()]
    x_min, x_max = min(x_vals), max(x_vals)
    y_min, y_max = min(y_vals), max(y_vals)

    # Expandimos límites en un 10%
    x_padding = (x_max - x_min) * 0.15
    y_padding = (y_max - y_min) * 0.15

    ax.set_xlim(x_min - x_padding, x_max + x_padding)
    ax.set_ylim(y_min - y_padding, y_max + y_padding)

    weights = [edata["weight"] for _, _, edata in G.edges(data=True)]

    nx.draw(
        G, pos, ax=ax,
        with_labels=True,
        node_size=500 * zoom,
        node_color=app.node_color,
        edge_color=app.node_color,
        width=[1 + (w / max(weights)) * 4 for w in weights],
        edge_cmap=plt.cm.Blues,
        font_size = int(float(slider_texto.get()) * zoom)
    )

    ax.set_title("Red generada", fontsize=14)
    ax.axis("off")  # Oculta ejes

    # Contenedor de scroll
    canvas_frame = tk.Frame(frame_output, bg="white")
    canvas_frame.pack(fill="both", expand=True)
    app.scrollable_canvas = canvas_frame

    h_scrollbar = tk.Scrollbar(canvas_frame, orient="horizontal")
    h_scrollbar.pack(side="bottom", fill="x")

    v_scrollbar = tk.Scrollbar(canvas_frame, orient="vertical")
    v_scrollbar.pack(side="right", fill="y")

    canvas_widget = tk.Canvas(canvas_frame, bg="white",
                              xscrollcommand=h_scrollbar.set,
                              yscrollcommand=v_scrollbar.set)
    canvas_widget.pack(side="left", fill="both", expand=True)

    h_scrollbar.config(command=canvas_widget.xview)
    v_scrollbar.config(command=canvas_widget.yview)

    fig_canvas = FigureCanvasTkAgg(fig, master=canvas_widget)
    fig_canvas.draw()

    widget = fig_canvas.get_tk_widget()
    widget.update_idletasks()
    canvas_widget.create_window((0, 0), window=widget, anchor="nw")

    # Importante: establecer correctamente el tamaño del scroll
    widget.update_idletasks()
    canvas_widget.update_idletasks()
    canvas_widget.config(scrollregion=canvas_widget.bbox("all"))

    app.canvas_network = fig_canvas
    plt.close(fig)

def cargar_columnas_excel(*args):
    hoja = combo_hojas.get()
    if not hoja:
        return
    try:
        fila_ini = int(entry_fila_ini.get()) - 1  # base 1 -> base 0
        col_ini = int(entry_col_ini.get()) - 1    # base 1 -> base 0
        if app.tipo_encabezado.get() == "Fila":
            df = app.excel_file.parse(hoja, header=fila_ini)
            df = df.iloc[:, col_ini:]
            app.df = df
            cargar_columnas_desde_df()
        else:
            df_raw = app.excel_file.parse(hoja, header=None)
            df_raw = df_raw.iloc[fila_ini:, col_ini:]
            app.df_raw = df_raw
            cargar_columnas_desde_df_columnas_encabezado()
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo cargar la hoja:\n{e}")

def cargar_columnas_desde_df_csv():
    try:
        fila_ini = int(entry_fila_ini.get()) - 1  # base 1 -> base 0
        col_ini = int(entry_col_ini.get()) - 1    # base 1 -> base 0
        df = app.df_raw.iloc[fila_ini:, col_ini:]
        if app.tipo_encabezado.get() == "Fila":
            df.columns = df.iloc[0]  # Usa la primera fila como encabezado
            df = df[1:]  # Elimina la fila de encabezado de los datos
            app.df = df.reset_index(drop=True)  # Reinicia el índice
            cargar_columnas_desde_df()
        else:
            app.df_raw = df.reset_index(drop=True)
            cargar_columnas_desde_df_columnas_encabezado()
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo procesar CSV:\n{e}")

def cargar_columnas_desde_df():
    columnas = list(app.df.columns)
    combo_source['values'] = columnas
    combo_target['values'] = columnas
    combo_keywords['values'] = columnas
    combo_source.set('')
    combo_target.set('')
    combo_keywords.set('')

def cargar_columnas_desde_df_columnas_encabezado():
    try:
        col_ini = int(entry_col_ini.get()) - 1
        df = app.df_raw
        df = df.iloc[:, col_ini:]
        app.df = df
        campos = list(df.iloc[:, 0].dropna().astype(str))  # Encabezados en columna
        combo_source['values'] = campos
        combo_target['values'] = campos
        combo_keywords['values'] = campos
        combo_source.set('')
        combo_target.set('')
        combo_keywords.set('')
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo cargar columnas encabezado columna:\n{e}")

def generar_red_general():
    if not hasattr(app, "df"):
        messagebox.showwarning("Aviso", "Primero carga un archivo válido.")
        return

    origen = combo_source.get()
    destino = combo_target.get()
    if not origen or not destino:
        messagebox.showwarning("Aviso", "Selecciona columna origen y destino.")
        return

    G = nx.Graph()

    # Agrega todos los nodos aunque no tengan relaciones
    if app.tipo_encabezado.get() == "Fila":
        for _, row in app.df.iterrows():
            n1 = row[origen]
            n2 = row[destino]
            if not pd.isna(n1):
                G.add_node(n1)
            if not pd.isna(n2):
                G.add_node(n2)
            if pd.isna(n1) or pd.isna(n2):
                continue
            if G.has_edge(n1, n2):
                G[n1][n2]["weight"] += 1
            else:
                G.add_edge(n1, n2, weight=1)

    else:
        df = app.df
        try:
            idx_origen = df[df.iloc[:, 0] == origen].index[0]
            idx_destino = df[df.iloc[:, 0] == destino].index[0]
            for col_i in df.columns[1:]:
                n1 = df.at[idx_origen, col_i]
                n2 = df.at[idx_destino, col_i]
                if not pd.isna(n1):
                    G.add_node(n1)
                if not pd.isna(n2):
                    G.add_node(n2)
                if pd.isna(n1) or pd.isna(n2):
                    continue
                if G.has_edge(n1, n2):
                    G[n1][n2]["weight"] += 1
                else:
                    G.add_edge(n1, n2, weight=1)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar red con encabezado en columna:\n{e}")
            return

    app.grafo_general = G
    app.grafo_keywords = None
    app.red_con_cluster = False
    app.cluster_partition = None
    app.grafo_clusterizado_actual = None
    dibujar_red(G)

def generar_red_keywords():
    if not hasattr(app, "df"):
        messagebox.showwarning("Aviso", "Primero carga un archivo válido.")
        return
    col = combo_keywords.get()
    if not col:
        messagebox.showwarning("Aviso", "Selecciona la columna de palabras clave.")
        return

    if app.tipo_encabezado.get() == "Fila":
        G = crear_red_palabras_clave(app.df, col)
        app.grafo_keywords = G
        app.grafo_general = None  # Limpiar red general
        app.red_con_cluster = False
        app.cluster_partition = None
        app.grafo_clusterizado_actual = None
        dibujar_red(G)
    else:
        messagebox.showinfo("Info", "Generación de red de keywords para encabezado en columna no implementada aún.")

def exportar_png():
    if app.canvas_network:
        if hasattr(app, "grafo_keywords") and app.grafo_keywords is not None:
            default_name = "red_keywords.png"
        else:
            default_name = "red_general.png"

        archivo = filedialog.asksaveasfilename(
            defaultextension=".png",
            initialfile=default_name,
            filetypes=[("PNG Image", "*.png")]
        )
        if archivo:
            app.canvas_network.figure.savefig(archivo)

def exportar_gexf():
    if hasattr(app, "grafo_keywords") and app.grafo_keywords is not None:
        default_name = "red_keywords.gexf"
        grafo = app.grafo_keywords
    elif hasattr(app, "grafo_general") and app.grafo_general is not None:
        default_name = "red_general.gexf"
        grafo = app.grafo_general
    else:
        return

    archivo = filedialog.asksaveasfilename(
        defaultextension=".gexf",
        initialfile=default_name,
        filetypes=[("GEXF File", "*.gexf")]
    )
    if archivo:
        nx.write_gexf(grafo, archivo)

def redibujar_grafo():
    if hasattr(app, "grafo_keywords") and app.grafo_keywords is not None:
        if app.red_con_cluster:
            aplicar_clustering_y_dibujar(app.grafo_keywords)
        else:
            dibujar_red(app.grafo_keywords)
    elif hasattr(app, "grafo_general") and app.grafo_general is not None:
        if app.red_con_cluster:
            aplicar_clustering_y_dibujar(app.grafo_general)
        else:
            dibujar_red(app.grafo_general)

def aplicar_clustering_y_dibujar(G):
    if app.canvas_network:
        app.canvas_network.get_tk_widget().destroy()
        app.scrollable_canvas.destroy()

    zoom = app.zoom_level
    fig, ax = plt.subplots(figsize=(8 * zoom, 6 * zoom))
    pos = nx.spring_layout(G, seed=42, scale=zoom)

    # Solo calcular la partición si no está guardada
    if app.cluster_partition is None or app.grafo_clusterizado_actual is not G:
        app.cluster_partition = community_louvain.best_partition(G)
        app.grafo_clusterizado_actual = G  # Guarda el grafo actual

    # Detectar comunidades
    partition = community_louvain.best_partition(G)

    # Obtener colormap desde el combo
    selected_cmap_name = combo_colormap.get()
    cmap = matplotlib.colormaps.get_cmap(selected_cmap_name)

    # Colores por comunidad
    communities = list(set(partition.values()))
    color_map = cmap.resampled(len(communities))
    node_colors = [color_map(partition[node]) for node in G.nodes()]
    node_color_map = {node: color for node, color in zip(G.nodes(), node_colors)}
    edge_colors = [node_color_map[u] for u, v in G.edges()]

    grosor = slider_grosor.get()
    weights = [edata["weight"] * grosor for _, _, edata in G.edges(data=True)]

    nx.draw(
        G, pos, ax=ax,
        with_labels=True,
        node_size=500 * zoom,
        node_color=node_colors,
        edge_color=edge_colors,
        width=weights,
        font_size=int(float(slider_texto.get()) * zoom)
    )

    ax.set_title("Red con clústeres detectados", fontsize=14)
    ax.axis("off")

    # Scroll y canvas como antes
    canvas_frame = tk.Frame(frame_output, bg="white")
    canvas_frame.pack(fill="both", expand=True)
    app.scrollable_canvas = canvas_frame

    h_scrollbar = tk.Scrollbar(canvas_frame, orient="horizontal")
    h_scrollbar.pack(side="bottom", fill="x")

    v_scrollbar = tk.Scrollbar(canvas_frame, orient="vertical")
    v_scrollbar.pack(side="right", fill="y")

    canvas_widget = tk.Canvas(canvas_frame, bg="white",
                              xscrollcommand=h_scrollbar.set,
                              yscrollcommand=v_scrollbar.set)
    canvas_widget.pack(side="left", fill="both", expand=True)

    h_scrollbar.config(command=canvas_widget.xview)
    v_scrollbar.config(command=canvas_widget.yview)

    fig_canvas = FigureCanvasTkAgg(fig, master=canvas_widget)
    fig_canvas.draw()

    widget = fig_canvas.get_tk_widget()
    widget.update_idletasks()
    canvas_widget.create_window((0, 0), window=widget, anchor="nw")

    canvas_widget.config(scrollregion=canvas_widget.bbox("all"))
    app.canvas_network = fig_canvas
    plt.close(fig)

    app.red_con_cluster = True

def mostrar_filtro_keywords():
    if not hasattr(app, "lista_keywords"):
        return

    ventana = tk.Toplevel(app)
    ventana.title("Seleccionar palabras clave")
    ventana.geometry("400x500")
    ventana.grab_set()

    frame_check = tk.Frame(ventana)
    frame_check.pack(fill="both", expand=True)

    canvas = tk.Canvas(frame_check)
    scrollbar_y = tk.Scrollbar(frame_check, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar_y.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar_y.pack(side="right", fill="y")

    app.keyword_vars = {}
    for palabra in app.lista_keywords:
        var = tk.BooleanVar(value=True)
        chk = tk.Checkbutton(scrollable_frame, text=palabra, variable=var, anchor="w")
        chk.pack(fill="x", padx=5, pady=2)
        app.keyword_vars[palabra] = var

    def aplicar_filtro():
        keywords_seleccionadas = [k for k, var in app.keyword_vars.items() if var.get()]
        if not keywords_seleccionadas:
            return

        # Crear red filtrada
        col = combo_keywords.get()
        G = nx.Graph()
        for _, row in app.df.iterrows():
            try:
                keywords = str(row[col]).split(";")
                keywords = [k.strip() for k in keywords if k.strip() and k.strip() in keywords_seleccionadas]
                for i in range(len(keywords)):
                    for j in range(i + 1, len(keywords)):
                        k1, k2 = keywords[i], keywords[j]
                        if G.has_edge(k1, k2):
                            G[k1][k2]["weight"] += 1
                        else:
                            G.add_edge(k1, k2, weight=1)
            except:
                continue
        app.grafo_keywords = G
        app.red_con_cluster = False
        dibujar_red(G)
        ventana.destroy()

    tk.Button(ventana, text="Aplicar filtro", command=aplicar_filtro, bg="#219ebc", fg="white").pack(pady=10)

# Interfaz
app = tk.Tk()
app.filepath = None
app.excel_file = None
app.df_raw = None
app.hojas = []
app.tipo_encabezado = tk.StringVar(value="Fila")
app.title("Visualizador de Redes Bibliométricas")
app.geometry("1200x700")
app.configure(bg="#e0f7fa")
app.canvas_network = None
app.zoom_level = 1.0  # Nivel de zoom inicial
app.node_color = "#90caf9"
app.cluster_partition = None

style = {"font": ("Arial", 10), "bg": "#f0f4f8"}

# Contenedor horizontal
frame_contenedor_horizontal = tk.Frame(app, bg="#f0f4f8")
frame_contenedor_horizontal.pack(fill="both", expand=True)

frame_controles = tk.Frame(frame_contenedor_horizontal, bg="#f0f4f8", width=280)
frame_controles.pack(side="left", fill="y", padx=10, pady=10)

frame_output = tk.Frame(frame_contenedor_horizontal, bg="white")
frame_output.pack(side="right", fill="both", expand=True, padx=10, pady=10)

# Controles
tk.Button(frame_controles, text="📂 Cargar archivo CSV/XLSX", command=cargar_archivo,
          font=("Segoe UI", 11, "bold"), bg="#8ecae6", fg="white", padx=10, pady=6).pack(pady=(5,5))

label_estado = tk.Label(frame_controles, text="", font=("Segoe UI", 10), fg="green", bg="#f0f4f8")
label_estado.pack()

tk.Label(frame_controles, text="Selecciona hoja (solo Excel):", font=("Arial", 10), bg="#f0f4f8").pack(anchor="w", padx=5, pady=(15,0))
combo_hojas = ttk.Combobox(frame_controles, width=28)
combo_hojas.pack(padx=5, pady=5)
combo_hojas.bind("<<ComboboxSelected>>", manejar_cambio_hoja)

# Campos fila/columna
frame_filas_cols = tk.Frame(frame_controles, bg="#f0f4f8")
frame_filas_cols.pack(anchor="w", padx=5, pady=(10,5))

tk.Label(frame_filas_cols, text="Fila inicio (1 base):", bg="#f0f4f8").grid(row=0, column=0, sticky="w")
entry_fila_ini = tk.Entry(frame_filas_cols, width=6)
entry_fila_ini.grid(row=0, column=1, padx=5)
entry_fila_ini.insert(1, "1")

tk.Label(frame_filas_cols, text="Columna inicio (1 base):", bg="#f0f4f8").grid(row=1, column=0, sticky="w")
entry_col_ini = tk.Entry(frame_filas_cols, width=6)
entry_col_ini.grid(row=1, column=1, padx=5)
entry_col_ini.insert(1, "1")

tk.Label(frame_controles, text="¿Los encabezados están en fila o columna?", font=("Arial", 10), bg="#f0f4f8").pack(anchor="w", padx=5, pady=(10,0))
radio_fila = tk.Radiobutton(frame_controles, text="Fila", variable=app.tipo_encabezado, value="Fila", bg="#f0f4f8", command=manejar_cambio_hoja)
radio_columna = tk.Radiobutton(frame_controles, text="Columna", variable=app.tipo_encabezado, value="Columna", bg="#f0f4f8", command=manejar_cambio_hoja)
radio_fila.pack(anchor="w", padx=10)
radio_columna.pack(anchor="w", padx=10)

entry_fila_ini.bind("<FocusOut>", manejar_cambio_hoja)
entry_col_ini.bind("<FocusOut>", manejar_cambio_hoja)
entry_fila_ini.bind("<Return>", manejar_cambio_hoja)
entry_col_ini.bind("<Return>", manejar_cambio_hoja)

tk.Label(frame_controles, text="Columna origen:", **style).pack(anchor="w", padx=5, pady=(15, 0))
combo_source = ttk.Combobox(frame_controles, width=35)
combo_source.pack(padx=5, pady=5)

tk.Label(frame_controles, text="Columna destino:", **style).pack(anchor="w", padx=5)
combo_target = ttk.Combobox(frame_controles, width=35)
combo_target.pack(padx=5, pady=5)

tk.Label(frame_controles, text="Columna palabras clave:", **style).pack(anchor="w", padx=5, pady=(15, 0))
combo_keywords = ttk.Combobox(frame_controles, width=35)
combo_keywords.pack(padx=5, pady=5)

tk.Button(frame_controles, text="🌐 Generar red general", command=generar_red_general,
          font=("Segoe UI", 10, "bold"), bg="#219ebc", fg="white").pack(pady=(20, 5))

tk.Button(frame_controles, text="🔑 Generar red de keywords", command=generar_red_keywords,
          font=("Segoe UI", 10, "bold"), bg="#023047", fg="white").pack(pady=5)

tk.Button(frame_controles, text="💾 Exportar PNG", command=exportar_png,
          font=("Segoe UI", 10), bg="#ffb703", fg="black").pack(pady=(20, 5))

tk.Button(frame_controles, text="📁 Exportar GEXF", command=exportar_gexf,
          font=("Segoe UI", 10), bg="#fb8500", fg="black").pack(pady=5)

def seleccionar_color():
    color = colorchooser.askcolor(title="Seleccionar color de nodos")[1]
    if color:
        app.node_color = color
        redibujar_grafo()

tk.Button(frame_controles, text="🎨 Detectar y colorear clústeres",
          command=lambda: aplicar_clustering_y_dibujar(
              app.grafo_keywords if app.grafo_keywords else app.grafo_general),
          font=("Segoe UI", 10), bg="#6a994e", fg="white").pack(pady=10)

tk.Label(frame_controles, text="🎨 Esquema de color para clústeres", **style).pack(pady=(10, 0))
combo_colormap = ttk.Combobox(frame_controles, values=[
    "Set1", "Set2", "Set3", "Pastel1", "Accent", "Dark2", "Paired", "Spectral"
])
combo_colormap.set("tab20")  # Valor por defecto
combo_colormap.pack(padx=5, pady=(0, 10))
combo_colormap.bind("<<ComboboxSelected>>", lambda event: redibujar_grafo())

tk.Button(frame_controles, text="🧮 Filtrar palabras clave",
          command=mostrar_filtro_keywords,
          font=("Segoe UI", 10), bg="#0077b6", fg="white").pack(pady=(5, 10))


# Controles a la derecha del grafo
frame_controles_derechos = tk.Frame(frame_output, bg="#f0f4f8", width=240)
frame_controles_derechos.pack(side="right", fill="y", padx=(0, 0), pady=0)

label_grosor = tk.Label(frame_controles_derechos, text="Grosor de aristas", **style)
label_grosor.pack(pady=(10,10))

slider_grosor = tk.Scale(
    frame_controles_derechos,
    from_=0.1,
    to=5,
    resolution=0.1,
    orient="horizontal",
    length=200,
    bg="#f0f4f8"
    #command=lambda val: redibujar_grafo()
)
slider_grosor.set(1.0)
slider_grosor.pack()

def actualizar_zoom(valor):
    app.zoom_level = float(valor)
    redibujar_grafo()

tk.Label(frame_controles_derechos, text="🔍 Zoom del grafo", **style).pack(pady=(25, 10))
zoom_slider = tk.Scale(frame_controles_derechos, from_=0.1, to=3, resolution=0.1, orient="horizontal",
                       length=200, command=actualizar_zoom, bg="#f0f4f8")
zoom_slider.set(1.0)
zoom_slider.pack(pady=(10, 10))

tk.Label(frame_controles_derechos, text="🔠 Tamaño de texto", **style).pack(pady=(10, 10))
slider_texto = tk.Scale(frame_controles_derechos, from_=1, to=20, resolution=1, orient="horizontal",
                        length=200, bg="#f0f4f8", command=lambda val: redibujar_grafo())
slider_texto.set(9)
slider_texto.pack(pady=(10, 10))
slider_grosor.config(command=lambda val: redibujar_grafo())

# Función para cerrar la aplicación
def cerrar_app():
    app.quit()  # Esto asegura que el mainloop se detiene correctamente

app.protocol("WM_DELETE_WINDOW", cerrar_app)  # Captura el clic en la 'X' para cerrarlo

app.cluster_partition = None
app.grafo_clusterizado_actual = None
# Iniciar el mainloop
app.mainloop()
