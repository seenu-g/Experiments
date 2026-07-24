import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Represents an Entity or a Concept
class Node:
    def __init__(self, entity_id: str, entity_type: str, properties: dict = None):
        self.id = entity_id          # Unique URI or ID
        self.type = entity_type      # e.g., "Person", "Company"
        self.properties = properties or {}  # Key-value pairs (e.g., {"age": 30})

    def __repr__(self):
        return f"Node({self.id}, Type={self.type})"

#Represents a Directed, Typed Semantic Relation between two Nodes
class Edge:
    def __init__(self, source: str, relation_type: str, target: str):
        self.source = source         # Subject
        self.relation = relation_type # Predicate
        self.target = target         # Object
        self.properties = {}         # Key-value pairs (e.g., {"since": 2012})

    def __repr__(self):
        return f"Edge({self.source} --[{self.relation}]--> {self.target})"


class KnowledgeGraph:
    def __init__(self):
        self.nodes = {}       # Map: Node ID -> Node object
        self.edges = []       # List of all Edge triples
        self.ontology = {}    # Map: Relation -> Allowed (Source_Type, Target_Type)
        self.rules = []       # List of structural inference functions

    # "ontology rule" is a schema constraint: it says a givenrelation is only
    # allowed to connect a specific source-entity-type to a specific target-entity-type.
    # Defines the allowed semantic schema (domain and range restrictions)."""
    def add_ontology_rule(self, relation: str, allowed_source_type: str, allowed_target_type: str):
        self.ontology[relation] = (allowed_source_type, allowed_target_type)

    # inference rule is a function that looks at the facts (edges) already 
    # in the graph and derives new facts that were never explicitly added 
    # the automated-reasoning part of this toy engine.
    """Registers a logical inference rule for reasoning."""
    def add_inference_rule(self, rule_function):
        self.rules.append(rule_function)

    def add_node(self, node: Node):
        self.nodes[node.id] = node

    """Validates schema definitions and inserts a directional fact."""
    def add_edge(self, edge: Edge):
        
        # 1. Structural Validation
        if edge.source not in self.nodes or edge.target not in self.nodes:
            raise ValueError(f"Aborting: Source or Target node does not exist in graph.")
        
        # 2. Semantic/Ontology Validation
        src_type = self.nodes[edge.source].type
        tgt_type = self.nodes[edge.target].type
        
        if edge.relation in self.ontology:
            allowed_src, allowed_tgt = self.ontology[edge.relation]
            if src_type != allowed_src or tgt_type != allowed_tgt:
                raise TypeError(
                    f"Ontology Violation! Relation '{edge.relation}' connects "
                    f"{src_type}->{tgt_type}. Expected {allowed_src}->{allowed_tgt}."
                )
        
        self.edges.append(edge)

    """Executes registered rules to automatically deduce new implicit facts."""
    def run_reasoner(self):
    
        print("\n--- Running Logical Reasoning Engine ---")
        new_edges_deduced = True
        
        while new_edges_deduced:
            new_edges_deduced = False
            for rule in self.rules:
                deduced_edges = rule(self)
                for e in deduced_edges:
                    # Check if this exact statement already exists
                    exists = any(x.source == e.source and x.relation == e.relation and x.target == e.target for x in self.edges)
                    if not exists:
                        print(f"💡 Implicit Fact Deduced: {e.source} --[{e.relation}]--> {e.target}")
                        self.add_edge(e)
                        new_edges_deduced = True # Loop again to capture downstream deductions

    #   Every fact in the graph is a triple: (source, predicate/relation,
    #   object) — e.g. ("co:google", "subsidiary_of", "co:alphabet").
    #   query_triples does a linear scan over all edges and keeps the ones
    #   matching whichever of s (subject), p (predicate), o (object) you
    #   specify — any argument left as None acts as a wildcard.
    #   graph's basic pattern-matching search — a simplified version of a SPARQL/RDF triple query.
    """A basic triple-matching query engine (similar to SPARQL pattern matching)."""
    def query_triples(self, s=None, p=None, o=None):
        
        results = []
        for edge in self.edges:
            if s and edge.source != s: continue
            if p and edge.relation != p: continue
            if o and edge.target != o: continue
            results.append(edge)
        return results

# transitivity_rule (kg.py:91-102) is one concrete inference rule: it encodes "subsidiary-of is transitive" 
# If A is a subsidiary of B, and B is a subsidiary of C, then A is a subsidiary of C."""
def transitivity_rule(kg: KnowledgeGraph): 
    inferred = []
    subsidiaries = kg.query_triples(p="subsidiary_of")
        
    for e1 in subsidiaries:
        parent_company = e1.target
        # Find if the parent company itself has a parent company
        grandparents = kg.query_triples(s=parent_company, p="subsidiary_of")
        for e2 in grandparents:
            ultimate_owner = e2.target
            inferred.append(Edge(source=e1.source, relation_type="subsidiary_of", target=ultimate_owner))
    return inferred

# this is also a inference rule
# If Company A is headquartered in City X, and City X is located in Country Y, then A operates in Country Y.
def location_inheritance_rule(kg: KnowledgeGraph):
    
    inferred = []
    headquarters = kg.query_triples(p="headquartered_in")
        
    for hq in headquarters:
        city = hq.target
        contained_locations = kg.query_triples(s=city, p="located_in")
        for loc in contained_locations:
            country = loc.target
            inferred.append(Edge(source=hq.source, relation_type="operates_in", target=country))
    return inferred

if __name__ == "__main__":
    from load_kg_data import load_from_csv, load_from_json

    kg = KnowledgeGraph()

    # 2. Declare Ontology (Schema)
    kg.add_ontology_rule("headquartered_in", "Company", "City")
    kg.add_ontology_rule("located_in",       "City",    "Country")
    kg.add_ontology_rule("subsidiary_of",    "Company", "Company")
    kg.add_ontology_rule("operates_in",      "Company", "Country")

    # 3. Register Inference Rules
    kg.add_inference_rule(transitivity_rule)
    kg.add_inference_rule(location_inheritance_rule)

    # 4. Insert Entities (Nodes) and Explicit Facts (Edges) — default: CSV.
    # Swap to load_from_json(kg) to load data/graph.json instead.
    load_from_csv(kg)

    # --- TEST SCHEMA CONSTRAINT VIOLATION ---
    try:
        # A City cannot be a subsidiary of a Person (Ontology rule expects Company -> Company)
        kg.add_edge(Edge("geo:mountain_view", "subsidiary_of", "co:google"))
    except TypeError as e:
        print(f"\n❌ Successfully blocked bad data: {e}")

    # 6. Execute Logical Reasoning
    kg.run_reasoner()

    # 7. Query the fully fleshed-out knowledge base
    print("\n--- Querying Final Knowledge Base ---")
    all_relations = kg.query_triples(s="co:youtube")
    for relation in all_relations:
        print(f"Fact verified: YouTube -> {relation.relation} -> {relation.target}")

    all_relations = kg.query_triples(s="co:google")
    for relation in all_relations:
        print(f"Fact verified: co:google -> {relation.relation} -> {relation.target}")

    
    all_relations = kg.query_triples(s="geo:mountain_view")
    for relation in all_relations:
        print(f"Fact verified: geo:mountain_view -> {relation.relation} -> {relation.target}")
