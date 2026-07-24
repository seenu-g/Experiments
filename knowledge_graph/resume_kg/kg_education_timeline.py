"""
Knowledge graph: Srinivasan, education, and degree, linked on a timeline.

Chain is Person -> Institution -> Degree: Person connects to Institution
(education), Institution connects to Degree/title (awarded). There is no
direct edge between Person and Degree. Institutions are ordered by the
start year of their earliest degree and chained with a next_institution
edge, laid out left-to-right by time.

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

    # institutions ordered by the start year of their earliest degree
    ordered_institutions = sorted(
        institutions,
        key=lambda inst: min(e["start"] for e in education if e["institution"] == inst),
    )
    prev_institution = None
    for institution in ordered_institutions:
        if prev_institution:
            kg.add_edge(prev_institution, institution, relation="next_institution")
        prev_institution = institution

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


def timeline_positions(kg: nx.DiGraph):
    institutions = [n for n, a in kg.nodes(data=True) if a.get("type") == "School"]
    institutions.sort(key=lambda n: min(
        kg.nodes[d]["start"] for d in kg.successors(n) if kg.nodes[d].get("type") == "Degree"
    ))

    SPACING = 6
    DEGREE_SPACING = 2
    pos = {PERSON: (len(institutions) * SPACING / 2, 2)}

    for i, institution in enumerate(institutions):
        pos[institution] = (i * SPACING, 0.5)
        degree_nodes = [n for n in kg.successors(institution) if kg.nodes[n].get("type") == "Degree"]
        for j, degree in enumerate(degree_nodes):
            pos[degree] = (i * SPACING + j * DEGREE_SPACING, -0.5)

    return pos


def visualize(kg: nx.DiGraph, out_dir: str):
    color_map = {"Person": "gold", "School": "plum", "Degree": "orange"}
    colors = [color_map.get(kg.nodes[n].get("type"), "lightgrey") for n in kg.nodes]

    pos = timeline_positions(kg)
    plt.figure(figsize=(16, 6))

    timeline_edges = [(u, v) for u, v, d in kg.edges(data=True) if d.get("relation") == "next_institution"]
    other_edges = [(u, v) for u, v, d in kg.edges(data=True) if d.get("relation") != "next_institution"]

    nx.draw_networkx_nodes(kg, pos, node_color=colors, node_size=1400)
    nx.draw_networkx_labels(kg, pos, font_size=7)
    nx.draw_networkx_edges(kg, pos, edgelist=other_edges, edge_color="grey", arrows=True)
    nx.draw_networkx_edges(
        kg, pos, edgelist=timeline_edges, edge_color="crimson", width=2.5,
        arrows=True, arrowsize=20, connectionstyle="arc3,rad=0.15",
    )
    def institution_start(institution):
        return min(
            kg.nodes[d]["start"] for d in kg.successors(institution) if kg.nodes[d].get("type") == "Degree"
        )

    timeline_labels = {(u, v): f"{institution_start(v)}→" for u, v in timeline_edges}
    nx.draw_networkx_edge_labels(
        kg, pos, edge_labels=timeline_labels, font_size=7, font_color="crimson",
    )

    plt.title("Knowledge Graph — Srinivasan and Education (Timeline)")
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "kg_education_timeline.png"), dpi=150)
    plt.show()


if __name__ == "__main__":
    out_dir = person_output_dir(PERSON)

    institutions = build_institutions()
    education = build_education(institutions)
    print(f"Institutions: {len(institutions)}, Degrees: {len(education)}")
    for e in education:
        print(f"  {e['start']}-{e['end']}: {e['degree']} @ {e['institution']}")

    kg = build_graph(institutions, education)
    print(f"Graph: {kg.number_of_nodes()} nodes, {kg.number_of_edges()} edges")

    out_path = os.path.join(out_dir, "kg_education_timeline.json")
    export_json(kg, out_path)
    print(f"Exported {out_path}")

    visualize(kg, out_dir)
