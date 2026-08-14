"""
Knowledge graph data structures for the payment-gateway domain.

Self-contained copy of Node/Edge/KnowledgeGraph (not imported from
kg.py) -- just the base structures, no ontology/rules/reasoner. Nodes
and edges are loaded from CSV: data/payments_nodes.csv (id,type,properties)
and data/payments_edges.csv (source,relation,target).
"""
import csv
import json


class Node:
    def __init__(self, entity_id: str, entity_type: str, properties: dict = None):
        self.id = entity_id           # Unique ID, e.g. "cust:1001"
        self.type = entity_type       # e.g. "Customer", "Merchant"
        self.properties = properties or {}

    def __repr__(self):
        return f"Node({self.id}, Type={self.type})"


class Edge:
    def __init__(self, source: str, relation_type: str, target: str):
        self.source = source          # source Node id
        self.relation = relation_type # e.g. "paid_by"
        self.target = target          # target Node id

    def __repr__(self):
        return f"Edge({self.source} --[{self.relation}]--> {self.target})"


class KnowledgeGraph:
    def __init__(self):
        self.nodes = {}    # Node ID -> Node object
        self.edges = []    # list of Edge objects

    def add_node(self, node: Node):
        self.nodes[node.id] = node

    def add_edge(self, edge: Edge):
        self.edges.append(edge)


def load_nodes_csv(kg: KnowledgeGraph, path: str):
    """Reads id,type,properties rows. properties is a JSON string, optional."""
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            properties = json.loads(row["properties"]) if row.get("properties") else {}
            kg.add_node(Node(row["id"], row["type"], properties))


def load_edges_csv(kg: KnowledgeGraph, path: str):
    """Reads source,relation,target rows."""
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            kg.add_edge(Edge(row["source"], row["relation"], row["target"]))


def load_from_csv(kg: KnowledgeGraph, nodes_path="data/payments_nodes.csv", edges_path="data/payments_edges.csv"):
    load_nodes_csv(kg, nodes_path)
    load_edges_csv(kg, edges_path)


NODE_COLORS = {
    "Customer": "lightgreen", "Merchant": "skyblue", "Category": "khaki",
    "Transaction": "lightsalmon", "Payout": "plum", "Policy": "lightgray",
}


def draw_graph(kg: KnowledgeGraph):
    """Renders the KnowledgeGraph with networkx/matplotlib -- used only for
    display, not for storing the graph (that's what nodes/edges are for).
    MultiDiGraph so two edges between the same pair (e.g. paid_by and
    refunded_to both txn->customer) don't overwrite each other."""
    import matplotlib.pyplot as plt
    import networkx as nx

    g = nx.MultiDiGraph()
    for node in kg.nodes.values():
        g.add_node(node.id, type=node.type)
    for edge in kg.edges:
        g.add_edge(edge.source, edge.target, key=edge.relation, relation=edge.relation)

    colors = [NODE_COLORS.get(g.nodes[n]["type"], "white") for n in g.nodes]

    pos = nx.spring_layout(g, seed=42)
    plt.figure(figsize=(11, 7))
    nx.draw(g, pos, with_labels=True, node_color=colors, node_size=2000, font_size=7, font_weight="bold")
    # NOTE: edge labels are keyed by (source, target), so where two relations
    # share the same pair only one label is drawn -- see the printed edge
    # list for the full picture.
    edge_labels = {(u, v): d["relation"] for u, v, d in g.edges(data=True)}
    nx.draw_networkx_edge_labels(g, pos, edge_labels=edge_labels, font_color="red", font_size=7)
    plt.show()


if __name__ == "__main__":
    kg = KnowledgeGraph()
    load_from_csv(kg)
    print(f"{len(kg.nodes)} nodes, {len(kg.edges)} edges")
    for edge in kg.edges:
        print(edge)
    draw_graph(kg)
