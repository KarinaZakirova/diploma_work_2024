import networkx as nx
import pandas as pd
import csv
import matplotlib.pyplot as plt
from os import listdir

def iter_csv_graphs(graph_dir="graph/", plot_dir="plots/"):
    for path in listdir(graph_dir):
        print(path)
        print("=========")
        if path in listdir(plot_dir):
            continue
        with open(graph_dir + path, encoding='UTF-8') as f:
            triplets = list(csv.reader(f))
            if not triplets:
                continue
            yield path, triplets

def get_edge_labels(triplets):
    return {(subj, obj): predicate for subj, predicate, obj in triplets}

def draw_graphs():
    for filename, triplets in iter_csv_graphs():
        subj, predicate, obj = zip(*triplets)

        kg_df = pd.DataFrame({'source':subj, 'target':obj, 'edge':predicate})

        print(kg_df)

        # Создание ориентированного графа из кадра данных
        G=nx.from_pandas_edgelist(kg_df, "source", "target",
                                edge_attr=True, create_using=nx.MultiDiGraph())

        plt.figure(figsize=(12,12))

        pos = nx.spring_layout(G)
        nx.draw(G, with_labels=True, node_color='skyblue', edge_cmap=plt.cm.Blues, pos = pos)
        nx.draw_networkx_edge_labels(
            G, pos,
            edge_labels=get_edge_labels(triplets),
            font_color='indigo'
        )
        plt.savefig(f"plots/{filename}.png")


if __name__ == "__main__":
    draw_graphs()
