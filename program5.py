import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import os

# ========== Funciones de lógica ==========
def cargar_archivo():
    filepath = filedialog.askopenfilename(filetypes=[("Archivos CSV o Excel", "*.csv *.xlsx")])
    if not filepath:
        return

    ext = os.path.splitext(filepath)[-1]
    try:
        if ext == ".csv":
            df = pd.read_csv(filepath)
        elif ext == ".xlsx":
            df = pd.read_excel(filepath)
        else:
            raise ValueError("Formato no soportado")
    except Exception as e:
        messagebox.showerror("Error al cargar archivo", str(e))
        return

    columnas = df.columns.tolist()
    combo_source['values'] = columnas
    combo_target['values'] = columnas
    combo_keywords['values'] = columnas

    combo_source.set("")
    combo_target.set("")
    combo_keywords.set("")

    app.df = df
    label_status.config(text=f"Archivo cargado: {os.path.basename(filepath)} ✅")


def crear_red_general():
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

    dibujar_grafo(G, "Red General")

def crear_red_palabras_clave():
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

    dibujar_grafo(G, "Red de Palabras Clave")

def dibujar_grafo(G, titulo):
    plt.figure(figsize=(10, 8))
    pos = nx.spring_layout(G, seed=42)
    weights = [edata['weight'] for _, _, edata in G.edges(data=True)]

    nx.draw(G, pos, with_labels=True, node_size=500, node_color="skyblue", edge_color="gray",
            width=weights, font_size=9)
    plt.title(titulo)
    plt.axis("off")
    plt.tight_layout()
    plt.show()

def dibujar_grafo(G, titulo):
    import os
    from tkinter import filedialog

    # Mostrar el grafo
    plt.figure(figsize=(10, 8))
    pos = nx.spring_layout(G, seed=42)
    weights = [edata['weight'] for _, _, edata in G.edges(data=True)]

    nx.draw(G, pos, with_labels=True, node_size=500, node_color="skyblue", edge_color="gray",
            width=weights, font_size=9)
    plt.title(titulo)
    plt.axis("off")
    plt.tight_layout()
    plt.show()

    # Preguntar dónde guardar imagen
    file_img = filedialog.asksaveasfilename(defaultextension=".png",
                                             filetypes=[("Imagen PNG", "*.png")],
                                             title="Guardar red como imagen")
    if file_img:
        plt.savefig(file_img)
        messagebox.showinfo("Imagen guardada", f"Imagen guardada en:\n{file_img}")

    # Preguntar dónde guardar archivo de red (.gexf para Gephi)
    file_net = filedialog.asksaveasfilename(defaultextension=".gexf",
                                            filetypes=[("Archivo GEXF", "*.gexf"), ("GraphML", "*.graphml")],
                                            title="Guardar red como archivo")
    if file_net:
        ext = os.path.splitext(file_net)[-1].lower()
        if ext == ".gexf":
            nx.write_gexf(G, file_net)
        elif ext == ".graphml":
            nx.write_graphml(G, file_net)
        else:
            messagebox.showwarning("Extensión no válida", "Solo se permite .gexf o .graphml")
            return
        messagebox.showinfo("Archivo de red guardado", f"Red guardada en:\n{file_net}")

# ========== Interfaz gráfica ==========
app = tk.Tk()
app.title("Visualizador de Redes Bibliométricas")
app.geometry("500x350")

btn_cargar = tk.Button(app, text="Cargar archivo CSV o Excel", command=cargar_archivo)
btn_cargar.pack(pady=10)

label_status = tk.Label(app, text="Ningún archivo cargado aún")
label_status.pack()

frame_form = tk.Frame(app)
frame_form.pack(pady=20)

tk.Label(frame_form, text="Columna Origen:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
tk.Label(frame_form, text="Columna Destino:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
tk.Label(frame_form, text="Palabras Clave:").grid(row=2, column=0, sticky="e", padx=5, pady=5)

combo_source = tk.ttk.Combobox(frame_form, width=30)
combo_source.grid(row=0, column=1)

combo_target = tk.ttk.Combobox(frame_form, width=30)
combo_target.grid(row=1, column=1)

combo_keywords = tk.ttk.Combobox(frame_form, width=30)
combo_keywords.grid(row=2, column=1)

btn_red_general = tk.Button(app, text="Mostrar Red General", command=crear_red_general)
btn_red_general.pack(pady=5)

btn_red_keywords = tk.Button(app, text="Mostrar Red de Palabras Clave", command=crear_red_palabras_clave)
btn_red_keywords.pack(pady=5)

app.mainloop()
