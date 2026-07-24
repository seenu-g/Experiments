"""
Example: build a knowledge graph from resume.pdf, with Experience (employer +
position only) and Education (degree + school only) kept as two separate,
date-ordered clusters.

Role/company/date headers are too irregular for one robust regex (mixed
dashes, pipes, parenthetical company names, trailing "| Reported to CEO"
asides), so they're listed here explicitly in the order they appear in the
resume (values read straight out of the PDF text, just not regex-matched).

Pipeline:
  1. Sort each cluster by start year and chain consecutive items with a
     next_role / next_degree edge to represent the timeline.
  2. Export to JSON and draw a two-band visualization (experience row on top,
     education row on bottom).
"""
import json

import matplotlib.pyplot as plt
import networkx as nx

PERSON = "Srinivasan G"

# (title, company, start_year, end_year)
ROLE_HEADERS = [
    ("Software Engineer", "Tata InfoTech Limited (TCS)", 1998, 2000),
    ("Technical Leader, MTS-2", "Hughes Software", 2000, 2006),
    ("Technical Project Manager", "Protean Software (Harman)", 2006, 2011),
    ("Head of Product Development", "MobiSir | ArthaVidhya", 2011, 2015),
    ("Development Team Lead", "Meridium (GE Digital)", 2015, 2016),
    ("Director", "Accion Labs", 2016, 2019),
    ("Senior Architect – Global Business", "ESDS Solutions", 2019, 2020),
    ("Senior Manager – Technology", "Clarivate", 2021, 2022),
    ("Platform Development - SVP", "Vayana Network", 2022, 2023),
    ("Senior Engineering Manager", "ACV Auctions", 2024, 2026),
]

# (degree, school, start_year, end_year)
EDUCATION_HEADERS = [
    ("Bachelor of Science in Mathematics", "University of Madras", 1993, 1996),
    ("Master of Science in Mathematics (Theoretical Computer Science)",
     "College of Engineering, Guindy", 1996, 1998),
    ('Professional Development: "Extensive Vision AI"', "The School of AI", 2020, 2020),
]

def build_roles():
    roles = [
        {"title": title, "company": company, "start": start, "end": end}
        for title, company, start, end in ROLE_HEADERS
    ]
    return sorted(roles, key=lambda r: r["start"])


def build_education():
    education = [
        {"degree": d, "school": s, "start": start, "end": end}
        for d, s, start, end in EDUCATION_HEADERS
    ]
    return sorted(education, key=lambda e: e["start"])


def build_graph(roles, education) -> nx.DiGraph:
    kg = nx.DiGraph()
    kg.add_node(PERSON, type="Person")

    prev_role_node = None
    for role in roles:
        role_node = f"{role['title']} @ {role['company']}"
        kg.add_node(role["company"], type="Company", cluster="experience")
        kg.add_node(role_node, type="Role", cluster="experience",
                    start=role["start"], end=role["end"])
        kg.add_edge(PERSON, role_node, relation="held_role")
        kg.add_edge(role_node, role["company"], relation="worked_at")
        if prev_role_node:
            kg.add_edge(prev_role_node, role_node, relation="next_role")
        prev_role_node = role_node

    prev_degree_node = None
    for edu in education:
        degree_node = f"{edu['degree']} @ {edu['school']}"
        kg.add_node(edu["school"], type="School", cluster="education")
        kg.add_node(degree_node, type="Degree", cluster="education",
                    start=edu["start"], end=edu["end"])
        kg.add_edge(PERSON, degree_node, relation="earned")
        kg.add_edge(degree_node, edu["school"], relation="from")
        if prev_degree_node:
            kg.add_edge(prev_degree_node, degree_node, relation="next_degree")
        prev_degree_node = degree_node

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


def layered_positions(kg: nx.DiGraph):
    """Lay experience nodes in a top band, education nodes in a bottom band."""
    exp_roles = [n for n, a in kg.nodes(data=True) if a.get("type") == "Role"]
    exp_roles.sort(key=lambda n: kg.nodes[n]["start"])
    edu_degrees = [n for n, a in kg.nodes(data=True) if a.get("type") == "Degree"]
    edu_degrees.sort(key=lambda n: kg.nodes[n]["start"])

    ROLE_SPACING = 4
    pos = {PERSON: (len(exp_roles) * ROLE_SPACING / 2, 3)}

    for i, role in enumerate(exp_roles):
        pos[role] = (i * ROLE_SPACING, 1.5)
        for succ in kg.successors(role):
            if kg.nodes[succ].get("type") == "Company":
                pos[succ] = (i * ROLE_SPACING, 2.2)

    EDU_SPACING = 6
    for i, degree in enumerate(edu_degrees):
        pos[degree] = (i * EDU_SPACING, -1)
        for succ in kg.successors(degree):
            if kg.nodes[succ].get("type") == "School":
                pos[succ] = (i * EDU_SPACING, -2.2)

    # anything unpositioned (shouldn't normally happen) gets a fallback layout
    missing = [n for n in kg.nodes if n not in pos]
    if missing:
        fallback = nx.spring_layout(kg.subgraph(missing), seed=1)
        pos.update(fallback)
    return pos


def visualize(kg: nx.DiGraph):
    color_map = {
        "Person": "gold",
        "Company": "skyblue",
        "Role": "lightgreen",
        "School": "plum",
        "Degree": "orange",
    }
    colors = [color_map.get(kg.nodes[n].get("type"), "lightgrey") for n in kg.nodes]

    pos = layered_positions(kg)
    plt.figure(figsize=(20, 8))
    nx.draw(
        kg, pos, with_labels=True, node_color=colors, node_size=1400,
        font_size=7, edge_color="grey", arrows=True,
    )
    plt.title("Resume Knowledge Graph — Experience (top) / Education (bottom)")
    plt.tight_layout()
    plt.savefig("resume_kg.png", dpi=150)
    plt.show()


if __name__ == "__main__":
    roles = build_roles()
    education = build_education()

    print(f"Roles: {len(roles)}, Education: {len(education)}")
    for r in roles:
        print(f"  {r['start']}-{r['end']}: {r['title']} @ {r['company']}")
    for e in education:
        print(f"  {e['start']}-{e['end']}: {e['degree']} @ {e['school']}")

    kg = build_graph(roles, education)
    print(f"\nGraph: {kg.number_of_nodes()} nodes, {kg.number_of_edges()} edges")

    export_json(kg, "resume_kg.json")
    print("Exported resume_kg.json")

    visualize(kg)
