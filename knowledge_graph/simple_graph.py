import networkx as nx
import matplotlib.pyplot as plt
print ("start to build")

# 1. Initialize a directed graph
kg = nx.DiGraph()

# 2. Add entities (Nodes) with optional attributes
kg.add_node("Python", type="Programming Language", difficulty="Medium")
kg.add_node("Knowledge Graph", type="Data Structure")
kg.add_node("NetworkX", type="Python Library")

# 3. Add relationships (Edges) with attributes
kg.add_edge("NetworkX", "Python", relation="written_in")
kg.add_edge("NetworkX", "Knowledge Graph", relation="used_to_build")

# 4. Inspect the graph
print(f"Nodes: {kg.nodes(data=True)}")
print(f"Edges: {kg.edges(data=True)}")
print ("End build")

# 5. Visualize the graph
pos = nx.spring_layout(kg)
plt.figure(figsize=(8, 6))

# Draw nodes and edges
nx.draw(kg, pos, with_labels=True, node_color='skyblue', node_size=2000, font_size=10, font_weight='bold')

# Draw edge labels
edge_labels = nx.get_edge_attributes(kg, 'relation')
nx.draw_networkx_edge_labels(kg, pos, edge_labels=edge_labels, font_color='red')

plt.show()