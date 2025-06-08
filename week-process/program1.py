import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

def load_data(csv_file):
    """Carga los datos desde un archivo CSV."""
    df = pd.read_csv(csv_file)
    return df

def create_network(df, source_col, target_col):
    """Crea una red basada en columnas de origen y destino."""
    G = nx.Graph()
    
    for _, row in df.iterrows():
        source = row[source_col]
        target = row[target_col]
        
        if G.has_edge(source, target):
            G[source][target]['weight'] += 1
        else:
            G.add_edge(source, target, weight=1)
    
    return G

def draw_network(G):
    """Dibuja la red usando networkx y matplotlib."""
    plt.figure(figsize=(10, 8))
    pos = nx.spring_layout(G, seed=42)  # Posicionamiento de nodos
    
    edges = G.edges(data=True)
    weights = [edata['weight'] for _, _, edata in edges]
    
    nx.draw(G, pos, with_labels=True, node_size=500, node_color="lightblue", 
            edge_color=weights, width=2.0, edge_cmap=plt.cm.Blues, font_size=10)
    
    plt.show()

# Ejemplo de uso
csv_file = "data.csv"  # Reemplázalo con tu archivo
source_col = "Autor1"
target_col = "Autor2"

df = load_data(csv_file)
G = create_network(df, source_col, target_col)
draw_network(G)
