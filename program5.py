import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import os

# Variables globales para los grafos
G_general = None
G_keywords = None

# Crear ventana principal
app = tk.Tk()
app.title("Visualizador de Redes Bibliométricas")
app.geometry("700x500")

# Función para cargar el archivo
def cargar_archivo():
    file_path = filedialog.askopenfilename(filetypes=[("Archivos CSV o Excel", "*.csv *.xlsx")])
    if not file_path:
        return

    try:
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.endswith('.xlsx'):
            df = pd.read_excel(file_path, engine='openpyxl')
        else:
            raise ValueError("Formato no compatible")
    except Exception as e:
        messagebox.showerror("Error al cargar archivo", str(e))
        return

    app.df = df
    columnas = df.columns.tolist()
    combo_source['values'] = columnas
    combo_target['values'] = columnas
    combo_keywords['values'] = columnas
    messagebox.showinfo("Archivo cargado", f"Archivo cargado con éxito:\n{os.path.basename(file_path)}")

# Función para dibujar grafo
def dibujar_grafo(G, titulo):
    plt.figure(figsize=(10, 8))
    pos = nx.spring_layout(G, seed=42)
    weights = [edata['weight'] for _, _, edata in G.edges(data=True)]
    nx.draw(G, pos, with_labels=True, node_size=500, node_color="skyblue",
            edge_color="gray", width=weights, font_size=9)
    plt.title(titulo)
    plt.axis("off")
    plt.show()

# Función para crear red general
def crear_red_general():
    global G_general
    df = app.df
    source_col = combo_source.get()
    target_col = combo_target.get()

    if not source_col or not target_col:
        messagebox.showwarning("Selección incompleta", "Selecciona columnas para origen y destino")
        return

    G = nx.Graph()
    for _, row in df.iterrows():
        s, t = row[source_col], row[target_col]
        if pd.notna(s) and pd.notna(t):
            if G.has_edge(s, t):
                G[s][t]['weight'] += 1
            else:
                G.add_edge(s, t, weight=1)

    G_general = G
    dibujar_grafo(G, "Red General")

# Función para crear red de palabras clave
def crear_red_palabras_clave():
    global G_keywords
    df = app.df
    kw_col = combo_keywords.get()

    if not kw_col:
        messagebox.showwarning("Selección incompleta", "Selecciona la columna de palabras clave")
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

# Exportar imagen
def exportar_imagen(grafo, nombre_por_defecto):
    if grafo is None:
        messagebox.showwarning("Red vacía", "Primero genera una red.")
        return

    file_img = filedialog.asksaveasfilename(defaultextension=".png",
                                            filetypes=[("Imagen PNG", "*.png")],
                                            title="Guardar red como imagen",
                                            initialfile=nombre_por_defecto)
    if file_img:
        plt.figure(figsize=(10, 8))
        pos = nx.spring_layout(grafo, seed=42)
        weights = [edata['weight'] for _, _, edata in grafo.edges(data=True)]
        nx.draw(grafo, pos, with_labels=True, node_size=500, node_color="skyblue",
                edge_color="gray", width=weights, font_size=9)
        plt.title(nombre_por_defecto)
        plt.axis("off")
        plt.savefig(file_img)
        plt.close()
        messagebox.showinfo("Guardado", f"Imagen guardada como {file_img}")

# Exportar GEXF
def exportar_gexf(grafo, nombre_por_defecto):
    if grafo is None:
        messagebox.showwarning("Red vacía", "Primero genera una red.")
        return

    file_gexf = filedialog.asksaveasfilename(defaultextension=".gexf",
                                             filetypes=[("Archivo GEXF", "*.gexf")],
                                             title="Guardar red como archivo",
                                             initialfile=nombre_por_defecto)
    if file_gexf:
        nx.write_gexf(grafo, file_gexf)
        messagebox.showinfo("Guardado", f"Grafo exportado como {file_gexf}")

# Elementos de la interfaz
frame_form = tk.Frame(app)
frame_form.pack(pady=20)

tk.Button(frame_form, text="📂 Cargar archivo CSV/XLSX", command=cargar_archivo).grid(row=0, column=0, columnspan=2, pady=10)

tk.Label(frame_form, text="Columna origen:").grid(row=1, column=0, sticky="e")
combo_source = ttk.Combobox(frame_form, width=30)
combo_source.grid(row=1, column=1)

tk.Label(frame_form, text="Columna destino:").grid(row=2, column=0, sticky="e")
combo_target = ttk.Combobox(frame_form, width=30)
combo_target.grid(row=2, column=1)

tk.Label(frame_form, text="Columna palabras clave:").grid(row=3, column=0, sticky="e")
combo_keywords = ttk.Combobox(frame_form, width=30)
combo_keywords.grid(row=3, column=1)

tk.Button(app, text="🔗 Crear Red General", command=crear_red_general).pack(pady=5)
tk.Button(app, text="🔑 Crear Red de Palabras Clave", command=crear_red_palabras_clave).pack(pady=5)

frame_export = tk.Frame(app)
frame_export.pack(pady=15)

tk.Button(frame_export, text="📷 Exportar imagen red general", command=lambda: exportar_imagen(G_general, "red_general")).grid(row=0, column=0, padx=5, pady=5)
tk.Button(frame_export, text="📷 Exportar imagen red palabras clave", command=lambda: exportar_imagen(G_keywords, "red_keywords")).grid(row=0, column=1, padx=5, pady=5)
tk.Button(frame_export, text="💾 Exportar GEXF red general", command=lambda: exportar_gexf(G_general, "red_general")).grid(row=1, column=0, padx=5, pady=5)
tk.Button(frame_export, text="💾 Exportar GEXF red palabras clave", command=lambda: exportar_gexf(G_keywords, "red_keywords")).grid(row=1, column=1, padx=5, pady=5)

app.mainloop()
