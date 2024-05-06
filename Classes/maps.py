
import numpy as np
import random
from util import greedy_path, find_route, greedy_path_with_capacity
import osmnx as ox
import math
from Classes.Position import euclidean_dist_vec

class GraphMap:
    def __init__(self, trash_agents, central_agent, G):
        np.random.seed(0) # set the seed to 0 for uniform results
        self.n_locations = len(trash_agents) + 1 # +1 because the central is also a location
        self.G = G  # Graph from osmnx

        # Initialize the distance matrix with zeros
        self.distance_matrix = np.zeros((self.n_locations, self.n_locations))
        self.routes_matrix = [[None] * self.n_locations for _ in range(self.n_locations)]

        # set up a dictionary that maps agent index to their respective jid (string)
        self.index_to_agent = {}
        self.index_to_position = {}
        self.jid_to_index = {}
        
        for i, agent in enumerate(trash_agents):
            self.index_to_agent[i] = str(agent.jid)
            self.jid_to_index[str(agent.jid)] = i
            self.index_to_position[i] = agent.get('position')

        # the central agent is the last index
        self.index_to_agent[self.n_locations-1] = str(central_agent.jid)
        self.jid_to_index[str(central_agent.jid)] = self.n_locations-1
        self.index_to_position[self.n_locations-1] = central_agent.get('position')

        self.fill_matrices()

    def fill_matrices(self):
        for i in range(self.n_locations):
            for j in range(i + 1, self.n_locations):
                if i != j:
                    # Find route between positions i and j
                    route_latlon = find_route(self.G, self.index_to_position[i], self.index_to_position[j])
                    self.routes_matrix[i][j] = route_latlon
                    self.routes_matrix[j][i] = list(reversed(route_latlon))
                    
                    # Calculate the length of the route for the distance matrix
                    route_length = sum(
                        euclidean_dist_vec(route_latlon[k][0], route_latlon[k][1], route_latlon[k+1][0], route_latlon[k+1][1]) for k in range(len(route_latlon) - 1)
                    )
                    self.distance_matrix[i][j] = self.distance_matrix[j][i] = route_length


    def find_best_path(self, trash_occupancies_dict, collector_capacity):
        #best_path = greedy_path(self.n_locations-1, self.distance_matrix)
        best_path = greedy_path_with_capacity(self.n_locations-1, self.distance_matrix, trash_occupancies_dict, collector_capacity)
        # best_path[0] == best_path[-1] -> the start and end location is the same (trash center)

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