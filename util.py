
# interval that defines the update frequency of the visual simulation, and the update of the positions of the trucks
# the smaller the interval, the faster the trucks move
update_interval = 0.02

# value that defines how fine grain the position updates are
# the smaller the value, the higher amount of position updates the trash collectors go through
jump_size = 0.0001

import osmnx as ox
import networkx as nx
import heapq

def jid_to_name(jid):
    name = jid.split('@')[0]
    return name

""" SEARCH ALGORITHMS """

def _find_next_location(current_location, visited, distance_matrix):
    best_next_location = None
    min_distance = float('inf')
    for i in range(len(distance_matrix)):
        if i not in visited and distance_matrix[current_location][i] < min_distance:
            min_distance = distance_matrix[current_location][i]
            best_next_location = i
    return best_next_location

def greedy_path(start_location, distance_matrix):
    path = [start_location]
    visited = set(path)
    while len(visited) < len(distance_matrix):
        next_location = _find_next_location(path[-1], visited, distance_matrix)
        if next_location is None:
            break
        path.append(next_location)
        visited.add(next_location)
    return path + [start_location]

# finds route between two tuples (latitude, longitude)
def find_route(G, orig_point, dest_point):
    # Use the new method to find the nearest nodes
    orig_node = ox.distance.nearest_nodes(G, orig_point[1], orig_point[0])
    dest_node = ox.distance.nearest_nodes(G, dest_point[1], dest_point[0])
    route_nodes = nx.shortest_path(G, orig_node, dest_node, weight='length')
    
    # Convert node IDs to (latitude, longitude) pairs
    route_latlon = [(G.nodes[node]['y'], G.nodes[node]['x']) for node in route_nodes]
    return route_latlon


def _calculate_priority_2(distance, occupancy, remaining_capacity):
    if occupancy > remaining_capacity:
        # Discourage picking up from this location if it exceeds remaining capacity
        return -float('inf')
    else:
        # Prioritize by occupancy, discourage by distance
        return occupancy - distance * 100  # The 100 factor is arbitrary and may need adjustment

def greedy_path_with_capacity(start_location, distance_matrix, trash_occupancy_dict, max_capacity, excluded_indexes=[]):
    n_locations = len(distance_matrix)
    path = [start_location]
    visited = {start_location}.union(set(excluded_indexes))
    current_capacity = 0
    priority_queue = []

    # Fill the priority queue based on initial distances and occupancies
    for i in range(n_locations):
        if i != start_location:
            priority = _calculate_priority_2(distance_matrix[start_location][i], trash_occupancy_dict[i], max_capacity)
            heapq.heappush(priority_queue, (-priority, i))  # Max-heap using negative priority

    # Continue until the priority queue is empty or all locations are visited
    while priority_queue and len(visited) < n_locations:
        _, next_location = heapq.heappop(priority_queue)
        if next_location in visited:
            continue  # Skip already visited locations
        
        additional_trash = min(trash_occupancy_dict[next_location], max_capacity - current_capacity)
        if additional_trash > 0:
            path.append(next_location)
            visited.add(next_location)
            current_capacity += additional_trash
            
            # If capacity reached, return to start to offload and continue
            if current_capacity >= max_capacity:
                break
                # path.append(start_location)
                # current_capacity = 0  # Reset capacity after offloading
                # visited = {start_location}  # Reset visited after offloading

            # Update the queue with the remaining locations
            for i in range(n_locations):
                if i not in visited:
                    priority = _calculate_priority_2(distance_matrix[next_location][i], trash_occupancy_dict[i], max_capacity - current_capacity)
                    heapq.heappush(priority_queue, (-priority, i))

    if path[-1] != start_location:
        path.append(start_location)  # Ensure the path ends at the start location

    return path

# solve using a TSP solver (Travelling Salesman Problem)
def find_optimal_path_tsp(distance_matrix, trash_occupancies, max_capacity, excluded_nodes=[]):
    # Create a complete graph from the distance matrix
    G = nx.Graph()  # Changed to a simple Graph instead of complete graph initialization
    num_nodes = len(distance_matrix)
    start_node = num_nodes-1

    excluded_nodes = set(excluded_nodes)
    excluded_nodes.discard(start_node) # we remove the start node from excluded nodes, because the path has to go through this node

    # Add nodes and edges with appropriate weights, excluding specified nodes
    for i in range(num_nodes):
        if i in excluded_nodes:
            continue
        for j in range(i + 1, num_nodes):
            if j in excluded_nodes:
                continue
            G.add_edge(i, j, weight=distance_matrix[i][j])

    # Solve TSP using an approximation method, considering only included nodes
    if len(G.nodes) > 0:
        cycle = nx.approximation.traveling_salesman_problem(
            G, cycle=True, weight='weight')
        # Reorder the cycle to start and end at the start_location
        start_index = cycle.index(start_node)
        ordered_cycle =  cycle[start_index:] + cycle[:start_index] + [start_node]
    else:
        ordered_cycle = []

    # Refine the cycle to respect capacity constraints
    path, current_load = [], 0
    start_location = ordered_cycle[0]
    path.append(start_location)

    for node in ordered_cycle[1:]:
        if node == start_node: # if node is the start location, we set the cost to 0
            occupancy = 0
        else:
            occupancy = trash_occupancies[node]
        if current_load + occupancy <= max_capacity:
            path.append(node)
            current_load += occupancy
        else:
            # Go to node and then go to start location
            path.append(node)
            path.append(start_location)
            current_load = occupancy
            break

    # Ensure returning to the start location if not already there
    if path[-1] != start_location:
        path.append(start_location)

    return path