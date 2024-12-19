import pandas as pd
import os
import ast
import networkx as nx
import plotly.graph_objects as go
from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)


# Dosya yolunu belirleme
file_path = os.path.join(os.getcwd(), "PROLAB 3 - GÜNCEL DATASET.xlsx")
data = pd.read_excel(file_path, engine="openpyxl")

# Yazar isimlerini normalize etmek için bir fonksiyon
def normalize_name(name):
    return name.strip().replace(".", "").replace(",", "").lower()

# Ana yazarlar ve coauthors için sözlükler
node_papers = {}  # Yazarların yer aldığı makaleleri toplar
edge_weights = {}  # İki yazar arasındaki ortak makale sayısını tutar

# Veriyi döngü ile işleme
for _, row in data.iterrows():
    if pd.notna(row['author_name']):  # Ana yazar
        main_author = normalize_name(row['author_name'])
        paper_title = row['paper_title']

        if main_author not in node_papers:
            node_papers[main_author] = set()
        node_papers[main_author].add(paper_title)

        if pd.notna(row['coauthors']):  # Coauthors
            try:
                coauthors = ast.literal_eval(row['coauthors'])
                coauthors = [normalize_name(author) for author in coauthors]

                for coauthor in coauthors:
                    if coauthor not in node_papers:
                        node_papers[coauthor] = set()
                    node_papers[coauthor].add(paper_title)

                    # Kenar ağırlıklarını güncelle
                    edge = tuple(sorted((main_author, coauthor)))
                    edge_weights[edge] = edge_weights.get(edge, 0) + 1
            except Exception as e:
                print(f"Hata: {e} - Veri: {row['coauthors']}")

# Ortalama makale sayısını hesaplama
avg_papers = sum(len(papers) for papers in node_papers.values()) / len(node_papers)

# NetworkX grafı oluşturma
G = nx.Graph()

# Düğümleri ekleme
for author, papers in node_papers.items():
    paper_count = len(papers)
    G.add_node(author, size=paper_count, color="blue" if paper_count >= avg_papers * 1.2 else "lightblue")

# Kenarları ekleme
for (source, target), weight in edge_weights.items():
    G.add_edge(source, target, weight=weight)

# Düğüm ve kenar verilerini görselleştirme için hazırlama
pos = nx.spring_layout(G, seed=42)  # Yayılma düzeni
node_x, node_y, node_sizes, node_colors, node_text = [], [], [], [], []

for node in G.nodes():
    x, y = pos[node]
    node_x.append(x)
    node_y.append(y)
    node_sizes.append(G.nodes[node]["size"] * 10)  # Düğüm boyutları
    node_colors.append(G.nodes[node]["color"])  # Düğüm renkleri
    node_text.append(f"{node}<br>Makale Sayısı: {G.nodes[node]['size']}")

edge_x, edge_y, edge_weights = [], [], []

for edge in G.edges(data=True):
    x0, y0 = pos[edge[0]]
    x1, y1 = pos[edge[1]]
    edge_x.extend([x0, x1, None])
    edge_y.extend([y0, y1, None])
    edge_weights.append(edge[2]["weight"])

# Kenarların çizimi
edge_trace = go.Scatter(
    x=edge_x,
    y=edge_y,
    line=dict(width=1, color="white"),
    hoverinfo="none",
    mode="lines",
)

# Düğümlerin çizimi
node_trace = go.Scatter(
    x=node_x,
    y=node_y,
    mode="markers",
    marker=dict(
        size=node_sizes,
        color=node_colors,
        line_width=2,
    ),
    text=node_text,
    hoverinfo="text",
)

# Grafı oluşturma
fig = go.Figure(
    data=[edge_trace, node_trace],
    layout=go.Layout(
        title="Yazarlar Arası Ortak Çalışma Grafı",
        titlefont_size=16,
        showlegend=False,
        hovermode="closest",
        margin=dict(b=0, l=0, r=0, t=40),
        xaxis=dict(showgrid=False, zeroline=False),
        yaxis=dict(showgrid=False, zeroline=False),
    ),
)

# Görüntüleme
fig.show()
