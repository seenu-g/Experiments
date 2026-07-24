"""
Loads node/edge data into a KnowledgeGraph from CSV or JSON. CSV is two files
(data/nodes.csv, data/edges.csv); JSON is a single {"nodes": [...], "edges":
[...]} file (data/graph.json). Both produce an identical graph.
"""
import csv
import json

from kg import Edge, KnowledgeGraph, Node


def load_nodes_csv(kg: KnowledgeGraph, path: str):
    """Reads id,type,properties rows and adds each as a Node. properties is a JSON string, optional."""
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            properties = json.loads(row["properties"]) if row.get("properties") else {}
            kg.add_node(Node(row["id"], row["type"], properties))


def load_edges_csv(kg: KnowledgeGraph, path: str):
    """Reads source,relation,target rows and adds each as an Edge."""
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            kg.add_edge(Edge(row["source"], row["relation"], row["target"]))


def load_from_csv(kg: KnowledgeGraph, nodes_path="data/nodes.csv", edges_path="data/edges.csv"):
    load_nodes_csv(kg, nodes_path)
    load_edges_csv(kg, edges_path)


def load_from_json(kg: KnowledgeGraph, path="data/graph.json"):
    """Reads a single {"nodes": [...], "edges": [...]} JSON file."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    for n in data["nodes"]:
        kg.add_node(Node(n["id"], n["type"], n.get("properties", {})))
    for e in data["edges"]:
        kg.add_edge(Edge(e["source"], e["relation"], e["target"]))
