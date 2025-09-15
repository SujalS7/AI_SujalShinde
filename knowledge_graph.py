import json


#  Define a Knowledge Graph
# Here, we represent our graph as a dictionary.
# Each concept (like "Data Structures") is a KEY.
# The VALUE is another dictionary containing:
#   - A "definition" (short explanation of the concept)
#   - A "related" list (links to other connected concepts)

knowledge_graph = {
    "Data Structures": {
        "definition": "Ways to store and organize data efficiently.",
        "related": ["Arrays", "Linked List", "Trees"]
    },
    "Algorithms": {
        "definition": "Step-by-step procedures to solve problems.",
        "related": ["Sorting", "Searching"]
    },
    "Trees": {
        "definition": "A hierarchical data structure with nodes.",
        "related": ["Binary Tree", "Graphs"]
    },
    "Graphs": {
        "definition": "A collection of nodes connected by edges.",
        "related": ["Trees", "Graph Traversal"]
    }
}

# We can save this dictionary into a JSON file. Because JSON is a portable format

with open("knowledge_graph.json", "w") as f:
    json.dump(knowledge_graph, f, indent=4)


# We read the JSON file back into Python.
with open("knowledge_graph.json", "r") as f:
    kg = json.load(f)


# This function takes a concept (like "Trees"),
# looks it up in the graph, and returns:
#   - The definition
#   - Related concepts
# If the concept does not exist, it gives a friendly error.
def get_concept_info(concept):
    if concept in kg:
        definition = kg[concept]["definition"]
        related = kg[concept]["related"]
        return definition, related
    else:
        return None, []



#  Test with a student query
query = "Trees"

definition, related = get_concept_info(query)

if definition:
    print(f"📘 Concept: {query}")
    print(f"📖 Definition: {definition}")
    print(f"🔗 Related Topics: {', '.join(related)}")
else:
    print(f"❌ Sorry, the concept '{query}' was not found in the knowledge graph.")
