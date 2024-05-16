
import numpy as np
import random
import osmnx as ox
import networkx as nx
import math
from Classes.Position import euclidean_dist_vec

class GraphMap:
    def __init__(self, trash_jids, trash_positions, center_jid, center_position, G):
        np.random.seed(0) # set the seed to 0 for uniform results
        self.n_locations = len(trash_jids) + 1 # +1 because the central is also a location
        self.G = G  # Graph from osmnx

        # Initialize the distance matrix with zeros
        self.distance_matrix = np.zeros((self.n_locations, self.n_locations))
        self.routes_matrix = [[None] * self.n_locations for _ in range(self.n_locations)]

        # set up a dictionary that maps agent index to their respective jid (string)
        self.index_to_agent = {}
        self.index_to_position = {}
        self.jid_to_index = {}
        
        for i, (jid, position) in enumerate(zip(trash_jids, trash_positions)):
            self.index_to_agent[i] = jid
            self.jid_to_index[jid] = i
            self.index_to_position[i] = position

        # the central agent is the last index
        self.index_to_agent[self.n_locations-1] = center_jid
        self.jid_to_index[center_jid] = self.n_locations-1
        self.index_to_position[self.n_locations-1] = center_position

        self.fill_matrices()

    def fill_matrices(self):
        for i in range(self.n_locations):
            for j in range(i + 1, self.n_locations):
                if i != j:
                    # Find route between positions i and j
                    route_latlon = self.find_route(i, j)
                    self.routes_matrix[i][j] = route_latlon
                    self.routes_matrix[j][i] = list(reversed(route_latlon))
                    
                    # Calculate the length of the route for the distance matrix
                    route_length = sum(
                        euclidean_dist_vec(route_latlon[k][0], route_latlon[k][1], route_latlon[k+1][0], route_latlon[k+1][1]) for k in range(len(route_latlon) - 1)
                    )
                    self.distance_matrix[i][j] = self.distance_matrix[j][i] = route_length


    def find_best_path(self, trash_occupancies_dict, elapsed_time_collection, excluded_locations_jids, collector_capacity=None):
        # convert excluded_locations in jids to indexes
        excluded_locations = [self.jid_to_index[jid] for jid in excluded_locations_jids]
        best_path = self.find_optimal_path_tsp(trash_occupancies_dict, elapsed_time_collection, max_capacity=collector_capacity, excluded_nodes=excluded_locations)
        print(best_path)
        if len(best_path) > 2:
            assert best_path[0] == best_path[-1] # the start and end location is the same (trash center)

        # now we need to change best_path, because it contains the indexes of the agents in the path, instead of their jid's
        jids_path = [self.index_to_agent[i] for i in best_path]

        # Get cost and route arrays based on best path
        cost_array = []
        route_array = []
        for i in range(len(best_path)-1):
            start = best_path[i]
            end = best_path[i+1]
            cost = self.distance_matrix[start][end]
            route = self.routes_matrix[start][end]
            cost_array.append(cost)
            route_array.append(route)
        return jids_path, cost_array, route_array

    def get_route(self, start_jid, end_jid=None):
        start_index = self.jid_to_index[start_jid]
        if not end_jid:
            end_index = self.n_locations-1 # set end index to the collection center
        else:
            end_index = self.jid_to_index[end_jid]
        return self.routes_matrix[start_index][end_index]

    def find_route(self, i, j):
        orig_point = self.index_to_position[i]
        dest_point = self.index_to_position[j]
        # Use the new method to find the nearest nodes
        orig_node = ox.distance.nearest_nodes(self.G, orig_point[1], orig_point[0])
        dest_node = ox.distance.nearest_nodes(self.G, dest_point[1], dest_point[0])
        route_nodes = nx.shortest_path(self.G, orig_node, dest_node, weight='length')

        # Convert node IDs to (latitude, longitude) pairs
        route_latlon = [(self.G.nodes[node]['y'], self.G.nodes[node]['x']) for node in route_nodes]
        return route_latlon

    """
    finds the optimal path using a TSP (Travelling Salesman Problem) solver
    trash_occupancies maps trash jids to their occupancies
    """
    def find_optimal_path_tsp(self, trash_occupancies, elapsed_time_collection, max_capacity=None, excluded_nodes=[]):
        distance_matrix = self.distance_matrix
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
                i_jid = self.index_to_agent[i]
                j_jid = self.index_to_agent[j]
                edge_weight = distance_matrix[i][j]

                # the start node doesnt have an elapsed time since the last trash collection, because the start node is the CollectionCenter
                # so we only change the edge_weight if the nodes aren't the start node
                if i != start_node:
                    edge_weight += elapsed_time_collection[i_jid]
                if j != start_node:
                    edge_weight += elapsed_time_collection[j_jid]

                G.add_edge(i, j, weight=edge_weight)

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
        if len(ordered_cycle) > 0:
            start_location = ordered_cycle[0]
            path.append(start_location)

            for node in ordered_cycle[1:]:
                if node == start_node: # if node is the start location, we set the cost to 0
                    continue
                elif path[-1] != node:
                    # only run if the current node is different from the last. Because we can't have the same node twice in a row
                    trash_jid = self.index_to_agent[node]
                    occupancy = trash_occupancies[trash_jid]
                    if not max_capacity or (current_load + occupancy <= max_capacity):
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