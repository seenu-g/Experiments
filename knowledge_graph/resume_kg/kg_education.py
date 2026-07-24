"""
Knowledge graph: Srinivasan, education, and degree.

Chain is Person -> Institution -> Degree: Person connects to Institution
(education), Institution connects to Degree/title (awarded). There is no
direct edge between Person and Degree.

Resume data (person, institutions, degrees) is loaded from
fixtures/srinivasan_resume.json via resume_data.load_resume() instead of
being hardcoded here.
"""
import json
import os

import matplotlib.pyplot as plt
import networkx as nx

from resume_data import load_resume, person_output_dir

_resume = load_resume()
PERSON = _resume["person"]


def build_institutions():
    return list(_resume["institutions"])


def build_education(institutions):
    education = _resume["degrees"]
    unknown_institutions = {e["institution"] for e in education} - set(institutions)
    if unknown_institutions:
        raise ValueError(f"Degree references unknown institution(s): {unknown_institutions}")
    return sorted(education, key=lambda e: e["start"])


def build_graph(institutions, education) -> nx.DiGraph:
    kg = nx.DiGraph()
    kg.add_node(PERSON, type="Person")

    for institution in institutions:
        kg.add_node(institution, type="School")
        kg.add_edge(PERSON, institution, relation="education")

    for edu in education:
        degree_node = f"{edu['degree']}"
        kg.add_node(degree_node, type="Degree", start=edu["start"], end=edu["end"])
        kg.add_edge(edu["institution"], degree_node, relation="awarded")

    return kg


def export_json(kg: nx.DiGraph, path: str):
    data = {
        "nodes": [{"id": n, **attrs} for n, attrs in kg.nodes(data=True)],
        "edges": [
            {"source": u, "target": v, **attrs} for u, v, attrs in kg.edges(data=True)
        ],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def linear_positions(kg: nx.DiGraph, institutions):
    """One row per institution: Person | Institution | Degree(s), left to right."""
    ROW_SPACING = 2
    DEGREE_SPACING = 3.5

    pos = {}
    for row, institution in enumerate(institutions):
        y = -row * ROW_SPACING
        pos[institution] = (2, y)
        degree_nodes = [n for n in kg.successors(institution) if kg.nodes[n].get("type") == "Degree"]
        for i, degree_node in enumerate(degree_nodes):
            pos[degree_node] = (4 + i * DEGREE_SPACING, y)

    pos[PERSON] = (0, -((len(institutions) - 1) * ROW_SPACING) / 2)
    return pos


def visualize(kg: nx.DiGraph, institutions, out_dir: str):
    color_map = {"Person": "gold", "School": "plum", "Degree": "orange"}
    colors = [color_map.get(kg.nodes[n].get("type"), "lightgrey") for n in kg.nodes]

    pos = linear_positions(kg, institutions)
    plt.figure(figsize=(14, 8))
    nx.draw(
        kg, pos, with_labels=True, node_color=colors, node_size=1400,
        font_size=7, edge_color="grey", arrows=True,
    )
    plt.title("Knowledge Graph — Srinivasan and Education")
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "kg_education.png"), dpi=150)
    plt.show()


if __name__ == "__main__":
    out_dir = person_output_dir(PERSON)

    institutions = build_institutions()
    education = build_education(institutions)
    print(f"Institutions: {len(institutions)}, Degrees: {len(education)}")

    kg = build_graph(institutions, education)
    print(f"Graph: {kg.number_of_nodes()} nodes, {kg.number_of_edges()} edges")

    out_path = os.path.join(out_dir, "kg_education.json")
    export_json(kg, out_path)
    print(f"Exported {out_path}")

    visualize(kg, institutions, out_dir)
