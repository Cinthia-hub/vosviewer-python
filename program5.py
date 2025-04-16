import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import os
import warnings

# Ignorar warning de openpyxl
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

# Variables globales
G_general = None
G_keywords = None

# Crear ventana principal
app = tk.Tk()
app.title("Visualizador de Redes Bibliométricas")
app.configure(bg="#f0f4f8")
app.geometry("900x700")

# Función para cargar archivo
def cargar_archivo():
    file_path = filedialog.askopenfilename(filetypes=[("Archivos CSV o Excel", "*.csv *.xlsx")])
    if not file_path:
        return
    try:
        if file_path.endswith(".csv"):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path, engine="openpyxl")
        app.df = df
        cols = df.columns.tolist()
        combo_source['values'] = cols
        combo_target['values'] = cols
        combo_keywords['values'] = cols
        label_estado.config(text=f"✅ Archivo cargado: {os.path.basename(file_path)}", fg="green")
    except Exception as e:
        label_estado.config(text=f"⚠️ Error: {str(e)}", fg="red")

# Funciones para grafo
def crear_red_general():
    global G_general
    df = app.df
    s, t = combo_source.get(), combo_target.get()
    if not s or not t:
        messagebox.showwarning("Falta info", "Selecciona origen y destino")
        return
    G = nx.Graph()
    for _, row in df.iterrows():
        if pd.notna(row[s]) and pd.notna(row[t]):
            a, b = row[s], row[t]
            if G.has_edge(a, b):
                G[a][b]['weight'] += 1
            else:
                G.add_edge(a, b, weight=1)
    G_general = G
    dibujar_grafo(G, "Red General")

def crear_red_palabras_clave():
    global G_keywords
    df = app.df
    kw_col = combo_keywords.get()
    if not kw_col:
        messagebox.showwarning("Falta info", "Selecciona columna de keywords")
        return
    G = nx.Graph()
    for _, row in df.iterrows():
        if pd.notna(row[kw_col]):
            keywords = [kw.strip().lower() for kw in str(row[kw_col]).split(';') if kw.strip()]
            for i in range(len(keywords)):
                for j in range(i + 1, len(keywords)):
                    k1, k2 = keywords[i], keywords[j]
                    if G.has_edge(k1, k2):
                        G[k1][k2]['weight'] += 1
                    else:
                        G.add_edge(k1, k2, weight=1)
    G_keywords = G
    dibujar_grafo(G, "Red de Palabras Clave")

def dibujar_grafo(G, titulo):
    plt.figure(figsize=(10, 8))
    pos = nx.spring_layout(G, seed=42)
    weights = [edata['weight'] for _, _, edata in G.edges(data=True)]
    nx.draw(G, pos, with_labels=True, node_size=600, node_color="#7dcfb6",
            edge_color="gray", width=weights, font_size=9)
    plt.title(titulo)
    plt.axis("off")
    plt.show()

# Función exportar
def exportar_imagen(grafo, nombre_por_defecto):
    if grafo is None:
        messagebox.showwarning("Red vacía", "Primero genera una red.")
        return
    file_img = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png")],
                                            initialfile=nombre_por_defecto)
    if file_img:
        plt.figure(figsize=(10, 8))
        pos = nx.spring_layout(grafo, seed=42)
        weights = [edata['weight'] for _, _, edata in grafo.edges(data=True)]
        nx.draw(grafo, pos, with_labels=True, node_size=600, node_color="#7dcfb6",
                edge_color="gray", width=weights, font_size=9)
        plt.title(nombre_por_defecto)
        plt.axis("off")
        plt.savefig(file_img)
        plt.close()
        messagebox.showinfo("Guardado", f"Imagen guardada como {file_img}")

def exportar_gexf(grafo, nombre_por_defecto):
    if grafo is None:
        messagebox.showwarning("Red vacía", "Primero genera una red.")
        return
    file_gexf = filedialog.asksaveasfilename(defaultextension=".gexf", filetypes=[("GEXF", "*.gexf")],
                                             initialfile=nombre_por_defecto)
    if file_gexf:
        nx.write_gexf(grafo, file_gexf)
        messagebox.showinfo("Guardado", f"Grafo exportado como {file_gexf}")

# 🎨 Estilo común
style = {
    "font": ("Segoe UI", 11),
    "bg": "#f0f4f8"
}

# 🧱 Layout general
frame_form = tk.Frame(app, bg="#f0f4f8")
frame_form.pack(pady=20)

tk.Button(frame_form, text="📂 Cargar archivo CSV/XLSX", command=cargar_archivo,
          font=("Segoe UI", 11, "bold"), bg="#8ecae6", fg="white", padx=10, pady=6).grid(row=0, column=0, columnspan=2, pady=10)

# Label de estado debajo del botón
label_estado = tk.Label(frame_form, text="", font=("Segoe UI", 10), fg="green", bg="#f0f4f8")
label_estado.grid(row=1, column=0, columnspan=2, pady=(0, 15))

tk.Label(frame_form, text="Columna origen:", **style).grid(row=2, column=0, sticky="e", padx=10, pady=5)
combo_source = ttk.Combobox(frame_form, width=40)
combo_source.grid(row=2, column=1, pady=5)

tk.Label(frame_form, text="Columna destino:", **style).grid(row=3, column=0, sticky="e", padx=10, pady=5)
combo_target = ttk.Combobox(frame_form, width=40)
combo_target.grid(row=3, column=1, pady=5)

tk.Label(frame_form, text="Columna palabras clave:", **style).grid(row=4, column=0, sticky="e", padx=10, pady=5)
combo_keywords = ttk.Combobox(frame_form, width=40)
combo_keywords.grid(row=4, column=1, pady=5)

# 🔘 Botones de generación
frame_buttons = tk.Frame(app, bg="#f0f4f8")
frame_buttons.pack(pady=20)

tk.Button(frame_buttons, text="🔗 Crear Red General", command=crear_red_general,
          bg="#219ebc", fg="white", font=("Segoe UI", 11), padx=10, pady=6).grid(row=0, column=0, padx=20, pady=10)

tk.Button(frame_buttons, text="🔑 Crear Red Palabras Clave", command=crear_red_palabras_clave,
          bg="#023047", fg="white", font=("Segoe UI", 11), padx=10, pady=6).grid(row=0, column=1, padx=20, pady=10)

# 💾 Botones de exportación
frame_export = tk.LabelFrame(app, text="Exportar Redes", font=("Segoe UI", 12, "bold"), bg="#f0f4f8", padx=15, pady=10)
frame_export.pack(pady=10)

tk.Button(frame_export, text="📷 Imagen red general", command=lambda: exportar_imagen(G_general, "red_general"),
          bg="#ffb703", fg="black", font=("Segoe UI", 10), padx=8).grid(row=0, column=0, padx=10, pady=5)

tk.Button(frame_export, text="📷 Imagen palabras clave", command=lambda: exportar_imagen(G_keywords, "red_keywords"),
          bg="#ffb703", fg="black", font=("Segoe UI", 10), padx=8).grid(row=0, column=1, padx=10, pady=5)

tk.Button(frame_export, text="💾 GEXF red general", command=lambda: exportar_gexf(G_general, "red_general"),
          bg="#fb8500", fg="white", font=("Segoe UI", 10), padx=8).grid(row=1, column=0, padx=10, pady=5)

tk.Button(frame_export, text="💾 GEXF palabras clave", command=lambda: exportar_gexf(G_keywords, "red_keywords"),
          bg="#fb8500", fg="white", font=("Segoe UI", 10), padx=8).grid(row=1, column=1, padx=10, pady=5)

# Ejecutar app
app.mainloop()
