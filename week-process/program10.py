import tkinter as tk
from tkinter import filedialog, ttk, colorchooser
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
    archivo = filedialog.askopenfilename(filetypes=[("Archivos CSV o Excel", "*.csv *.xlsx")])
    if archivo:
        try:
            if archivo.endswith(".csv"):
                df = pd.read_csv(archivo)
            else:
                df = pd.read_excel(archivo, engine="openpyxl")

            app.df = df
            columnas = list(df.columns)
            combo_source["values"] = columnas
            combo_target["values"] = columnas
            combo_keywords["values"] = columnas
            label_estado.config(text=f"✅ Archivo cargado: {archivo.split('/')[-1]}")
        except Exception as e:
            label_estado.config(text=f"⚠️ Error: {str(e)}")

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
            keywords = str(row[keywords_col]).split(";")
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
    app.lista_keywords = sorted(keywords_unicas)  # Guardamos las únicas
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

def generar_red_general():
    if not hasattr(app, "df"):
        return
    source = combo_source.get()
    target = combo_target.get()
    if source and target:
        G = crear_red_general(app.df, source, target)
        app.grafo_general = G
        app.grafo_keywords = None  # Limpiar la red de keywords
        app.red_con_cluster = False
        dibujar_red(G)

def generar_red_keywords():
    if not hasattr(app, "df"):
        return
    col = combo_keywords.get()
    if col:
        G = crear_red_palabras_clave(app.df, col)
        app.grafo_keywords = G
        app.grafo_general = None  # Limpiar la red general
        app.red_con_cluster = False
        dibujar_red(G)

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

    # Scrollbars
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
          font=("Segoe UI", 11, "bold"), bg="#8ecae6", fg="white", padx=10, pady=6).pack(pady=(5, 5))

label_estado = tk.Label(frame_controles, text="", font=("Segoe UI", 10), fg="green", bg="#f0f4f8")
label_estado.pack()

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
