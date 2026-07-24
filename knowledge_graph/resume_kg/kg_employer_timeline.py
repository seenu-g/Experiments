"""
Knowledge graph: Srinivasan, employer, and position, linked on a timeline.

Chain is Person -> Company -> Role: Person connects to Company (worked_at),
Company connects to Role/title (held_position). There is no direct edge
between Person and Role. Employers are ordered by the start year of their
earliest role and chained with a next_employer edge, laid out left-to-right
by time.

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

    # employers ordered by the start year of their earliest role
    ordered_employers = sorted(
        employers,
        key=lambda emp: min(r["start"] for r in roles if r["employer"] == emp),
    )
    prev_employer = None
    for employer in ordered_employers:
        if prev_employer:
            kg.add_edge(prev_employer, employer, relation="next_employer")
        prev_employer = employer

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


def timeline_positions(kg: nx.DiGraph):
    employers = [n for n, a in kg.nodes(data=True) if a.get("type") == "Company"]
    employers.sort(key=lambda n: min(
        kg.nodes[r]["start"] for r in kg.successors(n) if kg.nodes[r].get("type") == "Role"
    ))

    SPACING = 4
    ROLE_SPACING = 2
    pos = {PERSON: (len(employers) * SPACING / 2, 2)}

    for i, employer in enumerate(employers):
        pos[employer] = (i * SPACING, 0.5)
        role_nodes = [n for n in kg.successors(employer) if kg.nodes[n].get("type") == "Role"]
        for j, role in enumerate(role_nodes):
            pos[role] = (i * SPACING + j * ROLE_SPACING, -0.5)

    return pos


def visualize(kg: nx.DiGraph, out_dir: str):
    color_map = {"Person": "gold", "Company": "skyblue", "Role": "lightgreen"}
    colors = [color_map.get(kg.nodes[n].get("type"), "lightgrey") for n in kg.nodes]

    pos = timeline_positions(kg)
    plt.figure(figsize=(20, 6))

    timeline_edges = [(u, v) for u, v, d in kg.edges(data=True) if d.get("relation") == "next_employer"]
    other_edges = [(u, v) for u, v, d in kg.edges(data=True) if d.get("relation") != "next_employer"]

    nx.draw_networkx_nodes(kg, pos, node_color=colors, node_size=1400)
    nx.draw_networkx_labels(kg, pos, font_size=7)
    nx.draw_networkx_edges(kg, pos, edgelist=other_edges, edge_color="grey", arrows=True)
    nx.draw_networkx_edges(
        kg, pos, edgelist=timeline_edges, edge_color="crimson", width=2.5,
        arrows=True, arrowsize=20, connectionstyle="arc3,rad=0.15",
    )

    def employer_start(employer):
        return min(
            kg.nodes[r]["start"] for r in kg.successors(employer) if kg.nodes[r].get("type") == "Role"
        )

    timeline_labels = {(u, v): f"{employer_start(v)}→" for u, v in timeline_edges}
    nx.draw_networkx_edge_labels(
        kg, pos, edge_labels=timeline_labels, font_size=7, font_color="crimson",
    )

    plt.title("Knowledge Graph — Srinivasan and Employer (Timeline)")
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "kg_employer_timeline.png"), dpi=150)
    plt.show()


if __name__ == "__main__":
    out_dir = person_output_dir(PERSON)

    employers = build_employers()
    roles = build_roles(employers)
    print(f"Employers: {len(employers)}, Roles: {len(roles)}")
    for r in roles:
        print(f"  {r['start']}-{r['end']}: {r['title']} @ {r['employer']}")

    kg = build_graph(employers, roles)
    print(f"Graph: {kg.number_of_nodes()} nodes, {kg.number_of_edges()} edges")

    out_path = os.path.join(out_dir, "kg_employer_timeline.json")
    export_json(kg, out_path)
    print(f"Exported {out_path}")

    visualize(kg, out_dir)
