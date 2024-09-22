"""
This script extracts formulas from an Excel file and builds a dependency graph.
"""

from collections import Counter
import re
from openpyxl import load_workbook
import networkx as nx
import matplotlib.pyplot as plt
import sys

# Regex to detect cell references like A1, B2, or ranges like A1:B2
CELL_REF_REGEX = r"('?[A-Za-z0-9_\-\[\] ]+'?![A-Z]{1,3}[0-9]+(:[A-Z]{1,3}[0-9]+)?)|([A-Z]{1,3}[0-9]+(:[A-Z]{1,3}[0-9]+)?)"  # noqa

# dictionary that stores the uniqe functions used in the formulas
# the key will be the funciton name and the value will be the number of times it was used
functions_dict = {}


def log(msg):
    """
    Log a message to the console if verbosity is enabled using the --verbose flag.
    """
    # if verbosity is enabled

    if "--verbose" in sys.argv:
        print(msg)


def stat_functions(cellvalue):
    # functions used in the formula
    cellfuncs = re.findall(r"[A-Z]+\(", cellvalue)
    log(f"  Functions used: {functions_dict}")
    # add the functions to the dictionary
    for function in cellfuncs:
        # remove the "(" from the function name
        function = function[:-1]
        if function in functions_dict:
            functions_dict[function] += 1
        else:
            functions_dict[function] = 1


def extract_formulas_and_build_dependencies(file_path):
    """
    Extract formulas from an Excel file and build a dependency graph.
    """

    # Load the workbook
    wb = load_workbook(file_path, data_only=False)

    # Create a directed graph for dependencies
    graph = nx.DiGraph()

    # Iterate over all sheets
    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        log(f"-- Analyzing sheet: {sheet_name} --")

        # Iterate over all cells
        for row in ws.iter_rows():
            for cell in row:
                if isinstance(cell.value, str) and cell.value.startswith("="):
                    stat_functions(cell.value)

                    # The formula is found in this cell
                    cell_name = f"{sheet_name}!{cell.coordinate}"
                    log(f"Formula in {cell_name}: {cell.value}")

                    # Extract all referenced cells from the formula
                    referenced_cells = extract_references(cell.value)
                    refs = []

                    # Add the cell and its dependencies to the graph
                    for ref_cell in referenced_cells:
                        if "!" not in ref_cell:
                            # No sheet specified in the assume current sheet
                            refc = f"{sheet_name}!{ref_cell}"
                        else:
                            refc = ref_cell

                        # Add node to refs if not already in refs
                        if refc not in refs:
                            log(f"  Depends on: {refc}")
                            refs.append(refc)
                            graph.add_edge(cell_name, refc)

    return graph


def print_summary(graph, functionsdict):
    """
    Summarize a networkx DiGraph representing a dependency graph. And print the most used functions in the formulas
    """

    strpadsize = 28
    numpadsize = 5
    # 1. Print basic information about the graph

    print("=== Dependency Graph Summary ===")
    print(
        "Cell/Node count".ljust(strpadsize, " ")
        + str(graph.number_of_nodes()).rjust(numpadsize, " ")
    )
    print(
        "Dependency count".ljust(strpadsize, " ")
        + str(graph.number_of_edges()).rjust(numpadsize, " ")
    )
    print()

    # 2. Print the nodes with the highest degree
    degree_view = graph.degree()

    degree_counts = Counter(dict(degree_view))
    max_degree_node = degree_counts.most_common(10)
    print("=== Nodes with the highest degree ===")
    for node, degree in max_degree_node:
        print(f"{node.ljust(strpadsize)}{str(degree).rjust(numpadsize, ' ')} ")

    # 3. Print the most used functions
    print("\n=== Formula functions by count ===")
    sorted_functions = dict(
        sorted(functionsdict.items(), key=lambda item: item[1], reverse=True)
    )

    for function, count in sorted_functions.items():
        print(f"{function.ljust(strpadsize, ' ')}{str(count).rjust(numpadsize, ' ')}")


def extract_references(formula):
    """
    Extract all referenced cells from a formula using regular expressions.
    This returns a list of cells that are mentioned directly (e.g., A1, B2),
    but doesn't handle ranges or external sheets' references.
    """
    formula = formula.replace("$", "")
    matches = re.findall(CELL_REF_REGEX, formula)
    references = [match[0] if match[0] else match[2] for match in matches]

    # trim the extracted references
    references = [ref.strip() for ref in references]

    return references


def visualize_dependency_graph(graph, file_path):
    """
    Render the dependency graph using matplotlib and networkx.
    """

    # if --keep-direction is not passed as argument
    if "--keep-direction" not in sys.argv:
        # Convert the graph to an undirected graph
        graph = graph.to_undirected()

    pos = nx.spring_layout(graph)  # layout for nodes
    plt.figure(figsize=(10, 10))
    nx.draw(
        graph,
        pos,
        with_labels=True,
        node_color="black",
        edge_color="gray",
        linewidths=3.5,
        alpha=0.8,
        width=1,
        # font_weight="bold",
        node_size=20,
    )
    plt.title("Excel Cell Dependency Graph")
    # Save the plot as an image file
    plt.savefig(f"images/{file_path}.png")


if __name__ == "__main__":
    path_to_excel = "Book1.xlsx"

    if len(sys.argv) > 1:
        path_to_excel = sys.argv[1]

    # Extract formulas and build the dependency graph
    dependency_graph = extract_formulas_and_build_dependencies(path_to_excel)

    print_summary(dependency_graph, functions_dict)

    # if --no-visualize is not passed as argument
    if "--no-visualize" not in sys.argv:
        print(
            "\033[1;30;40m\nVisualizing the graph of dependencies.\nThis might take a while...\033[0;37;40m\n"  # noqa
        )

        visualize_dependency_graph(dependency_graph, path_to_excel)
