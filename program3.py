import pandas as pd
import itertools
import networkx as nx
import matplotlib.pyplot as plt
from collections import Counter

# 1. Cargar archivo CSV
df = pd.read_csv("datos_bibliograficos.csv")

# 2. Procesar palabras clave
def procesar_keywords(texto):
    return [kw.strip().lower() for kw in str(texto).split(';') if kw.strip()]

df['keywords_list'] = df['keywords'].apply(procesar_keywords)

# 3. Contar ocurrencias individuales
ocurrencias = Counter()
for lista in df['keywords_list']:
    ocurrencias.update(lista)

# 4. Contar co-ocurrencias
coocurrencias = Counter()
for lista in df['keywords_list']:
    for par in itertools.combinations(sorted(set(lista)), 2):
        coocurrencias[par] += 1

# 5. Crear grafo
G = nx.Graph()
for keyword, count in ocurrencias.items():
    if count >= 2:  # solo incluir nodos con al menos 2 ocurrencias
        G.add_node(keyword, size=count)

for (kw1, kw2), weight in coocurrencias.items():
    if kw1 in G and kw2 in G and weight >= 2:
        G.add_edge(kw1, kw2, weight=weight)

# 6. Visualización mejorada
plt.figure(figsize=(14, 10))
pos = nx.spring_layout(G, k=0.5, seed=42)  # diseño estable

# Tamaño de nodos basado en ocurrencias
node_sizes = [G.nodes[n]['size'] * 300 for n in G.nodes]

# Grosor de aristas basado en co-ocurrencias
edge_weights = [G[u][v]['weight'] for u, v in G.edges]

# Dibujar nodos
nx.draw_networkx_nodes(G, pos, node_size=node_sizes, node_color='skyblue', alpha=0.9, edgecolors='black')

# Dibujar aristas
nx.draw_networkx_edges(G, pos, width=edge_weights, alpha=0.5)

# Dibujar etiquetas
nx.draw_networkx_labels(G, pos, font_size=10, font_family='sans-serif')

plt.title("Mapa de co-ocurrencia de palabras clave", fontsize=16)
plt.axis('off')
plt.tight_layout()
plt.show()
