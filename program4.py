import streamlit as st
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import io
#import warnings

#warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

st.title("Visualizador de Redes Bibliométricas")

# 1. Cargar archivo CSV o Excel
uploaded_file = st.file_uploader("Sube un archivo CSV o Excel", type=["csv", "xlsx"])

if uploaded_file:
    # Detectar tipo de archivo
    filename = uploaded_file.name
    if filename.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    elif filename.endswith(".xlsx"):
        df = pd.read_excel(uploaded_file)
    else:
        st.error("Formato de archivo no soportado")
        st.stop()

    st.success(f"¡Archivo '{filename}' cargado correctamente!")

    st.subheader("Vista previa del archivo")
    st.dataframe(df.head())

    columnas = df.columns.tolist()

    # 2. Selección de columnas para red general
    st.subheader("Red General (Origen -> Destino)")
    source_col = st.selectbox("Selecciona la columna de origen", columnas)
    target_col = st.selectbox("Selecciona la columna de destino", columnas)

    # 3. Selección de columna para red de palabras clave
    st.subheader("Red de Palabras Clave")
    keywords_col = st.selectbox("Selecciona la columna de palabras clave", columnas)

    def create_network(df, source_col, target_col):
        G = nx.Graph()
        for _, row in df.iterrows():
            source = row[source_col]
            target = row[target_col]
            if pd.notna(source) and pd.notna(target):
                if G.has_edge(source, target):
                    G[source][target]['weight'] += 1
                else:
                    G.add_edge(source, target, weight=1)
        return G

    def create_keyword_network(df, keywords_col):
        G = nx.Graph()
        for _, row in df.iterrows():
            if pd.notna(row[keywords_col]):
                keywords = [kw.strip().lower() for kw in str(row[keywords_col]).split(';') if kw.strip()]
                for i in range(len(keywords)):
                    for j in range(i + 1, len(keywords)):
                        k1, k2 = keywords[i], keywords[j]
                        if G.has_edge(k1, k2):
                            G[k1][k2]['weight'] += 1
                        else:
                            G.add_edge(k1, k2, weight=1)
        return G

    def draw_network(G, title="Red"):
        st.subheader(title)
        fig, ax = plt.subplots(figsize=(10, 8))
        pos = nx.spring_layout(G, seed=42)
        weights = [edata['weight'] for _, _, edata in G.edges(data=True)]
        nx.draw(G, pos, with_labels=True, node_size=500, node_color="skyblue", edge_color="gray",
                width=weights, font_size=9, ax=ax)
        st.pyplot(fig)

    # 4. Generar y mostrar redes
    G1 = create_network(df, source_col, target_col)
    G2 = create_keyword_network(df, keywords_col)

    draw_network(G1, "Red General")
    draw_network(G2, "Red de Palabras Clave (Co-ocurrencias)")
