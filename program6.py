import tkinter as tk
from tkinter import filedialog, ttk
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

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
    for _, row in df.iterrows():
        try:
            keywords = str(row[keywords_col]).split(";")
            keywords = [k.strip() for k in keywords if k.strip()]
            for i in range(len(keywords)):
                for j in range(i + 1, len(keywords)):
                    k1, k2 = keywords[i], keywords[j]
                    if G.has_edge(k1, k2):
                        G[k1][k2]["weight"] += 1
                    else:
                        G.add_edge(k1, k2, weight=1)
        except:
            continue
    return G

def dibujar_red(G):
    if app.canvas_network:
        app.canvas_network.get_tk_widget().destroy()

    zoom = app.zoom_level

    fig, ax = plt.subplots(figsize=(8, 6))
    pos = nx.spring_layout(G, seed=42, scale=zoom)
    weights = [edata["weight"] for _, _, edata in G.edges(data=True)]

    nx.draw(
        G, pos, ax=ax,
        with_labels=True,
        node_size=500 * zoom,
        node_color="#90caf9",
        edge_color=weights,
        width=2,
        edge_cmap=plt.cm.Blues,
        font_size=int(9 * zoom)
    )
    ax.set_title("Red generada", fontsize=14)

    canvas = FigureCanvasTkAgg(fig, master=frame_output)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)
    app.canvas_network = canvas

def generar_red_general():
    if not hasattr(app, "df"):
        return
    source = combo_source.get()
    target = combo_target.get()
    if source and target:
        G = crear_red_general(app.df, source, target)
        app.grafo_general = G
        dibujar_red(G)

def generar_red_keywords():
    if not hasattr(app, "df"):
        return
    col = combo_keywords.get()
    if col:
        G = crear_red_palabras_clave(app.df, col)
        app.grafo_keywords = G
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

# Interfaz
app = tk.Tk()
app.title("Visualizador de Redes Bibliométricas")
app.geometry("1200x700")
app.configure(bg="#e0f7fa")
app.canvas_network = None
app.zoom_level = 1.0  # Nivel de zoom inicial

style = {"font": ("Segoe UI", 10), "bg": "#f0f4f8"}

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

def actualizar_zoom(valor):
    app.zoom_level = float(valor)
    # Redibuja el grafo actual si existe
    if hasattr(app, "grafo_keywords") and app.grafo_keywords is not None:
        dibujar_red(app.grafo_keywords)
    elif hasattr(app, "grafo_general") and app.grafo_general is not None:
        dibujar_red(app.grafo_general)

tk.Label(frame_controles, text="🔍 Zoom del grafo", **style).pack(pady=(25, 0))
zoom_slider = tk.Scale(frame_controles, from_=0.5, to=2.5, resolution=0.1, orient="horizontal",
                       length=200, command=actualizar_zoom, bg="#f0f4f8")
zoom_slider.set(1.0)
zoom_slider.pack(pady=(0, 10))

def cerrar_app():
    app.destroy()  # Esto detiene el loop y cierra la ventana


app.protocol("WM_DELETE_WINDOW", cerrar_app)
app.mainloop()
