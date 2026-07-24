"""
Knowledge graph: Srinivasan, employer, and position.

Chain is Person -> Company -> Role: Person connects to Company (worked_at),
Company connects to Role/title (held_position). There is no direct edge
between Person and Role.

Resume data (person, employers, roles) is loaded from
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


def build_employers():
    return list(_resume["employers"])


def build_roles(employers):
    roles = _resume["roles"]
    unknown_employers = {r["employer"] for r in roles} - set(employers)
    if unknown_employers:
        raise ValueError(f"Role references unknown employer(s): {unknown_employers}")
    return sorted(roles, key=lambda r: r["start"])


def build_graph(employers, roles) -> nx.DiGraph:
    kg = nx.DiGraph()
    kg.add_node(PERSON, type="Person")

    for employer in employers:
        kg.add_node(employer, type="Company")
        kg.add_edge(PERSON, employer, relation="worked_at")

    for role in roles:
        role_node = f"{role['title']}"
        kg.add_node(role_node, type="Role", start=role["start"], end=role["end"])
        kg.add_edge(role["employer"], role_node, relation="held_position")

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


def linear_positions(kg: nx.DiGraph, employers):
    """One row per employer: Person | Employer | Role(s), left to right."""
    ROW_SPACING = 2
    ROLE_SPACING = 2.5

    pos = {}
    for row, employer in enumerate(employers):
        y = -row * ROW_SPACING
        pos[employer] = (2, y)
        role_nodes = [n for n in kg.successors(employer) if kg.nodes[n].get("type") == "Role"]
        for i, role_node in enumerate(role_nodes):
            pos[role_node] = (4 + i * ROLE_SPACING, y)

    pos[PERSON] = (0, -((len(employers) - 1) * ROW_SPACING) / 2)
    return pos


def visualize(kg: nx.DiGraph, employers, out_dir: str):
    color_map = {"Person": "gold", "Company": "skyblue", "Role": "lightgreen"}
    colors = [color_map.get(kg.nodes[n].get("type"), "lightgrey") for n in kg.nodes]

    pos = linear_positions(kg, employers)
    plt.figure(figsize=(16, 12))
    nx.draw(
        kg, pos, with_labels=True, node_color=colors, node_size=1400,
        font_size=7, edge_color="grey", arrows=True,
    )
    plt.title("Knowledge Graph — Srinivasan and Employer")
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "kg_employer.png"), dpi=150)
    plt.show()


if __name__ == "__main__":
    out_dir = person_output_dir(PERSON)

    employers = build_employers()
    roles = build_roles(employers)
    print(f"Employers: {len(employers)}, Roles: {len(roles)}")

    kg = build_graph(employers, roles)
    print(f"Graph: {kg.number_of_nodes()} nodes, {kg.number_of_edges()} edges")

    out_path = os.path.join(out_dir, "kg_employer.json")
    export_json(kg, out_path)
    print(f"Exported {out_path}")

    visualize(kg, employers, out_dir)
