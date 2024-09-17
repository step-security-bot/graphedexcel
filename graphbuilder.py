from collections import Counter
import re
from openpyxl import load_workbook
import networkx as nx
import matplotlib.pyplot as plt

# Regular expression to detect cell references like A1, B2, or ranges like A1:B2
# CELL_REF_REGEX = r"[A-Z]{1,3}[0-9]+"
CELL_REF_REGEX = r"(('?[A-Za-z0-9\s_\-\[\]]+'?![A-Z]{1,3}[0-9]+)|([A-Z]{1,3}[0-9]+))"


def extract_formulas_and_build_dependencies(file_path):
    # Load the workbook
    wb = load_workbook(file_path, data_only=False)

    # Create a directed graph for dependencies
    G = nx.DiGraph()

    # Iterate over all sheets
    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        print(f"\n-- Analyzing sheet: {sheet_name} --\n")

        # Iterate over all cells
        for row in ws.iter_rows():
            for cell in row:
                if isinstance(cell.value, str) and cell.value.startswith("="):
                    # The formula is found in this cell
                    cell_name = f"{sheet_name}!{cell.coordinate}"
                    print(f"Formula in {cell_name}: {cell.value}")

                    # Extract all referenced cells from the formula
                    referenced_cells = extract_references(cell.value)
                    refs = []
                    # Add the cell and its dependencies to the graph
                    for ref_cell in referenced_cells:
                        # if ref_cell is without sheet name, add sheet name
                        if "!" not in ref_cell:
                            refc = f"{sheet_name}!{ref_cell}"
                        else:
                            refc = ref_cell

                        # add node to refs if not already in refs
                        if refc not in refs:
                            print(f"  Depends on: {refc}")
                            refs.append(refc)
                            G.add_edge(cell_name, refc)

                    # Cell "cell_name" depends on "ref_cell"

    return G


def summarize_graph(G):
    """
    Summarize a networkx DiGraph representing a dependency graph.
    """
    # 1. Print basic information about the graph
    print("=== Dependency Graph Summary ===")
    print(f"Number of nodes (cells): {G.number_of_nodes()}")
    print(f"Number of edges (dependencies): {G.number_of_edges()}\n")

    degreeView = G.degree()

    degree_counts = Counter(dict(degreeView))
    max_degree_node = degree_counts.most_common(10)
    print(f"Nodes with the highest degree:")
    for node, degree in max_degree_node:
        print(f"  {node}: {degree} dependencies")


def extract_references(formula):
    """
    Extract all referenced cells from a formula using regular expressions.
    This returns a list of cells that are mentioned directly (e.g., A1, B2),
    but doesn't handle ranges or external sheets' references.
    """
    formula = formula.replace("$", "")
    matches = re.findall(CELL_REF_REGEX, formula)
    extracted_references = [match[0].replace("$", "") for match in matches if match[0]]

    return extracted_references


def visualize_dependency_graph(G, file_path):
    """
    Render the dependency graph using matplotlib and networkx.
    """

    G = G.to_undirected()

    pos = nx.spiral_layout(G)  # layout for nodes
    plt.figure(figsize=(30, 30))
    nx.draw(
        G,
        pos,
        # with_labels=True,
        node_color="black",
        edge_color="gray",
        linewidths=0.5,
        alpha=0.8,
        width=0.1,
        # font_weight="bold",
        node_size=2,
    )
    plt.title("Excel Cell Dependency Graph")
    # Save the plot as an image file
    plt.savefig(f"{file_path}.png")


if __name__ == "__main__":
    # Replace 'your_spreadsheet.xlsx' with the path to your Excel file
    #    path_to_excel = "Book1.xlsx"
    path_to_excel = "simplified_1.xlsx"

    # Extract formulas and build the dependency graph
    dependency_graph = extract_formulas_and_build_dependencies(path_to_excel)

    summarize_graph(dependency_graph)

    # print("\n-- Generate visualization --")
    # Visualize the graph of dependencies
    visualize_dependency_graph(dependency_graph, path_to_excel)
