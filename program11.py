import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import community as community_louvain  # Asegúrate de tener instalado python-louvain

def cargar_archivo():
    filepath = filedialog.askopenfilename(
        filetypes=[("Archivos CSV", "*.csv"), ("Archivos Excel", "*.xlsx *.xls")]
    )
    if not filepath:
        return

    try:
        if filepath.endswith((".xlsx", ".xls")):
            excel_file = pd.ExcelFile(filepath)
            app.hojas = excel_file.sheet_names
            combo_hojas['values'] = app.hojas
            combo_hojas.set(app.hojas[0])
            app.filepath = filepath
            app.excel_file = excel_file
            label_estado.config(text=f"Archivo Excel cargado: {filepath.split('/')[-1]}")
            cargar_columnas_excel()
        else:
            # Para CSV usamos fila y columna inicial para recortar el DataFrame luego
            df = pd.read_csv(filepath, header=None)
            app.df_raw = df
            app.filepath = filepath
            label_estado.config(text=f"Archivo CSV cargado: {filepath.split('/')[-1]}")
            combo_hojas['values'] = []
            combo_hojas.set("")
            app.hojas = []
            cargar_columnas_desde_df_csv()
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo cargar el archivo:\n{e}")

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
        app.df = pd.DataFrame(df.values)
        cargar_columnas_desde_df()
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
        # Primer columna ahora es encabezados
        campos = list(app.df_raw.iloc[:, 0].dropna().astype(str))
        combo_source['values'] = campos
        combo_target['values'] = campos
        combo_keywords['values'] = campos
        combo_source.set('')
        combo_target.set('')
        combo_keywords.set('')
        app.df = app.df_raw
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
    dibujar_red(G)

def generar_red_keywords():
    if not hasattr(app, "df"):
        messagebox.showwarning("Aviso", "Primero carga un archivo válido.")
        return
    col = combo_keywords.get()
    if not col:
        messagebox.showwarning("Aviso", "Selecciona la columna de palabras clave.")
        return

    G = nx.Graph()

    if app.tipo_encabezado.get() == "Fila":
        for _, row in app.df.iterrows():
            try:
                raw_text = str(row[col])

                # Detectar automáticamente el delimitador
                if ";" in raw_text:
                    keywords = raw_text.split(";")
                elif "," in raw_text:
                    keywords = raw_text.split(",")
                elif "." in raw_text:
                    keywords = raw_text.split(".")
                else:
                    keywords = [raw_text]  # solo una palabra clave

                # Eliminar espacios al inicio/final y cadenas vacías
                keywords = [kw.strip() for kw in keywords if kw.strip()]
                # Eliminar espacios al inicio/final y cadenas vacías
                keywords = [kw.strip() for kw in keywords if kw.strip()]
                for kw in keywords:
                    G.add_node(kw)  # Asegura que se agregue cada keyword como nodo

                for i in range(len(keywords)):
                    for j in range(i + 1, len(keywords)):
                        k1, k2 = keywords[i], keywords[j]
                        if G.has_edge(k1, k2):
                            G[k1][k2]["weight"] += 1
                        else:
                            G.add_edge(k1, k2, weight=1)

            except Exception:
                continue
    else:
        messagebox.showinfo("Info", "Generación de red de keywords para encabezado en columna no implementada aún.")
        return

    app.grafo_keywords = G
    dibujar_red(G)

def dibujar_red(G):
    if hasattr(app, "canvas_network") and app.canvas_network:
        app.canvas_network.get_tk_widget().destroy()
        app.scrollable_canvas.destroy()

    fig, ax = plt.subplots(figsize=(8,6))
    pos = nx.spring_layout(G, seed=42)
    nx.draw_networkx(G, pos=pos, ax=ax, with_labels=True, node_size=300, font_size=9)
    ax.axis("off")

    canvas_frame = tk.Frame(frame_output, bg="white")
    canvas_frame.pack(fill="both", expand=True)
    app.scrollable_canvas = canvas_frame

    canvas_widget = tk.Canvas(canvas_frame, bg="white")
    canvas_widget.pack(fill="both", expand=True)

    fig_canvas = FigureCanvasTkAgg(fig, master=canvas_widget)
    fig_canvas.draw()

    widget = fig_canvas.get_tk_widget()
    widget.pack(fill="both", expand=True)

    app.canvas_network = fig_canvas
    plt.close(fig)

# UI Setup

app = tk.Tk()
app.title("Visualizador de Redes Bibliométricas")
app.geometry("1200x700")
app.configure(bg="#e0f7fa")

frame_contenedor_horizontal = tk.Frame(app, bg="#f0f4f8")
frame_contenedor_horizontal.pack(fill="both", expand=True)

frame_controles = tk.Frame(frame_contenedor_horizontal, bg="#f0f4f8", width=320)
frame_controles.pack(side="left", fill="y", padx=10, pady=10)

frame_output = tk.Frame(frame_contenedor_horizontal, bg="white")
frame_output.pack(side="right", fill="both", expand=True, padx=10, pady=10)

tk.Button(frame_controles, text="📂 Cargar archivo CSV/XLSX", command=cargar_archivo,
          font=("Segoe UI", 11, "bold"), bg="#8ecae6", fg="white", padx=10, pady=6).pack(pady=(5,5))

label_estado = tk.Label(frame_controles, text="", font=("Segoe UI", 10), fg="green", bg="#f0f4f8")
label_estado.pack()

tk.Label(frame_controles, text="Selecciona hoja (solo Excel):", font=("Arial", 10), bg="#f0f4f8").pack(anchor="w", padx=5, pady=(15,0))
combo_hojas = ttk.Combobox(frame_controles, width=28)
combo_hojas.pack(padx=5, pady=5)
combo_hojas.bind("<<ComboboxSelected>>", cargar_columnas_excel)

# Nuevos campos para fila y columna inicial
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
app.tipo_encabezado = tk.StringVar(value="Fila")
radio_fila = tk.Radiobutton(frame_controles, text="Fila", variable=app.tipo_encabezado, value="Fila", bg="#f0f4f8", command=cargar_columnas_excel)
radio_columna = tk.Radiobutton(frame_controles, text="Columna", variable=app.tipo_encabezado, value="Columna", bg="#f0f4f8", command=cargar_columnas_excel)
radio_fila.pack(anchor="w", padx=10)
radio_columna.pack(anchor="w", padx=10)

tk.Label(frame_controles, text="Columna origen:", font=("Arial", 10), bg="#f0f4f8").pack(anchor="w", padx=5, pady=(15,0))
combo_source = ttk.Combobox(frame_controles, width=35)
combo_source.pack(padx=5, pady=5)

tk.Label(frame_controles, text="Columna destino:", font=("Arial", 10), bg="#f0f4f8").pack(anchor="w", padx=5)
combo_target = ttk.Combobox(frame_controles, width=35)
combo_target.pack(padx=5, pady=5)

tk.Label(frame_controles, text="Columna palabras clave:", font=("Arial", 10), bg="#f0f4f8").pack(anchor="w", padx=5, pady=(15,0))
combo_keywords = ttk.Combobox(frame_controles, width=35)
combo_keywords.pack(padx=5, pady=5)

tk.Button(frame_controles, text="🌐 Generar red general", command=generar_red_general,
          font=("Segoe UI", 10, "bold"), bg="#219ebc", fg="white").pack(pady=(20,5))

tk.Button(frame_controles, text="🔑 Generar red de keywords", command=generar_red_keywords,
          font=("Segoe UI", 10, "bold"), bg="#023047", fg="white").pack(pady=5)

# Variables iniciales
app.df = None
app.df_raw = None
app.hojas = []
app.filepath = None
app.excel_file = None
app.canvas_network = None
app.scrollable_canvas = None

app.mainloop()
